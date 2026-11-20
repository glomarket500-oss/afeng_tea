#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给已生成文章去水印：裁掉图片底部 15%（Kolors 水印区），按真实尺寸回写页面标注。
不重新生图 → 不会引入新的伪汉字/人脸风险。"""
import io
import re
import sys
from pathlib import Path

sys.path.insert(0, r"C:\afeng_tea")
from PIL import Image

REPO = Path(r"C:\afeng_tea")
FULL = REPO / "images" / "full"
THUMB = REPO / "images" / "thumb"
BOTTOM_CUT = 0.15
MAX_BYTES = 200 * 1024

ARTS = [
    REPO / "articles" / "20261115三泡就淡的鸭屎香的两只盖碗阿凤姐.html",
    REPO / "articles" / "20261115一只红泥炉半袋榄核炭阿凤姐.html",
]


def crop_16x9(im, bottom_cut=BOTTOM_CUT):
    """先裁底部，再居中裁成 16:9（不拉伸）"""
    if bottom_cut > 0:
        im = im.crop((0, 0, im.width, int(im.height * (1 - bottom_cut))))
    w, h = im.size
    target = 16 / 9
    if w / h > target:                 # 偏宽 → 裁两侧
        nw = round(h * target)
        left = (w - nw) // 2
        im = im.crop((left, 0, left + nw, h))
    elif w / h < target:               # 偏高 → 裁上下
        nh = round(w / target)
        top = (h - nh) // 2
        im = im.crop((0, top, w, top + nh))
    return im


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


for art in ARTS:
    if not art.exists():
        print(f"跳过（不存在）: {art.name}")
        continue
    html = art.read_text(encoding="utf-8")
    imgs = re.findall(r'src="\.\./images/full/([0-9a-z]+)-(cover|s\d)\.webp"', html)
    prefix = imgs[0][0] if imgs else None
    keys = ["cover"] + sorted({k for _, k in imgs if k != "cover"})
    print(f"\n=== {art.name[:34]}…  prefix={prefix}  图 {len(keys)} 张 ===")

    newdims = {}
    for k in keys:
        p = FULL / f"{prefix}-{k}.webp"
        if not p.exists():
            print(f"  {k}: 文件缺失，跳过")
            continue
        old = Image.open(p).convert("RGB")
        ow, oh = old.size
        im = crop_16x9(old)
        sz = save_webp(im, p)
        newdims[k] = im.size
        print(f"  {k}: {ow}×{oh} → {im.width}×{im.height}  {sz//1024}KB")
        if k == "cover":
            th = im.copy()
            th.thumbnail((400, 10000), Image.LANCZOS)
            save_webp(th, THUMB / f"{art.stem}-hero.webp")
            print(f"      缩图 → {th.width}×{th.height}")

    # 按真实尺寸回写页面 width/height
    for k, (w, h) in newdims.items():
        pat = re.compile(r'(src="\.\./images/full/' + re.escape(prefix) + "-"
                         + k + r'\.webp"[^>]*?width=")\d+(" height=")\d+(")')
        html, n = pat.subn(lambda m: f"{m.group(1)}{w}{m.group(2)}{h}{m.group(3)}", html)
        if n:
            print(f"  页面回写 {k}: {w}×{h}（命中 {n} 处）")
    art.write_text(html, encoding="utf-8")
