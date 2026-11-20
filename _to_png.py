#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 webp 转成 png 以便视觉检查"""
from PIL import Image
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
OUT = Path(r"C:\Users\Administrator\AppData\Local\hermes\cache\scratch\imgcheck")
OUT.mkdir(parents=True, exist_ok=True)

for f in sorted((REPO / "images" / "full").glob("qiuchu-*.webp")):
    im = Image.open(f).convert("RGB")
    p = OUT / (f.stem + ".png")
    im.save(p)
    print(p, im.size)
