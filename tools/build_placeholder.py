#!/usr/bin/env python3
"""Draw the on-brand stand-in used when a bottle has no photograph yet.

Site palette: paper #f4efe4, cream #fdfaf2, ink #17120e, wine #950951.
A bottle silhouette on the shop's paper stock, wordmark on a wine-coloured plate —
so a photo-less product still reads as ours rather than as a broken image.
"""
from PIL import Image, ImageDraw, ImageFont
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
W, H = 420, 559
PAPER, CREAM, INK, WINE = (244,239,228), (253,250,242), (23,18,14), (149,9,81)
F = "/System/Library/Fonts/Supplemental/"

img = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(img)

# faint paper texture: soft diagonal rules, the shop's own chalkboard feel
for x in range(-H, W, 26):
    d.line([(x, H), (x + H, 0)], fill=(238, 232, 219), width=1)

# bottle silhouette, centred
cx, top, bot = W // 2, 96, H - 132
bw, nw = 104, 34                      # body width, neck width
shoulder = top + 118
body = [(cx-nw//2, top), (cx+nw//2, top), (cx+nw//2, shoulder-46),
        (cx+bw//2, shoulder), (cx+bw//2, bot), (cx-bw//2, bot),
        (cx-bw//2, shoulder), (cx-nw//2, shoulder-46)]
d.polygon(body, fill=CREAM, outline=INK)
for off in (0, 1, 2):                 # a heavier hand-drawn outline
    d.line(body + [body[0]], fill=INK, width=1)
d.rectangle([cx-nw//2, top, cx+nw//2, top+16], fill=WINE)          # capsule
d.rectangle([cx-bw//2+13, shoulder+52, cx+bw//2-13, bot-46], fill=PAPER, outline=INK)  # label

def fit(text, path, size, maxw):
    while size > 8:
        f = ImageFont.truetype(path, size)
        if d.textlength(text, font=f) <= maxw: return f
        size -= 1
    return ImageFont.truetype(path, 8)

f1 = fit("PHOTO", F + "Impact.ttf", 25, bw - 40)
f2 = fit("TO COME", F + "Impact.ttf", 25, bw - 40)
d.text((cx, shoulder + 74), "PHOTO", font=f1, fill=INK, anchor="ma")
d.text((cx, shoulder + 100), "TO COME", font=f2, fill=INK, anchor="ma")

# wordmark plate
plate_top = H - 104
d.rectangle([46, plate_top, W - 46, plate_top + 52], fill=INK)
fw = fit("BIG NOSE · FULL BODY", F + "Arial Narrow Bold.ttf", 24, W - 130)
d.text((W // 2, plate_top + 26), "BIG NOSE · FULL BODY", font=fw, fill=PAPER, anchor="mm")
fs = fit("ASK US ABOUT THIS BOTTLE", F + "Arial Narrow Bold.ttf", 15, W - 110)
d.text((W // 2, H - 34), "ASK US ABOUT THIS BOTTLE", font=fs, fill=WINE, anchor="mm")

out = ROOT / "img" / "bottle-placeholder.jpg"
img.save(out, "JPEG", quality=82)
print("wrote", out.relative_to(ROOT), img.size)
