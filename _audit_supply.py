# -*- coding: utf-8 -*-
"""素材库供需审计：每天产出多少草稿 vs 每天消耗多少（发布）"""
import collections
import json
import re
from pathlib import Path

DRAFTS = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault\资料库\素材材料\茶叶素材")
STATE = Path(r"C:\afeng_tea\.published_drafts.json")

if not DRAFTS.exists():
    print(f"❌ 素材目录不存在: {DRAFTS}")
    raise SystemExit(1)

files = sorted(DRAFTS.glob("*.md"))
print(f"素材库路径: {DRAFTS}")
print(f"草稿总数: {len(files)}\n")

by_date = collections.Counter()
for p in files:
    m = re.match(r"(\d{4}-\d{2}-\d{2})", p.name)
    by_date[m.group(1) if m else "未标日期"] += 1

print("=== 最近 12 天每日产出 ===")
for d in sorted(by_date)[-12:]:
    print(f"  {d}  {by_date[d]:2d} 篇  {'█' * min(by_date[d], 40)}")

st = {}
if STATE.exists():
    try:
        st = json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        pass
print(f"\n=== 已发布登记 ===")
print(f"  .published_drafts.json 记录: {len(st)} 篇")
print(f"  按最新统计，未发布残留: {len(files) - len(st)} 篇")

recent = [p for p in files if re.match(r"2026-11-1[0-9]", p.name)]
print(f"\n  11月10日以来新增: {len(recent)} 篇")
days = len({re.match(r'(\d{4}-\d{2}-\d{2})', p.name).group(1) for p in recent if re.match(r'(\d{4}-\d{2}-\d{2})', p.name)})
if days:
    print(f"  日均产出约: {len(recent) / days:.1f} 篇/天   而发布能力: 1 篇/天")
    print(f"  → 积压增速约 {len(recent) / days - 1:.1f} 篇/天")
