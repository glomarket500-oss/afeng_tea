#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""线上验证（带 DNS 重试）：图片尺寸已改 738x415 + 封面已换 + 模块完整"""
import re
import socket
import time
import urllib.parse
import urllib.request

SLUG = "20261115三泡就淡的鸭屎香的两只盖碗阿凤姐"
URL = f"https://feng-tea.com/articles/{urllib.parse.quote(SLUG)}.html"
UA = {"User-Agent": "Mozilla/5.0"}


def fetch(u, tries=6):
    last = None
    for i in range(tries):
        try:
            return urllib.request.urlopen(
                urllib.request.Request(u, headers=UA), timeout=40).read()
        except (socket.gaierror, urllib.error.URLError, TimeoutError) as e:
            last = e
            print(f"    (第{i+1}次失败 {type(e).__name__}，15s 后重试)")
            time.sleep(15)
    raise SystemExit(f"取不到 {u}: {last}")


html = None
for i in range(4):
    try:
        html = fetch(URL, tries=3).decode("utf-8", "ignore")
        break
    except SystemExit:
        print("  整轮失败，再等 30s")
        time.sleep(30)
if html is None:
    raise SystemExit("网络持续不可达，稍后再验")

print(f"文章页 HTTP 200  {len(html)} 字节")
dims = set(re.findall(r'width="(\d+)" height="(\d+)"', html))
print(f"页面图片标注: {dims}  → {'✅ 已改 738×415' if dims == {('738', '415')} else '⚠ 仍是旧值'}")

raw = fetch("https://feng-tea.com/images/full/a202611154d957b-cover.webp")
print(f"封面线上: {len(raw)//1024}KB  → {'✅ 裁剪版' if len(raw) < 20000 else '⚠ 原始带水印版'}")
raw2 = fetch("https://feng-tea.com/images/full/a202611154d957b-s2.webp")
print(f"s2 线上:  {len(raw2)//1024}KB  → {'✅ 裁剪版' if len(raw2) < 42000 else '⚠ 原始带水印版'}")

for label, pat in [("lead", r'class="lead"'), ("faq-q", r'class="faq-q"'),
                   ("场景图", r'class="scene-fig"'), ("GEO", "📍"),
                   ("xhs-tags", r'class="xhs-tags"'),
                   ("article-tags", r'class="article-tags"')]:
    n = len(re.findall(pat, html))
    print(f"  {label:14s} {n}" + ("  ⚠" if n == 0 else ""))

bad = [k for k in ["林玉凤", "1079790744", "afeng-tea.vercel.app"] if k in html]
print(f"  隐私红线        {'❌ ' + str(bad) if bad else '✅ 干净'}")
