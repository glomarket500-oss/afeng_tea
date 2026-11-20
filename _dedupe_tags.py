#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理已发布文章页里重复的 .article-tags（保留第一份）"""
import re
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
targets = list((REPO / "articles").glob("20261115三泡就淡*.html"))
if not targets:
    raise SystemExit("找不到目标文章")

for p in targets:
    s = p.read_text(encoding="utf-8")
    before = s.count('class="article-tags"')
    blocks = re.findall(r'<div class="article-tags">.*?</div>', s, flags=re.S)
    if before <= 1:
        print(f"  {p.name}: 已是 {before} 份，无需处理")
        continue
    keep = blocks[0]
    # 删掉全部，再在头部 tags 之后插回唯一一份
    s = re.sub(r'\s*<div class="article-tags">.*?</div>', '', s, flags=re.S)
    s = re.sub(r'(<div class="tags">.*?</div>)', lambda m: m.group(1) + "\n" + keep,
               s, count=1, flags=re.S)
    after = s.count('class="article-tags"')
    p.write_text(s, encoding="utf-8")
    print(f"  {p.name}: {before} 份 → {after} 份")
