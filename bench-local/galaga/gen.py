#!/usr/bin/env python3
"""Galaga coding test: ask each installed Strata quant to write prompt.md's game, one server start per quant.

usage: gen.py [--quants IQ3_XXS,IQ3_S,unsloth-ud-q4_k_xl] [--arms off,medium] [--seeds 1,2]

Writes out/<quant>-<arm>-s<seed>.json (the request, the full response, timings from /metrics) and
out/<quant>-<arm>-s<seed>.html (the first ```html block of the answer, or the whole answer if it has none).
A run whose .json already exists is skipped, so an interrupted sweep resumes.
"""

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "qwfn-suite"))
import serve_strata  # noqa: E402

PORT = 8080
OUT = HERE / "out"
PROMPT = (HERE / "prompt.md").read_text(encoding="utf-8")

# Qwen's recommended sampling for each mode; a fixed seed per run so a run can be repeated.
ARMS = {
    "off": {"reasoning_effort": "none", "temperature": 0.7, "top_p": 0.8, "top_k": 20},
    # medium, the level the 2026-09-28 notes found safe; the budget only guards against runaway thinking
    "medium": {"reasoning_effort": "medium", "reasoning_budget_tokens": 16384,
               "temperature": 0.6, "top_p": 0.95, "top_k": 20},
    # 2026-10-03: a doubled thinking budget, at xhigh (which Strata runs as high) and at medium as the control;
    # a larger output cap so the longer thinking cannot crowd out the code
    "xhigh32k": {"reasoning_effort": "xhigh", "reasoning_budget_tokens": 32768, "max_tokens": 81920,
                 "temperature": 0.6, "top_p": 0.95, "top_k": 20},
    "medium32k": {"reasoning_effort": "medium", "reasoning_budget_tokens": 32768, "max_tokens": 81920,
                  "temperature": 0.6, "top_p": 0.95, "top_k": 20},
}
MAX_TOKENS = 49152


def post(body, timeout=7200):
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def metrics_row():
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/metrics", timeout=30) as r:
        m = json.load(r)
    return (m.get("requests") or [{}])[0], m.get("engine", {})


def extract_html(text):
    blocks = re.findall(r"```(?:html|HTML)?[ \t]*\n(.*?)```", text, re.S)
    blocks = [b for b in blocks if "<" in b]
    if blocks:
        return max(blocks, key=len), "fenced"
    # an unterminated block (the answer was cut off): everything after the opening fence
    m = re.search(r"```(?:html|HTML)?[ \t]*\n(.*)$", text, re.S)
    if m:
        return m.group(1), "unterminated"
    return text, "raw"


def run_one(quant, arm, seed):
    tag = f"{quant.lower()}-{arm}-s{seed}"
    jpath = OUT / f"{tag}.json"
    if jpath.exists():
        print(f"  {tag}: done already, skipped", flush=True)
        return
    body = {"model": "strata", "messages": [{"role": "user", "content": PROMPT}],
            "max_tokens": MAX_TOKENS, "seed": seed, **ARMS[arm]}
    t0 = time.time()
    resp = post(body)
    wall = time.time() - t0
    row, engine = metrics_row()
    msg = resp["choices"][0]["message"]
    content = msg.get("content") or ""
    thinking = msg.get("reasoning_content") or msg.get("reasoning") or ""
    html, how = extract_html(content)
    (OUT / f"{tag}.html").write_text(html, encoding="utf-8")
    rec = {"quant": quant, "arm": arm, "seed": seed, "request": body, "wall_s": round(wall, 1),
           "finish_reason": resp["choices"][0].get("finish_reason"), "usage": resp.get("usage"),
           "metrics": row, "engine": engine, "html_extract": how, "html_chars": len(html),
           "html_lines": html.count("\n") + 1, "thinking_chars": len(thinking), "content": content,
           "thinking": thinking}
    jpath.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    dm, otok = row.get("decode_ms") or 0, row.get("output_tokens") or 0
    rate = otok / (dm / 1000) if dm else 0
    print(f"  {tag}: {resp['choices'][0].get('finish_reason')}, {otok} tokens "
          f"(thinking {len(thinking)} chars), {rate:.1f} tok/s, {wall / 60:.1f} min, "
          f"html {rec['html_lines']} lines ({how})", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quants", default="IQ3_XXS,IQ3_S,unsloth-ud-q4_k_xl")
    ap.add_argument("--arms", default="off,medium")
    ap.add_argument("--seeds", default="1,2")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    if serve_strata.healthy(PORT):
        raise SystemExit(f"something already answers on {PORT}; stop it first")
    for quant in a.quants.split(","):
        todo = [(arm, int(s)) for arm in a.arms.split(",") for s in a.seeds.split(",")
                if not (OUT / f"{quant.lower()}-{arm}-s{s}.json").exists()]
        if not todo:
            print(f"{quant}: all runs done", flush=True)
            continue
        print(f"{quant}: starting server", flush=True)
        proc = serve_strata.start(quant, PORT)
        try:
            for arm, seed in todo:
                run_one(quant, arm, seed)
        finally:
            serve_strata.stop(proc, PORT)


if __name__ == "__main__":
    main()
