#!/usr/bin/env python3
"""Galaga coding test, Claude baseline: the same prompt.md, sent to a Claude model through the Anthropic API.

usage: gen_claude.py [--model claude-sonnet-5-5] [--arms off,medium] [--runs 1,2]
       (reads ANTHROPIC_API_KEY from the environment)

Writes out/<tag>-<arm>-r<run>.json and .html in the same shape gen.py does, so playtest.py, stats.py, blind.py and
results.py treat them like the Strata runs. The runs go in parallel. A run whose .json exists is skipped.

The arms match the Strata ones as closely as the API allows. Claude Sonnet 5.5 cannot turn thinking fully off and
takes no sampling parameters or seed, so the two runs per arm are plain repeats:
  off     thinking {type: "between_tools"} (no thinking before the answer), effort high (the model's default)
  medium  thinking {type: "adaptive"}, effort medium
No refusal fallback is configured, so a refusal is recorded as one instead of being answered by a different model.
"""

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import anthropic

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from gen import MAX_TOKENS, OUT, PROMPT, extract_html  # noqa: E402  (same prompt, cap and extraction as Strata)

ARMS = {
    "off": {"thinking": {"type": "between_tools"}, "output_config": {"effort": "high"}},
    "medium": {"thinking": {"type": "adaptive"}, "output_config": {"effort": "medium"}},
}


def run_one(client, model, arm, run):
    tag = f"{model.replace('claude-', '')}-{arm}-r{run}"
    jpath = OUT / f"{tag}.json"
    if jpath.exists():
        return f"  {tag}: done already, skipped"
    t0 = time.time()
    try:
        with client.messages.stream(model=model, max_tokens=MAX_TOKENS,
                                    messages=[{"role": "user", "content": PROMPT}], **ARMS[arm]) as stream:
            msg = stream.get_final_message()
            response = getattr(stream, "response", None)
            request_id = response.headers.get("request-id") if response is not None else None
    except anthropic.APIError as e:
        return f"  {tag}: API error, not saved: {e}"
    wall = time.time() - t0
    (OUT / f"{tag}.raw.json").write_text(msg.to_json(), encoding="utf-8")
    content = "".join(b.text for b in msg.content if b.type == "text")
    html, how = extract_html(content)
    (OUT / f"{tag}.html").write_text(html, encoding="utf-8")
    finish = {"end_turn": "stop", "max_tokens": "length"}.get(msg.stop_reason, msg.stop_reason)
    rec = {"quant": model, "arm": arm, "seed": run, "request": {"model": model, "max_tokens": MAX_TOKENS, **ARMS[arm]},
           "wall_s": round(wall, 1), "finish_reason": finish,
           "usage": {"prompt_tokens": msg.usage.input_tokens, "completion_tokens": msg.usage.output_tokens},
           "metrics": {"duration_s": round(wall, 1)}, "request_id": request_id,
           "blocks": [{"type": b.type, "chars": len(getattr(b, "text", None) or getattr(b, "thinking", None) or "")}
                      for b in msg.content],
           "stop_reason": msg.stop_reason,
           "stop_details": msg.stop_details.to_dict() if getattr(msg, "stop_details", None) else None,
           "html_extract": how, "html_chars": len(html), "html_lines": html.count("\n") + 1,
           "thinking_chars": 0, "content": content}
    jpath.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return (f"  {tag}: {finish}, {msg.usage.output_tokens} tokens, {msg.usage.output_tokens / wall:.1f} tok/s, "
            f"{wall / 60:.1f} min, html {rec['html_lines']} lines ({how})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("--arms", default="off,medium")
    ap.add_argument("--runs", default="1,2")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    client = anthropic.Anthropic(timeout=1800.0)
    jobs = [(arm, int(r)) for arm in a.arms.split(",") for r in a.runs.split(",")]
    print(f"{a.model}: {len(jobs)} runs in parallel", flush=True)
    with ThreadPoolExecutor(len(jobs)) as ex:
        for line in ex.map(lambda j: run_one(client, a.model, *j), jobs):
            print(line, flush=True)


if __name__ == "__main__":
    main()
