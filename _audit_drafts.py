# -*- coding: utf-8 -*-
"""素材库体检：按月/去重/质量/合规四维分析，给出处理建议（只读，不动文件）"""
import re
import collections
from pathlib import Path

D = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault\资料库\素材材料\茶叶素材")
files = sorted(D.glob("*.md"))
print(f"素材总数: {len(files)}\n")

by_month = collections.Counter()
by_day = collections.Counter()
title_key = collections.defaultdict(list)
quality = {"短(<600字)": 0, "正常(600-1500)": 0, "长(>1500)": 0}
issues = collections.Counter()
sizes = []

for p in files:
    name = p.name
    m = re.match(r"(\d{4}-\d{2})-(\d{2})", name)
    if m:
        by_month[m.group(1)] += 1
        by_day[f"{m.group(1)}-{m.group(2)}"] += 1
    else:
        by_month["无日期"] += 1
        issues["文件名无日期前缀"] += 1

    try:
        txt = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        issues["读取失败"] += 1
        continue

    zh = len(re.findall(r"[\u4e00-\u9fa5]", txt))
    sizes.append(zh)
    if zh < 600:
        quality["短(<600字)"] += 1
    elif zh > 1500:
        quality["长(>1500)"] += 1
    else:
        quality["正常(600-1500)"] += 1

    # 质量问题
    if "林玉凤" in txt or "林玉鳳" in txt:
        issues["含真名林玉凤"] += 1
    if "1079790744" in txt:
        issues["含QQ号"] += 1
    if "陈皮" in txt[:300] or "新会" in txt[:300]:
        issues["陈皮题材"] += 1
    if not re.search(r"^# ", txt, re.M):
        issues["无标题"] += 1

    # 标题指纹（去重）
    t = re.search(r"^# (.+)$", txt, re.M)
    if t:
        fp = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]", "", t.group(1))[:10]
        if fp:
            title_key[fp].append(name)

print("=== 按月分布 ===")
for k, v in sorted(by_month.items()):
    print(f"  {k}: {v} 篇")

print("\n=== 日产量 Top8（说明生成任务有多集中）===")
for k, v in by_day.most_common(8):
    print(f"  {k}: {v} 篇")

print("\n=== 篇幅分布 ===")
for k, v in quality.items():
    print(f"  {k}: {v} 篇")
if sizes:
    sizes.sort()
    print(f"  中位字数: {sizes[len(sizes)//2]} ｜ 最短 {sizes[0]} ｜ 最长 {sizes[-1]}")

print("\n=== 质量问题 ===")
if issues:
    for k, v in issues.most_common():
        print(f"  ⚠ {k}: {v} 篇")
else:
    print("  （无）")

dups = {k: v for k, v in title_key.items() if len(v) > 1}
dup_total = sum(len(v) - 1 for v in dups.values())
print(f"\n=== 标题重复 ===")
print(f"  重复标题组: {len(dups)} 组，多余副本 {dup_total} 篇")
for k, v in list(dups.items())[:6]:
    print(f"  · {k}… → {len(v)} 篇")
    for n in v[:3]:
        print(f"      {n}")
