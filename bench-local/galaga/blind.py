#!/usr/bin/env python3
"""Copy every out/*.html and its play-test results to review/<letter>/ under a shuffled letter, so reviewers do not
know which quant or setting wrote it. The key is written to review-key.json (not inside review/)."""

import json
import random
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT, PLAY, REV = HERE / "out", HERE / "play", HERE / "review"

names = sorted(p.stem for p in OUT.glob("*.html"))
random.Random(20261002).shuffle(names)
REV.mkdir(exist_ok=True)
key = {}
for i, name in enumerate(names):
    letter = chr(ord("A") + i)
    d = REV / letter
    d.mkdir(exist_ok=True)
    shutil.copy(OUT / f"{name}.html", d / "galaga.html")
    for f in (PLAY / name).glob("*"):
        shutil.copy(f, d / f.name)
    key[letter] = name
(HERE / "review-key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")
print(" ".join(sorted(key)))
