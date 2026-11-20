# -*- coding: utf-8 -*-
"""素材库整理（可逆操作，不删任何文件）：
 1) 清洗：真名→阿凤姐、删 QQ/旧域名
 2) 隔离：陈皮题材移到「陈皮素材（不进茶叶站）」
 3) 去重：标题指纹相同的，保留最新一篇，其余移入「_重复待确认」
 4) 归档：2026-10 及更早 → 资料库/素材材料/归档-2026-10/
运行：python _clean_drafts.py            # 预览
      python _clean_drafts.py --apply    # 执行
"""
import re
import shutil
import sys
from pathlib import Path

BASE = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault\资料库\素材材料")
D = BASE / "茶叶素材"
CHENPI = BASE / "陈皮素材（不进茶叶站）"
DUPS = BASE / "_重复待确认"
ARCHIVE = BASE / "归档-2026-10及更早"

APPLY = "--apply" in sys.argv
BAN = ("陈皮", "新会", "柑普", "小青柑", "柑皮")


def scrub(txt):
    txt = txt.replace("林玉凤（阿凤姐）", "阿凤姐").replace("林玉鳳（阿鳳姐）", "阿鳳姐")
    txt = txt.replace("林玉凤", "阿凤姐").replace("林玉鳳", "阿鳳姐")
    txt = re.sub(r"[ \t]*(?:💬\s*)?QQ\s*[：:]\s*107[-‑]?9790[-‑]?744", "", txt)
    txt = txt.replace("1079790744", "")
    for old in ("https://afeng-tea.vercel.app", "https://afengtea-2.vercel.app",
                "https://afengtea.vercel.app", "afeng-tea.vercel.app",
                "https://vocal-gaufre-8f51b7.netlify.app"):
        txt = txt.replace(old, "https://feng-tea.com")
    return txt


files = sorted(D.glob("*.md"))
print(f"素材总数: {len(files)}\n")

plan = {"scrub": [], "chenpi": [], "dup": [], "archive": []}
title_map = {}

for p in files:
    txt = p.read_text(encoding="utf-8", errors="replace")

    # 陈皮 → 隔离
    head = txt[:400]
    if any(k in p.name for k in BAN) or any(k in head for k in BAN):
        plan["chenpi"].append(p)
        continue

    # 清洗
    if txt != scrub(txt):
        plan["scrub"].append(p)

    # 归档（2026-10 及更早）
    m = re.match(r"(\d{4}-\d{2})", p.name)
    if m and m.group(1) <= "2026-10":
        plan["archive"].append(p)
        continue

    # 去重（只看 11 月保留区）
    t = re.search(r"^# (.+)$", txt, re.M)
    if t:
        fp = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]", "", t.group(1))[:10]
        if fp:
            title_map.setdefault(fp, []).append(p)

for fp, group in title_map.items():
    if len(group) > 1:
        group.sort(key=lambda x: x.name)     # 日期在前，保留最新的
        for p in group[:-1]:
            plan["dup"].append(p)

print("=== 处理计划 ===")
print(f"  清洗真名/QQ: {len(plan['scrub'])} 篇")
print(f"  陈皮隔离:    {len(plan['chenpi'])} 篇")
print(f"  重复副本:    {len(plan['dup'])} 篇 → 移到 _重复待确认")
print(f"  归档 2026-10 及更早: {len(plan['archive'])} 篇")
kept = len(files) - len(plan["chenpi"]) - len(plan["dup"]) - len(plan["archive"])
print(f"\n  处理后素材库剩余（11 月）：约 {kept} 篇")

if not APPLY:
    print("\n（预览模式。加 --apply 执行；所有操作是【移动】或【改文本】，不删除）")
    sys.exit(0)

# ===== 执行 =====
print("\n=== 执行中 ===")
for d in (CHENPI, DUPS, ARCHIVE):
    d.mkdir(parents=True, exist_ok=True)

n = 0
for p in plan["scrub"]:
    txt = p.read_text(encoding="utf-8", errors="replace")
    p.write_text(scrub(txt), encoding="utf-8")
    n += 1
print(f"  ✓ 清洗 {n} 篇")

for p in plan["chenpi"]:
    shutil.move(str(p), str(CHENPI / p.name))
print(f"  ✓ 陈皮隔离 {len(plan['chenpi'])} 篇")

for p in plan["dup"]:
    shutil.move(str(p), str(DUPS / p.name))
print(f"  ✓ 重复副本移出 {len(plan['dup'])} 篇")

for p in plan["archive"]:
    shutil.move(str(p), str(ARCHIVE / p.name))
print(f"  ✓ 归档 {len(plan['archive'])} 篇")

left = sorted(D.glob("*.md"))
print(f"\n=== 处理后 ===")
print(f"  茶叶素材库现存: {len(left)} 篇")
still = sum(1 for p in left if "林玉凤" in p.read_text(encoding='utf-8', errors='replace'))
print(f"  真名残留: {still} 篇（应为 0）")
print(f"  陈皮残留: {sum(1 for p in left if any(k in p.name for k in BAN))} 篇（应为 0）")
