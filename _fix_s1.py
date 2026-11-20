#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按页面图说重生成 s1（原本是封面的字节复制），不正文改动"""
import re, sys, urllib.request
from pathlib import Path

sys.path.insert(0, r"C:\afeng_tea")
import publish_new as P

ART = Path(r"C:\afeng_tea\articles\20261115三泡就淡的鸭屎香的两只盖碗阿凤姐.html")
html = ART.read_text(encoding="utf-8")

figs = re.findall(r'<figure class="scene-fig">(.*?)</figure>', html, re.S)
print(f"共 {len(figs)} 张场景图\n")
for i, f in enumerate(figs, 1):
    img = re.search(r'src="([^"]+)"', f)
    cap = re.search(r"<figcaption>(.*?)</figcaption>", f, re.S)
    cap = re.sub(r"<[^>]+>", "", cap.group(1)).strip() if cap else "(无图说)"
    print(f"  s{i}: {Path(img.group(1)).name if img else '?'}")
    print(f"      图说: {cap[:70]}")

# s1 的图说
cap1 = re.sub(r"<[^>]+>", "", re.search(r"<figcaption>(.*?)</figcaption>", figs[0], re.S).group(1)).strip()
print(f"\n→ 按 s1 图说重生成，构图依据：{cap1[:70]}")

key = P.load_env().get("SILICONFLOW_API_KEY")
prompt = f"{cap1}，静物特写，柔和自然光，极简构图"
url = P.gen_image(key, prompt)
print(f"✓ 生成成功 → {url[:80]}")
raw = urllib.request.urlopen(url, timeout=120).read()

out = Path(r"C:\afeng_tea\images\full\a202611154d957b-s1.webp")
w, h, sz = P.to_webp(raw, out, 869, 489)
print(f"✓ 覆盖 s1: {w}×{h}  {sz//1024}KB")

warns = P.audit_image(out)
print(f"✓ 像素合规: {'⚠ ' + ';'.join(warns) if warns else '通过（无正脸/无汉字）'}")

# 确认不再是封面的字节复制
cov = Path(r"C:\afeng_tea\images\full\a202611154d957b-cover.webp")
print(f"✓ 与封面不同: {'是' if out.read_bytes() != cov.read_bytes() else '否（仍重复！）'}")

# 页面里的 width/height 与实际像素核对
m = re.search(r'src="[^"]*-s1\.webp"[^>]*width="(\d+)"[^>]*height="(\d+)"', html) or \
    re.search(r'width="(\d+)"[^>]*height="(\d+)"[^>]*src="[^"]*-s1\.webp"', html)
print(f"✓ 页面标注: {m.group(1)}×{m.group(2)}  实际: {w}×{h}  → {'一致' if (int(m.group(1)), int(m.group(2))) == (w, h) else '不一致，需改页面'}")
