#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补生成某篇缺的配图（复用固定 prefix，不重建页面、不提交）
用法: python _gen_missing_images.py <draft.md> <prefix> <slug>
已修：底部15%去水印 + 429退避 + 7张缺一即中止
"""
import sys
from pathlib import Path

sys.path.insert(0, r"C:\afeng_tea")
import publish_new as P

draft, prefix, slug = sys.argv[1], sys.argv[2], sys.argv[3]
raw = P.scrub(Path(draft).read_text(encoding="utf-8"))
title, lead, sections, faq, tags, preview = P.parse_draft(raw)
print(f"标题: {title}")
print(f"幕数: {len(sections)}  标签: {len(tags)}  FAQ: {len(faq)}")
print("--- 开始生图 ---")

prompts, dims, audit = P.make_images(prefix, title, sections, slug)
print("\n--- 结果 ---")
for p in prompts:
    fp = Path(r"C:\afeng_tea\images\full") / f"{prefix}-{p['key']}.webp"
    print(f"  {p['key']:6s} {'✓' if fp.exists() else '✗ 缺失'}  {dims.get(p['key'])}")
print(f"audit_log: {audit if audit else '全部合规'}")
