#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""客观图像分析：主色调分布 / 红色占比 / 暗背景 / 高饱和块 → 判断是否是红灯笼/庙宇场景"""
import numpy as np
from PIL import Image
import glob
from pathlib import Path

PNG = Path(r"C:\afeng_tea\_png")
for f in sorted(glob.glob(str(PNG / "qiuchu-*.png"))):
    im = Image.open(f).convert("RGB")
    rgb = np.asarray(im).astype(np.int16)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(axis=2); mn = rgb.min(axis=2)
    sat = (mx - mn)
    red = (r > 120) & (r - g > 45) & (r - b > 45)
    dark = (mx < 70)
    print(f"\n=== {Path(f).stem} {im.size} ===")
    print(f"  均值 RGB      = ({r.mean():.0f},{g.mean():.0f},{b.mean():.0f})")
    print(f"  饱和度均值    = {sat.mean():.1f}")
    print(f"  红色像素占比  = {red.mean()*100:5.1f}%")
    print(f"  暗部(<70)占比 = {dark.mean()*100:5.1f}%")
    print(f"  亮部(>240)占比= {(mx>240).mean()*100:5.1f}%")
    # 上半 vs 下半 的红色差（庙宇场景通常上半天空+屋顶，下半红柱红门）
    top_red = red[:im.size[1]//2].mean()*100
    bot_red = red[im.size[1]//2:].mean()*100
    print(f"  上半红 {top_red:.1f}% / 下半红 {bot_red:.1f}%  (差 {top_red-bot_red:+.1f})")
    # 四角取色
    w, h = im.size
    for nm, (x, y) in {"左上":(60,60),"右上":(w-60,60),"左下":(60,h-60),"右下":(w-60,h-60),
                        "正中":(w//2,h//2)}.items():
        print(f"    {nm} = {tuple(rgb[y,x])}")
