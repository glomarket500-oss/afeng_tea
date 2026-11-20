#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""线上验证：图片尺寸已改 738x415 + 封面文件已换（去水印）+ 页面模块完整"""
import re
import urllib.parse
import urllib.request

SLUG = "20261115三泡就淡的鸭屎香的两只盖碗阿凤姐"
URL = f"https://feng-tea.com/articles/{urllib.parse.quote(SLUG)}.html"
UA = {"User-Agent": "Mozilla/5.0"}


def fetch(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read()


html = fetch(URL).decode("utf-8", "ignore")
print(f"文章页 HTTP 200  {len(html)} 字节")

dims = set(re.findall(r'width="(\d+)" height="(\d+)"', html))
print(f"页面图片标注尺寸: {dims}  → {'✅ 已更新为 738×415' if dims == {('738', '415')} else '⚠ 仍是旧值'}")

cov_url = "https://feng-tea.com/images/full/a202611154d957b-cover.webp"
raw = fetch(cov_url)
print(f"封面线上大小: {len(raw)//1024}KB  → {'✅ 已是裁剪版（≤20KB）' if len(raw) < 20000 else '⚠ 仍是原始带水印版'}")

s2 = fetch("https://feng-tea.com/images/full/a202611154d957b-s2.webp")
print(f"s2 线上大小:   {len(s2)//1024}KB  → {'✅ 已是裁剪版（≤40KB）' if len(s2) < 42000 else '⚠ 仍是原始带水印版'}")

for label, pat in [("lead 导语", r'class="lead"'), ("FAQ", r'class="faq-q"'),
                   ("场景图", r'class="scene-fig"'), ("GEO", r"📍"),
                   ("xhs-tags", r'class="xhs-tags"'),
                   ("article-tags", r'class="article-tags"')]:
    n = len(re.findall(pat, html))
    print(f"  {label:14s} {n}" + ("  ⚠" if n == 0 else ""))

bad = [k for k in ["林玉凤", "1079790744", "afeng-tea.vercel.app"] if k in html]
print(f"  隐私红线        {'❌ ' + str(bad) if bad else '✅ 干净'}")
