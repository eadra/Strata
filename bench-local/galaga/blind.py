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
# only games that were play-tested (a run with no code, like a Sonnet run that spent its cap thinking, has no play dir)
names = sorted(p.stem for p in OUT.glob("*.html") if p.stem not in key.values() and (PLAY / p.stem).is_dir())
random.Random(20261002 + len(key)).shuffle(names)
REV.mkdir(exist_ok=True)


def letters():
    i = 0
    while True:
        yield chr(ord("A") + i) if i < 26 else chr(ord("A") + i // 26 - 1) + chr(ord("A") + i % 26)
        i += 1


unused = (l for l in letters() if l not in key)
for name in names:
    letter = next(unused)
    d = REV / letter
    d.mkdir(exist_ok=True)
    shutil.copy(OUT / f"{name}.html", d / "galaga.html")
    for f in (PLAY / name).glob("*"):
        shutil.copy(f, d / f.name)
    key[letter] = name
KEY.write_text(json.dumps(key, indent=1), encoding="utf-8")
print(" ".join(sorted(key)))
