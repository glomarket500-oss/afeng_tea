#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单图实测：验证 gen_image 的退避重试 + 下载 + WebP + 像素合规检测整条路"""
import sys, time, urllib.request
from pathlib import Path

sys.path.insert(0, r"C:\afeng_tea")
import publish_new as P

env = P.load_env()
key = env.get("SILICONFLOW_API_KEY")
print(f"SILICONFLOW_API_KEY: {'存在 len=' + str(len(key)) if key else '缺失'}")

t0 = time.time()
url = P.gen_image(key, "木质茶席上一只白瓷盖碗，琥珀色茶汤，柔和晨光，极简构图")
print(f"✓ 生图成功 {time.time()-t0:.1f}s  → {url[:90]}")

raw = urllib.request.urlopen(url, timeout=120).read()
out = Path(r"C:\afeng_tea\images\full\_selftest.webp")
w, h, sz = P.to_webp(raw, out, 869, 489)
print(f"✓ WebP: {w}×{h}  {sz//1024}KB")

try:
    warns = P.audit_image(out)
    print(f"✓ 像素合规: {'⚠ ' + ';'.join(warns) if warns else '通过（无正脸/无汉字）'}")
except Exception as e:
    print(f"✗ audit_image 报错: {e}")
