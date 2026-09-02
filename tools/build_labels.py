#!/usr/bin/env python3
"""Render a label image per bottle into img/labels/<id>.png from data/catalog.json.
Typographic labels in the site's palette — placeholders until the shop supplies bottle shots."""
import json, pathlib, textwrap
from PIL import Image, ImageDraw, ImageFont

root = pathlib.Path(__file__).resolve().parent.parent
feed = json.loads((root / "data" / "catalog.json").read_text())
out_dir = root / "img" / "labels"
out_dir.mkdir(parents=True, exist_ok=True)

F = "/System/Library/Fonts/Supplemental/"
DISPLAY = F + "Impact.ttf"
SERIF_I = F + "Georgia Italic.ttf"
SANS_B = F + "Arial Narrow Bold.ttf"

PAPER = (253, 250, 242)
INK = (23, 18, 14)
CAT_COLOR = {
    "sparkling": (184, 137, 28), "white": (194, 161, 42), "rose": (212, 96, 127), "orange": (201, 106, 31),
    "red": (149, 9, 81), "sake": (63, 91, 140), "large": (23, 18, 14), "dessert": (107, 63, 160), "gift": (23, 18, 14),
}
W, H = 600, 780

def tint(rgb, amount):
    return tuple(int(PAPER[i] + (rgb[i] - PAPER[i]) * amount) for i in range(3))

def fit_lines(draw, text, font_path, max_w, start, min_size, max_lines):
    """Largest size at or below `start` whose wrapped text fits max_lines."""
    for size in range(start, min_size - 1, -2):
        font = ImageFont.truetype(font_path, size)
        avg = draw.textlength("ABCDEFGHIJKLMNOPQRSTUVWXYZ", font=font) / 26
        lines = textwrap.wrap(text.upper(), width=max(8, int(max_w / avg)))
        if len(lines) <= max_lines and all(draw.textlength(l, font=font) <= max_w for l in lines):
            return font, lines
    font = ImageFont.truetype(font_path, min_size)
    return font, textwrap.wrap(text.upper(), width=22)[:max_lines]

for w in feed["works"]:
    col = CAT_COLOR.get(w["category"], INK)
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    # colour band at the top, fading into paper
    for y in range(0, 230):
        d.line([(0, y), (W, y)], fill=tint(col, 0.22 * (1 - y / 230)))
    # double rule frame
    d.rectangle([18, 18, W - 19, H - 19], outline=INK, width=4)
    d.rectangle([32, 32, W - 33, H - 33], outline=INK, width=1)

    # category eyebrow
    f_cat = ImageFont.truetype(SANS_B, 26)
    cat = "  ".join(w["series"].upper())
    d.text(((W - d.textlength(cat, font=f_cat)) / 2, 72), cat, font=f_cat, fill=col)

    # title
    f_title, lines = fit_lines(d, w["title"], DISPLAY, W - 130, 64, 34, 4)
    lh = f_title.size * 1.05
    y = 130
    for line in lines:
        d.text(((W - d.textlength(line, font=f_title)) / 2, y), line, font=f_title, fill=INK)
        y += lh
    y += 18
    d.line([(150, y), (W - 150, y)], fill=INK, width=2)
    y += 26

    # origin
    f_or = ImageFont.truetype(SERIF_I, 28)
    for line in textwrap.wrap(w["place"], width=34):
        d.text(((W - d.textlength(line, font=f_or)) / 2, y), line, font=f_or, fill=INK)
        y += 36

    # vintage / size roundel
    f_big = ImageFont.truetype(DISPLAY, 92)
    mark = str(w["year"]) if w["year"] else w["size"]
    cy = H - 250
    d.ellipse([W / 2 - 92, cy - 92, W / 2 + 92, cy + 92], outline=col, width=5)
    tw = d.textlength(mark, font=f_big)
    d.text(((W - tw) / 2, cy - 58), mark, font=f_big, fill=col)

    # stamp
    f_st = ImageFont.truetype(DISPLAY, 30)
    st = "BIG NOSE  ·  FULL BODY"
    sw = d.textlength(st, font=f_st) + 44
    sx, sy = (W - sw) / 2, H - 118
    d.rounded_rectangle([sx, sy, sx + sw, sy + 54], radius=8, fill=INK)
    d.text((sx + 22, sy + 8), st, font=f_st, fill=PAPER)
    f_sm = ImageFont.truetype(SANS_B, 20)
    sm = "389 7TH AVE  ·  PARK SLOPE, BROOKLYN"
    d.text(((W - d.textlength(sm, font=f_sm)) / 2, H - 52), sm, font=f_sm, fill=INK)

    img.save(out_dir / f"{w['id']}.png", optimize=True)

print(f"{len(feed['works'])} labels → img/labels/")
