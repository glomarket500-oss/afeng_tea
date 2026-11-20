#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取线上文章页 + 首页卡片，dump 关键片段"""
import urllib.request, urllib.parse, re
UA = {"User-Agent": "Mozilla/5.0"}
SLUG = "20261115立冬之后换一壶秋茶阿凤姐教你顺时而饮"

def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40) as r:
        return r.read().decode("utf-8", "ignore")

b = get("https://feng-tea.com/articles/" + urllib.parse.quote(SLUG + ".html"))
idx = get("https://feng-tea.com/index.html")

out = []
out.append("========== 文章页 head 区 ==========")
out.append(b[:b.find("</head>") + 7])
out.append("\n\n========== article-tags / tags / xhs-tags 片段 ==========")
for m in re.finditer(r'<(div class="article-tags"|div class="tags"|p class="xhs-tags")[^>]*>', b):
    s = m.start()
    out.append(f"\n--- @{s} ---\n" + b[s:s + 900])
out.append("\n\n========== FAQ 区 ==========")
i = b.find("FAQ")
out.append(b[i:i + 1200] if i != -1 else "!! 未找到 FAQ 字样")
out.append("\n\n========== JSON-LD ==========")
for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', b, re.S):
    out.append(m.group(1))
out.append("\n\n========== 首页卡片 ==========")
m = re.search(r'<article class="article-card.*?id="article-' + re.escape(SLUG) + r'".*?</article>', idx, re.S)
out.append(m.group(0) if m else "!! 未找到卡片")

txt = "\n".join(out)
open(r"C:\afeng_tea\_dump.txt", "w", encoding="utf-8").write(txt)
print("已写入 _dump.txt，长度", len(txt))
