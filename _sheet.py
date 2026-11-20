#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 7 张图拼成联表（2 列），标序号，供视觉复核"""
from PIL import Image, ImageDraw
from pathlib import Path
REPO = Path(r"C:\afeng_tea")
OUT = REPO / "_png"
names = ["cover", "s1", "s2", "s3", "s4", "s5", "s6"]
CW, CH = 480, 270
cols = 2
rows = (len(names) + cols - 1) // cols
pad, lab = 10, 28
sheet = Image.new("RGB", (cols * (CW + pad) + pad, rows * (CH + pad + lab) + pad), (250, 248, 244))
d = ImageDraw.Draw(sheet)
for i, n in enumerate(names):
    p = OUT / f"qiuchu-{n}.png"
    r, c = divmod(i, cols)
    x = pad + c * (CW + pad)
    y = pad + r * (CH + pad + lab)
    im = Image.open(p).convert("RGB")
    im = im.resize((CW, CH), Image.LANCZOS)
    sheet.paste(im, (x, y))
    d.rectangle([x, y, x + CW, y + CH], outline=(180, 170, 155))
    d.text((x + 4, y + CH + 6), f"#{i} {n}  {Image.open(p).size}", fill=(40, 35, 30))
sheet.save(REPO / "_contact_sheet.png")
print("saved", REPO / "_contact_sheet.png", sheet.size)
