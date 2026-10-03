"""One contact sheet per game: play/<name>/sheet.png = title, 8 s after Enter, 30 s, 60 s, end (downscaled)."""
from pathlib import Path
from PIL import Image, ImageDraw
PLAY = Path(__file__).resolve().parent / "play"
FRAMES = ["1-title.png", "3-after-enter-8s.png", "4-play-030s.png", "4-play-060s.png", "5-end.png"]
for d in sorted(p for p in PLAY.iterdir() if p.is_dir()):
    ims = [Image.open(d / f).convert("RGB").resize((360, 400)) for f in FRAMES if (d / f).exists()]
    sheet = Image.new("RGB", (360 * len(ims), 420), "white")
    for i, im in enumerate(ims):
        sheet.paste(im, (360 * i, 20))
    ImageDraw.Draw(sheet).text((4, 4), d.name + "   " + "  |  ".join(FRAMES), fill="black")
    sheet.save(d / "sheet.png")
print("ok")
