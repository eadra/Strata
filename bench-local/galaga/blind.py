#!/usr/bin/env python3
"""Copy every out/*.html and its play-test results to review/<letter>/ under a shuffled letter, so reviewers do not
know which quant or setting wrote it. The key is written to review-key.json (not inside review/)."""

import json
import random
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT, PLAY, REV = HERE / "out", HERE / "play", HERE / "review"

KEY = HERE / "review-key.json"
# games already lettered keep their letters; new games get the next ones (Z, then AA, AB, ...) in a shuffled order
key = json.loads(KEY.read_text(encoding="utf-8")) if KEY.exists() else {}
names = sorted(p.stem for p in OUT.glob("*.html") if p.stem not in key.values())
random.Random(20261002 + len(key)).shuffle(names)
REV.mkdir(exist_ok=True)
for i, name in enumerate(names, start=len(key)):
    letter = chr(ord("A") + i) if i < 26 else "A" + chr(ord("A") + i - 26)
    d = REV / letter
    d.mkdir(exist_ok=True)
    shutil.copy(OUT / f"{name}.html", d / "galaga.html")
    for f in (PLAY / name).glob("*"):
        shutil.copy(f, d / f.name)
    key[letter] = name
KEY.write_text(json.dumps(key, indent=1), encoding="utf-8")
print(" ".join(sorted(key)))
