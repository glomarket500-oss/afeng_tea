#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地客观检测：文字残留（高通滤波响应）+ 肤色区域（人脸启发式）"""
import numpy as np
from PIL import Image
from pathlib import Path
import glob, sys

REPO = Path(r"C:\afeng_tea")
PNG = REPO / "_png"

def laplacian_energy(gray):
    """高通响应能量：文字/细线笔画区域会显著偏高"""
    k = np.array([[0,1,0],[1,-4,1],[0,1,0]], dtype=np.float64)
    h, w = gray.shape
    out = np.zeros((h - 2, w - 2), dtype=np.float64)
    for dy in range(3):
        for dx in range(3):
            out += k[dy, dx] * gray[dy:h - 2 + dy, dx:w - 2 + dx]
    return out

def skin_ratio(rgb):
    """YCrCb 肤色范围占比（粗略）"""
    y = rgb[..., 0]*0.299 + rgb[..., 1]*0.587 + rgb[..., 2]*0.114
    cr = (rgb[..., 0]-y)*0.713 + (rgb[..., 1]-y)*0.564
    cb = (rgb[..., 1]-y)*0.934 + (rgb[..., 2]-y)*0.180
    mask = (cr>133)&(cr<175)&(cb>77)&(cb<127)
    return mask.mean()

def runs_in_row(gray, thresh):
    """每行连续高响应像素的最长连续长度"""
    b = gray > thresh
    best = 0
    for row in b:
        c = 0
        for v in row:
            c = c + 1 if v else 0
            if c > best: best = c
    return best

files = sorted(glob.glob(str(PNG / "qiuchu-*.png")))
print(f"{'file':22s} {'size':12s} {'lap_energy':>11s} {'long_run':>9s} {'skin%':>7s} {'bright%':>8s}  判定")
print("-" * 88)
for f in files:
    im = Image.open(f).convert("RGB")
    rgb = np.asarray(im).astype(np.float64)
    gray = np.asarray(im.convert("L")).astype(np.float64)
    lap = laplacian_energy(gray)
    e = lap.std()
    # 自适应阈值：取高通响应的 98 百分位
    thr = np.percentile(np.abs(lap), 99.0)
    lr = runs_in_row(gray > 0, 0)  # 占位，稍后算
    # 文字型响应：连续笔画 → 同一行内连续高响应像素
    b = np.abs(lap) > max(thr, 25)
    best = 0
    for row in b:
        c = 0
        for v in row:
            c = c + 1 if v else 0
            if c > best: best = c
    sk = skin_ratio(rgb) * 100
    br = (gray > 245).mean() * 100
    name = Path(f).stem.replace("qiuchu-", "")
    flags = []
    if best >= 12: flags.append(f"疑似笔画(连续{best}px)")
    if sk > 3.0: flags.append(f"肤色{sk:.1f}%")
    if br > 25: flags.append(f"高光过曝{br:.0f}%")
    print(f"{name:22s} {str(im.size):12s} {e:11.2f} {best:9d} {sk:6.2f}% {br:7.1f}%  {'; '.join(flags) or 'OK'}")
