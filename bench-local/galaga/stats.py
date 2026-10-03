"""Generation stats per run from out/*.json: tokens, wall time, rate over the whole request, finish, file size."""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
rows = []
for p in sorted(q for q in (HERE / "out").glob("*.json") if not q.name.endswith(".raw.json")):
    r = json.loads(p.read_text(encoding="utf-8"))
    m = r["metrics"]; otok = r["usage"]["completion_tokens"]
    rows.append({"run": p.stem, "finish": r["finish_reason"], "out_tokens": otok,
                 "thinking_chars": r["thinking_chars"], "wall_min": round(r["wall_s"] / 60, 1),
                 "tok_s": round(otok / m["duration_s"], 1), "html_lines": r["html_lines"]})
for x in rows: print(x)
(HERE / "gen-stats.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
