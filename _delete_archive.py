# -*- coding: utf-8 -*-
"""删除 2026-10 及更早的归档老稿（从未发布过）。先校验再删。"""
import shutil
from pathlib import Path

P = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault\资料库\素材材料\归档-2026-10及更早")
LIMIT = 20 * 1024 * 1024      # 上限 20MB

if not P.exists():
    print("目录不存在，无需删除")
else:
    files = list(P.rglob("*"))
    sizes = [f.stat().st_size for f in files if f.is_file()]
    total = sum(sizes)
    print(f"待删目录: {P.name}")
    print(f"  文件数: {len(sizes)} 个")
    print(f"  总大小: {total/1024/1024:.2f} MB")
    print(f"  日期范围: {min(f.name for f in files if f.is_file())[:10]} ~ {max(f.name for f in files if f.is_file())[:10]}")
    if total > LIMIT:
        print(f"  ⛔ 超过 {LIMIT/1024/1024:.0f}MB 阈值，中止")
    else:
        shutil.rmtree(P)
        print(f"  ✓ 已删除")

V = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault")
S = V / "资料库" / "素材材料"
print("\n=== 素材材料目录现状 ===")
for d in sorted(S.iterdir()):
    if d.is_dir():
        print(f"  {d.name}: {len(list(d.glob('*.md')))} 篇")
print(f"\n茶叶素材库: {len(list((S/'茶叶素材').glob('*.md')))} 篇")
print(f"知识库笔记: {len(list((V/'茶叶知识库').glob('*.md')))} 篇")
