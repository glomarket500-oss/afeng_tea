#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""底部 xhs-tags 改为空格分隔（与站方既有文章一致）"""
import re
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
SLUG = "20261115立冬之后换一壶秋茶阿凤姐教你顺时而饮"
ART = REPO / "articles" / f"{SLUG}.html"

TAGS = ["凤凰单丛", "立冬养生", "秋茶老丛", "顺时而饮",
        "潮州工夫茶", "老丛鸭屎香", "惠州茶叶店", "惠州买茶去哪"]

p = ART.read_text(encoding="utf-8")
old = re.search(r'<p class="xhs-tags">(.*?)</p>', p, re.S).group(1)
new = " ".join(f"#{t}" for t in TAGS)
p = p.replace(f'<p class="xhs-tags">{old}</p>', f'<p class="xhs-tags">{new}</p>')
ART.write_text(p, encoding="utf-8")
print("旧:", old)
print("新:", new)
