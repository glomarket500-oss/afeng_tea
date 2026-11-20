#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补裁《三泡就淡》的封面（og:image 用，页面内没有 <img>，上次漏了）并重生缩图"""
import io
import sys
from pathlib import Path

sys.path.insert(0, r"C:\afeng_tea")
from PIL import Image

REPO = Path(r"C:\afeng_tea")
PREFIX = "a202611154d957b"
SLUG = "20261115三泡就淡的鸭屎香的两只盖碗阿凤姐"
BOTTOM_CUT = 0.15
MAX_BYTES = 200 * 1024
RES = getattr(getattr(Image, "Resampling", Image), "LANCZOS")


def save_webp(im, path, quality=82):
    q = quality
    while q >= 45:
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=q, method=6)
        if buf.tell() <= MAX_BYTES or q == 45:
            path.write_bytes(buf.getvalue())
            return buf.tell()
        q -= 6
    raise RuntimeError("压缩失败")


cov = REPO / "images" / "full" / f"{PREFIX}-cover.webp"
im = Image.open(cov).convert("RGB")
ow, oh = im.size
im = im.crop((0, 0, im.width, int(im.height * (1 - BOTTOM_CUT))))
w, h = im.size
target = 16 / 9
if w / h > target:
    nw = round(h * target)
    im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
elif w / h < target:
    nh = round(w / target)
    im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
sz = save_webp(im, cov)
print(f"封面: {ow}×{oh} → {im.width}×{im.height}  {sz//1024}KB")

th = im.copy()
th.thumbnail((400, 400), RES)
tsz = save_webp(th, REPO / "images" / "thumb" / f"{SLUG}-hero.webp")
print(f"缩图: {th.width}×{th.height}  {tsz//1024}KB")
