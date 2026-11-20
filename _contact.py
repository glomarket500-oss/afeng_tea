#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成拼图 + JPEG 副本，便于视觉检查"""
from PIL import Image, ImageOps, ImageDraw
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
OUT = Path(r"C:\Users\Administrator\AppData\Local\hermes\cache\scratch\imgcheck")
OUT.mkdir(parents=True, exist_ok=True)

files = ["qiuchu-cover", "qiuchu-s1", "qiuchu-s2", "qiuchu-s3", "qiuchu-s4", "qiuchu-s5", "qiuchu-s6"]
ims = []
for name in files:
    im = Image.open(REPO / "images" / "full" / f"{name}.webp").convert("RGB")
    im.save(OUT / f"{name}.jpg", "JPEG", quality=90)
    ims.append((name, im))

# 单张 s2 的放大版（提高可读性）
ImageOps.fit(ims[2][1], (1300, 731), method=Image.LANCZOS).save(OUT / "s2_big.jpg", "JPEG", quality=92)

# 拼图 2x4
cw, ch = 640, 360
sheet = Image.new("RGB", (cw * 2, ch * 4), "white")
d = ImageDraw.Draw(sheet)
for i, (name, im) in enumerate(ims):
    t = ImageOps.fit(im, (cw, ch), method=Image.LANCZOS)
    x, y = (i % 2) * cw, (i // 2) * ch
    sheet.paste(t, (x, y))
    d.rectangle([x, y, x + 200, y + 22], fill="black")
    d.text((x + 6, y + 6), name, fill="white")
sheet.save(OUT / "contact.jpg", "JPEG", quality=90)
print("done:", OUT / "contact.jpg", sheet.size)
