# -*- coding: utf-8 -*-
"""删除无用目录（带前置校验，防止误删）：
1) C:\\Users\\a           —— 4 个临时 py + 空目录，23K
2) _重复待确认            —— 3 篇旧版本重复稿（正版都在库里）
校验不通过就中止，不删。
"""
import shutil
from pathlib import Path

TARGETS = [
    (Path(r"C:\Users\a"), 200 * 1024, "4 个临时脚本，无有用文件"),
    (Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault\资料库\素材材料\_重复待确认"),
     500 * 1024, "3 篇旧版重复稿"),
]

def size_of(p):
    if p.is_file():
        return p.stat().st_size
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())

for path, limit, why in TARGETS:
    print(f"\n=== {path} ===")
    if not path.exists():
        print("  已不存在，跳过")
        continue
    files = [f for f in path.rglob("*") if f.is_file()] if path.is_dir() else [path]
    total = size_of(path)
    print(f"  预期: {why}")
    print(f"  实际: {len(files)} 个文件 / {total/1024:.1f} KB")
    if total > limit:
        print(f"  ⛔ 超过安全阈值 {limit/1024:.0f} KB，中止不删")
        continue
    for f in files[:8]:
        print(f"    · {f.relative_to(path)}")
    try:
        shutil.rmtree(path) if path.is_dir() else path.unlink()
        print(f"  ✓ 已删除")
    except Exception as e:
        print(f"  ✗ 删除失败: {e}")

print("\n=== 结果确认 ===")
for path, _, _ in TARGETS:
    print(f"  {'❌ 仍存在' if path.exists() else '✓ 已清除'}  {path}")

V = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault")
kb = V / "资料库" / "素材材料" / "茶叶素材"
print(f"\n知识库完好性: 笔记 {len(list((V/'茶叶知识库').glob('*.md')))} 篇 / 素材 {len(list(kb.glob('*.md')))} 篇")
