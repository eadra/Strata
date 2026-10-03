#!/usr/bin/env python3
"""Galaga coding test against an already-running NInfer server (Qwen3.8-27B on D:\\ninfer-4090), as a second local
reference next to the Strata quants. Same prompt.md, sampling, seeds and caps as gen.py's arms; this script does not
start or stop the server.

usage: gen_ninfer.py [--url http://localhost:8080] [--arms off,medium,medium32k,xhigh32k] [--seeds 1,2]

NInfer has no per-request thinking budget on Chat Completions, so the thinking arms go through its Anthropic-style
/v1/messages (thinking enabled + budget_tokens, output_config.effort, temperature/top_p/top_k, seed), and `off` goes
through /v1/chat/completions with reasoning_effort none, as gen.py sends it. Writes out/qwen3.8-27b-<arm>-s<seed>.json
and .html in gen.py's shape (the raw response first, as .raw.json), so playtest.py, stats.py, blind.py and results.py
treat them like the others. A run whose .json exists is skipped.
"""

import argparse
import json
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
PROMPT = (HERE / "prompt.md").read_text(encoding="utf-8")
MODEL = "qwen3.8-27b"

# mirrors gen.py's ARMS: the same effort, thinking budget, output cap and sampling
ARMS = {
    "off": {"api": "chat", "max_tokens": 49152, "reasoning_effort": "none", "temperature": 0.7, "top_p": 0.8,
            "top_k": 20},
    "medium": {"api": "messages", "max_tokens": 49152, "effort": "medium", "budget": 16384},
    "medium32k": {"api": "messages", "max_tokens": 81920, "effort": "medium", "budget": 32768},
    "xhigh32k": {"api": "messages", "max_tokens": 81920, "effort": "xhigh", "budget": 32768},
}
THINK_SAMPLING = {"temperature": 0.6, "top_p": 0.95, "top_k": 20}


def post(url, body, timeout=7200):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def extract_html(text):
    import re
    # anything may follow ```html on the fence line: Qwen3.8-27B once wrote "```html>"
    blocks = [b for b in re.findall(r"```(?:html|HTML)?[^\n]*\n(.*?)```", text, re.S) if "<" in b]
    if blocks:
        return max(blocks, key=len), "fenced"
    m = re.search(r"```(?:html|HTML)?[^\n]*\n(.*)$", text, re.S)
    return (m.group(1), "unterminated") if m else (text, "raw")


def run_one(base, arm, seed):
    tag = f"{MODEL}-{arm}-s{seed}"
    jpath = OUT / f"{tag}.json"
    if jpath.exists():
        return f"  {tag}: done already, skipped"
    a = ARMS[arm]
    if a["api"] == "chat":
        body = {"model": MODEL, "messages": [{"role": "user", "content": PROMPT}], "seed": seed,
                **{k: v for k, v in a.items() if k != "api"}}
        url = base + "/v1/chat/completions"
    else:
        body = {"model": MODEL, "max_tokens": a["max_tokens"], "seed": seed,
                "thinking": {"type": "enabled", "budget_tokens": a["budget"]},
                "output_config": {"effort": a["effort"]}, **THINK_SAMPLING,
                "messages": [{"role": "user", "content": PROMPT}]}
        url = base + "/v1/messages"
    t0 = time.time()
    resp = post(url, body)
    wall = time.time() - t0
    (OUT / f"{tag}.raw.json").write_text(json.dumps(resp, indent=1), encoding="utf-8")   # before any parsing
    if a["api"] == "chat":
        msg = resp["choices"][0]["message"]
        content, thinking = msg.get("content") or "", msg.get("reasoning_content") or ""
        finish = resp["choices"][0].get("finish_reason")
        out_tok = resp["usage"]["completion_tokens"]
    else:
        content = "".join(b.get("text", "") for b in resp["content"] if b["type"] == "text")
        thinking = "".join(b.get("thinking", "") for b in resp["content"] if b["type"] == "thinking")
        finish = {"end_turn": "stop", "max_tokens": "length"}.get(resp.get("stop_reason"), resp.get("stop_reason"))
        out_tok = resp["usage"]["output_tokens"]
    html, how = extract_html(content)
    (OUT / f"{tag}.html").write_text(html, encoding="utf-8")
    rec = {"quant": MODEL, "arm": arm, "seed": seed, "request": body, "wall_s": round(wall, 1),
           "finish_reason": finish, "usage": {"completion_tokens": out_tok, "raw": resp.get("usage")},
           "metrics": {"duration_s": round(wall, 1)}, "html_extract": how, "html_chars": len(html),
           "html_lines": html.count("\n") + 1, "thinking_chars": len(thinking), "content": content,
           "thinking": thinking}
    jpath.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return (f"  {tag}: {finish}, {out_tok} tokens (thinking {len(thinking)} chars), {out_tok / wall:.1f} tok/s, "
            f"{wall / 60:.1f} min, html {rec['html_lines']} lines ({how})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8080")
    ap.add_argument("--arms", default="off,medium,medium32k,xhigh32k")
    ap.add_argument("--seeds", default="1,2")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    for arm in a.arms.split(","):
        for s in a.seeds.split(","):
            try:
                print(run_one(a.url, arm, int(s)), flush=True)
            except Exception as e:   # one failed run must not stop the rest
                print(f"  {MODEL}-{arm}-s{s}: FAILED {type(e).__name__}: {str(e)[:300]}", flush=True)


if __name__ == "__main__":
    main()
