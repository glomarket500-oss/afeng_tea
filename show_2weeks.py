#!/usr/bin/env python3
"""从 audit_report.json 提取两周内文章的评分明细"""
import json
from pathlib import Path

BASE = Path(__file__).parent
d = json.load(open(BASE / "audit_report.json", encoding="utf-8"))
rows = [r for r in d if r["filename"].startswith(("2026111", "2026112"))]
rows.sort(key=lambda r: (-r["total_score"], r["filename"]))
for r in rows:
    print(f"{r['status']:>5} | {r['total_score']:>5.1f} | {r['filename']}")
print()
print("两周内文章数:", len(rows))
ok = sum(1 for r in rows if r["status"] == "合格")
warn = sum(1 for r in rows if r["status"] == "建议修复")
bad = sum(1 for r in rows if r["status"] == "不合格")
print(f"合格 {ok} / 建议修复 {warn} / 不合格 {bad}")
print()
print("=== 不合格文章的问题明细 ===")
for r in rows:
    if r["status"] in ("不合格", "建议修复"):
        print(f"\n[{r['total_score']:.1f}] {r['filename']}")
        for iss in r.get("issues", []):
            print(f"   - {iss}")
