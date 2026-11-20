#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
纯像素判定（不依赖视觉模型）：
A) 文字/汉字检测 —— 笔画宽度分析：
   汉字是「小尺寸、高对比、笔画宽度一致(WS~1-3px)、大量小连通域」的结构。
   B) 人脸检测 —— 肤色区域 + 椭圆对称性；
   C) 主体粗判 —— 色彩/纹理统计。
输出可解释的中间量，便于人工复核。
"""
from PIL import Image, ImageFilter
import glob, math
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
PNG = REPO / "_png"


def analyze(path):
    im = Image.open(path).convert("L")
    w, h = im.size
    g = im.resize((w // 2, h // 2), Image.BILINEAR)   # 降采样，便于连通域分析
    W, H = g.size
    px = g.load()

    # 二值化（Otsu）
    hist = [0] * 256
    for y in range(H):
        for x in range(W):
            hist[px[x, y]] += 1
    total = W * H
    s = sum(i * hist[i] for i in range(256))
    sumB = wB = 0
    bestT = 128
    for t in range(256):
        wB += hist[t]
        if wB == 0:
            continue
        wF = total - wB
        if wF == 0:
            break
        sumB += t * hist[t]
        mB = sumB / wB
        mF = (s - sumB) / wF
        var = wB * wF * (mB - mF) ** 2
        if var > bestT:
            bestT = var
    thr = 0
    s2 = 0; wB = 0
    bestVar = -1
    for t in range(256):
        wB += hist[t]
        if wB == 0: continue
        s2 += t * hist[t]
        mB = s2 / wB
        wF = total - wB
        if wF == 0: break
        mF = (s - s2) / wF
        var = wB * wF * (mB - mF) ** 2
        if var > bestVar: bestVar = var; thr = t
    binar = [[1 if px[x, y] > thr else 0 for x in range(W)] for y in range(H)]

    # 连通域（4邻域，栈实现）
    seen = [[0] * W for _ in range(H)]
    blobs = []
    for y0 in range(H):
        for x0 in range(W):
            if binar[y0][x0] and not seen[y0][x0]:
                stack = [(x0, y0)]; seen[y0][x0] = 1; pts = []
                while stack:
                    x, y = stack.pop(); pts.append((x, y))
                    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < W and 0 <= ny < H and binar[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = 1; stack.append((nx, ny))
                blobs.append(pts)

    areas = sorted((len(b) for b in blobs), reverse=True)
    # 汉字特征：大量小连通域（笔画分离），面积 4~200，且整体前景密度适中
    small = [a for a in areas if 4 <= a <= 200]
    tiny_ratio = len(small) / max(1, len(blobs))
    # 笔画宽度估计：中等连通域的等效直径分布
    widths = []
    for b in blobs:
        a = len(b)
        if 20 <= a <= 400:
            xs = [p[0] for p in b]; ys = [p[1] for p in b]
            d = math.sqrt(4 * a / math.pi)
            widths.append(d)
    med_w = sorted(widths)[len(widths)//2] if widths else 0

    # 人脸启发式：肤色比例 + 中心椭圆区肤色聚集
    rgb = Image.open(path).convert("RGB").resize((W, H), Image.BILINEAR)
    rp = rgb.load()
    skin = 0; center_skin = 0; cx, cy = W//2, H//2
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            R, G, B = rp[x, y]
            Y = 0.299*R + 0.587*G + 0.114*B
            Cr = (R-Y)*0.713 + (G-Y)*0.564
            Cb = (G-Y)*0.934 + (B-Y)*0.180
            if 133 < Cr < 180 and 77 < Cb < 130 and R > 60:
                skin += 1
                if ((x-cx)/(W*0.28))**2 + ((y-cy)/(H*0.30))**2 < 1:
                    center_skin += 1
    tot = (H//2 + 1) * (W//2 + 1)
    return dict(blobs=len(blobs), small=len(small), tiny_ratio=tiny_ratio,
                med_w=med_w, skin=skin/tot*100, cskin=center_skin/tot*100,
                biggest=areas[0] if areas else 0)


print(f"{'图':6s} {'连通域':>7s} {'小域':>7s} {'小域占比':>9s} {'笔画宽':>7s} {'肤色%':>7s} {'中心肤色%':>10s}  判定")
print("-" * 84)
for f in sorted(glob.glob(str(PNG / "qiuchu-*.png"))):
    r = analyze(f)
    flags = []
    if r["skin"] > 1.5:
        flags.append(f"有肤色{r['skin']:.1f}%")
    if r["cskin"] > 0.8:
        flags.append(f"中心肤色聚集{r['cskin']:.1f}%")
    if r["small"] > 60 and r["tiny_ratio"] > 0.55 and 0.8 <= r["med_w"] <= 3.5:
        flags.append(f"疑似文字(小域{r['small']}/宽{r['med_w']:.1f})")
    print(f"{Path(f).stem.replace('qiuchu-',''):6s} {r['blobs']:7d} {r['small']:7d} "
          f"{r['tiny_ratio']*100:8.1f}% {r['med_w']:7.1f} {r['skin']:6.2f}% {r['cskin']:9.2f}%  "
          f"{'; '.join(flags) or '无文字/无人脸迹象'}")
