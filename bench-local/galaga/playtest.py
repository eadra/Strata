#!/usr/bin/env python3
"""Automated play-test of every out/*.html: load it in Chrome (headless, file://), record console errors, start a
game and run a simple bot for PLAY_S seconds, with screenshots. Writes play/<name>/*.png and play/<name>/result.json,
and play/summary.json.

Checks (each true/false):
  loads_clean      no uncaught exception or console error in the first 3 s
  canvas           a <canvas> of at least 200x200 is on the page
  title_drawn      the canvas is not blank before any key is pressed
  animates_idle    the canvas changes on its own before any key is pressed (starfield / attract)
  starts           the picture changes substantially within 5 s of pressing Enter
  moves            holding Left, then Right, changes the bottom fifth of the playfield
  survives_play    no uncaught exception during the PLAY_S-second bot run
  alive_at_end     the canvas is still changing at the end of the run (not frozen)

usage: playtest.py [glob]   (Python with playwright; uses the installed Chrome, no browser download)
"""

import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT, PLAY = HERE / "out", HERE / "play"
PLAY_S = int(__import__("os").environ.get("PLAY_S", 90))

# Grabs the largest canvas's pixels as a small grayscale grid so frames can be compared cheaply in the page.
SNAP_JS = """(region) => {
  const cs = [...document.querySelectorAll('canvas')];
  if (!cs.length) return null;
  const c = cs.reduce((a, b) => (a.width * a.height >= b.width * b.height ? a : b));
  let d;
  try {
    let g = c.getContext('2d');
    if (!g) {   // a WebGL canvas: copy it onto a 2D one first
      const t = document.createElement('canvas'); t.width = c.width; t.height = c.height;
      g = t.getContext('2d'); g.drawImage(c, 0, 0);
    }
    d = g.getImageData(0, 0, c.width, c.height).data;
  } catch (e) { return null; }
  const W = 48, H = 64, out = [];
  const y0 = region === 'bottom' ? Math.floor(H * 0.8) : 0;
  for (let gy = y0; gy < H; gy++) for (let gx = 0; gx < W; gx++) {
    // each cell's brightest pixel, so a 1-2 px star or bullet still registers
    let m = 0;
    const xa = Math.floor(gx * c.width / W), xb = Math.floor((gx + 1) * c.width / W);
    const ya = Math.floor(gy * c.height / H), yb = Math.floor((gy + 1) * c.height / H);
    for (let y = ya; y < yb; y++) for (let x = xa; x < xb; x++) {
      const i = (y * c.width + x) * 4, v = (d[i] + d[i + 1] + d[i + 2]) / 3;
      if (v > m) m = v;
    }
    out.push(m);
  }
  return out;
}"""


def diff(a, b):
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def changed(a, b):
    """The fraction of grid cells whose brightness moved by more than 6 (catches small sprites and stars)."""
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(1 for x, y in zip(a, b) if abs(x - y) > 6) / len(a)


def lit(a):
    return 0.0 if not a else sum(1 for v in a if v > 8) / len(a)


def test(page, html, shots):
    errors = []
    page.on("pageerror", lambda e: errors.append(("pageerror", time.time(), str(e)[:300])))
    page.on("console", lambda m: m.type == "error" and errors.append(("console", time.time(), m.text[:300])))
    r = {}
    t_load = time.time()
    page.goto(html.as_uri())
    page.wait_for_timeout(3000)
    r["loads_clean"] = not errors
    size = page.evaluate("""() => { const cs = [...document.querySelectorAll('canvas')];
        return cs.length ? Math.max(...cs.map(c => Math.min(c.width, c.height))) : 0 }""")
    r["canvas"] = size >= 200
    page.screenshot(path=str(shots / "1-title.png"))
    a = page.evaluate(SNAP_JS, "all")
    page.wait_for_timeout(1000)
    b = page.evaluate(SNAP_JS, "all")
    r["title_drawn"] = lit(a) > 0.005
    r["animates_idle"] = changed(a, b) > 0.003

    page.keyboard.press("Enter", delay=100)
    best = 0.0
    for i in range(10):
        page.wait_for_timeout(500)
        best = max(best, diff(b, page.evaluate(SNAP_JS, "all")))
    r["starts"] = best > 2.0
    page.screenshot(path=str(shots / "2-after-enter-5s.png"))
    page.wait_for_timeout(3000)
    page.screenshot(path=str(shots / "3-after-enter-8s.png"))

    # movement: hold Left 1.2 s, then Right 2.4 s; compare the bottom strip where the fighter lives
    s0 = page.evaluate(SNAP_JS, "bottom")
    page.keyboard.down("ArrowLeft"); page.wait_for_timeout(1200); page.keyboard.up("ArrowLeft")
    s1 = page.evaluate(SNAP_JS, "bottom")
    page.keyboard.down("ArrowRight"); page.wait_for_timeout(2400); page.keyboard.up("ArrowRight")
    s2 = page.evaluate(SNAP_JS, "bottom")
    r["moves"] = max(changed(s0, s1), changed(s1, s2)) > 0.01

    # the bot: sweep left and right, tapping fire every 120 ms; screenshots every 15 s
    t_play, n_err_before = time.time(), len(errors)
    direction, last_turn, last_shot, k = "ArrowLeft", 0.0, 0.0, 0
    page.keyboard.down(direction)
    while time.time() - t_play < PLAY_S:
        now = time.time() - t_play
        if now - last_turn > 0.9:
            page.keyboard.up(direction)
            direction = "ArrowRight" if direction == "ArrowLeft" else "ArrowLeft"
            page.keyboard.down(direction)
            last_turn = now
        if now - last_shot > 0.16:
            page.keyboard.press("Space", delay=80)
            last_shot = now
        if now > 15 * (k + 1):
            k += 1
            page.screenshot(path=str(shots / f"4-play-{15 * k:03d}s.png"))
            if k % 2 == 0:
                page.keyboard.press("Enter", delay=100)   # restart if the bot lost and the game returned to the title
        page.wait_for_timeout(40)
    page.keyboard.up(direction)
    r["survives_play"] = len(errors) == n_err_before
    c0 = page.evaluate(SNAP_JS, "all"); page.wait_for_timeout(700); c1 = page.evaluate(SNAP_JS, "all")
    r["alive_at_end"] = changed(c0, c1) > 0.003
    page.screenshot(path=str(shots / "5-end.png"))
    r["passed"] = sum(1 for v in r.values() if v is True)
    r["errors"] = [{"kind": k_, "t": round(t - t_load, 1), "text": s} for k_, t, s in errors[:20]]
    r["n_errors"] = len(errors)
    return r


def main():
    pat = sys.argv[1] if len(sys.argv) > 1 else "*.html"
    PLAY.mkdir(exist_ok=True)
    summary = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True, args=["--autoplay-policy=no-user-gesture-required"])
        for html in sorted(OUT.glob(pat)):
            shots = PLAY / html.stem
            shots.mkdir(exist_ok=True)
            ctx = browser.new_context(viewport={"width": 900, "height": 1000})
            page = ctx.new_page()
            try:
                r = test(page, html, shots)
            except Exception as e:
                r = {"harness_error": str(e)[:300], "passed": 0}
            ctx.close()
            (shots / "result.json").write_text(json.dumps(r, indent=1), encoding="utf-8")
            summary[html.stem] = r
            print(f"{html.stem}: {r.get('passed')}/8 " +
                  " ".join(k for k, v in r.items() if v is False) + (f"  errors: {r.get('n_errors')}"
                  if r.get("n_errors") else ""), flush=True)
        browser.close()
    (PLAY / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
