"""Join the blind reviews (review/*/scores.json), the key, play-test results and generation stats into results.json
and print one table row per run plus per-quant means."""
import json
from pathlib import Path
from statistics import mean
HERE = Path(__file__).resolve().parent
key = json.loads((HERE / "review-key.json").read_text())
gen = {r["run"]: r for r in json.loads((HERE / "gen-stats.json").read_text())}
play = json.loads((HERE / "play" / "summary.json").read_text())
GROUPS = {"A": "deliverable", "B": "presentation", "C": "player", "D": "enemies", "E": "tractor", "F": "stages",
          "G": "sound", "H": "polish"}
rows = []
for letter, run in sorted(key.items(), key=lambda kv: kv[1]):
    s = json.loads((HERE / "review" / letter / "scores.json").read_text(encoding="utf-8"))
    items = s["items"]
    tot = sum(v["score"] for v in items.values())
    by = {g: sum(v["score"] for k, v in items.items() if k[0] == g) for g in GROUPS}
    sev = [b for b in s["bugs"] if b["severity"] == "severe"]
    rows.append({"run": run, "letter": letter, "total": tot, "groups": by, "verdict": s["verdict"],
                 "severe_bugs": len(sev), "minor_bugs": len(s["bugs"]) - len(sev),
                 "play_checks": play[run].get("passed"), **{k: gen[run][k] for k in
                 ("finish", "out_tokens", "wall_min", "tok_s", "html_lines")}})
(HERE / "results.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
print(f"{'run':30} {'L'} {'score':>5} {'play':>4} {'sev':>3} {'tok':>6} {'min':>5} {'tok/s':>6}  verdict")
for r in rows:
    print(f"{r['run']:30} {r['letter']} {r['total']:>5} {r['play_checks']:>4} {r['severe_bugs']:>3} "
          f"{r['out_tokens']:>6} {r['wall_min']:>5} {r['tok_s']:>6}  {r['verdict']}  {r['groups']}")
for q in ("iq3_xxs", "iq3_s", "unsloth-ud-q4_k_xl"):
    rs = [r for r in rows if r["run"].startswith(q + "-")]
    print(q, "mean", round(mean(r["total"] for r in rs), 1), "playable", sum(r["verdict"] in ("plays well",
          "playable with flaws") for r in rs), "of", len(rs))
