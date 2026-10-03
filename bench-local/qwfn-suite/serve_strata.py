#!/usr/bin/env python3
"""Start/stop a Strata server for one quant - the Strata analogue of QwFNfer's serve.sh.

usage: serve_strata.py <IQ3_XXS|IQ3_S|...> [port]        (blocks until /health answers)
       serve_strata.py --stop [port]

Kept as a module too: `start(quant, port)` returns the Popen, `stop(proc, port)` tears it down
and waits for the port to go quiet, so a runner can swap quants between benchmark phases.
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / ".venv" / "Scripts" / "python.exe"


def config_for(quant, ctx=None, kv_stream=True):
    p = ROOT / f"strata-{quant.lower()}.json"
    if not p.exists():
        raise SystemExit(f"no config {p.name} - run setup.py for {quant} first")
    if not ctx and kv_stream:
        return p
    # A context override gets its own config next to setup's (strata-iq3_s-262k.json), so the
    # installed one is never touched. Everything but --max-context and the log path is kept.
    cfg = json.loads(p.read_text(encoding="utf-8"))
    args = cfg["args"]
    if ctx:
        args[args.index("--max-context") + 1] = str(ctx)
    tag = f"strata-{quant.lower()}-{round(int(args[args.index('--max-context') + 1]) / 1000)}k"
    if not kv_stream and "--kv-resident" in args:
        # the whole KV cache in VRAM instead of pinned RAM: fewer expert slots, but no pinned-RAM cost
        i = args.index("--kv-resident")
        del args[i:i + 2]
        tag += "-nostream"
    cfg["log"] = str(ROOT / f"{tag}.log")
    out = ROOT / f"{tag}.json"
    out.write_text(json.dumps(cfg, indent=1), encoding="utf-8")
    return out


def healthy(port, timeout=5):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=timeout):
            return True
    except Exception:
        return False


def wait_up(port, timeout=900):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if healthy(port):
            return round(time.time() - t0)
        time.sleep(3)
    return None


def wait_down(port, timeout=180):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if not healthy(port, timeout=3):
            return True
        time.sleep(2)
    return False


def start(quant, port=8080, ctx=None, kv_stream=True):
    cfg = config_for(quant, ctx, kv_stream)
    proc = subprocess.Popen(
        [str(PY), str(ROOT / "serve" / "server.py"), "--engine", "strata",
         "--config", str(cfg), "--port", str(port)],
        cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    load = wait_up(port)
    if load is None:
        proc.kill()
        raise SystemExit(f"{quant}: SERVER DID NOT COME UP")
    print(f"  {quant} up in {load}s", flush=True)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/metrics", timeout=30) as r:
            e = json.load(r).get("engine", {})
        print(f"  {quant}: context {e.get('context')}, {e.get('expert_slots')} expert slots, "
              f"{e.get('expert_cache_mib')} MiB cache, {e.get('vram_free_mib')} MiB VRAM free, "
              f"arena {e.get('arena_mib')} MiB", flush=True)
    except Exception:
        pass
    return proc


def stop(proc, port=8080):
    if proc is None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=90)
    except subprocess.TimeoutExpired:
        proc.kill()
    wait_down(port)


if __name__ == "__main__":
    if sys.argv[1] == "--stop":
        raise SystemExit(0)
    q = sys.argv[1]
    p = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
    proc = start(q, p)
    print("  (running; ctrl-c to stop)", flush=True)
    try:
        proc.wait()
    except KeyboardInterrupt:
        stop(proc, p)
