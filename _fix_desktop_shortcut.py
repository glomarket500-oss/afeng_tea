# -*- coding: utf-8 -*-
"""整理桌面 Obsidian 快捷方式：删重复项 + 改成正常名字（不用 emoji）"""
from pathlib import Path

D = Path(r"C:\Users\Administrator\Desktop")

dup = D / "📔 Obsidian(茶叶知识库).lnk"      # 我手动复制的（emoji 显示成方框）
main = D / "Obsidian.lnk"                     # 安装程序自建的
new = D / "Obsidian 茶叶知识库.lnk"

print("=== 处理前 ===")
for p in sorted(D.glob("*Obsidian*.lnk")):
    print(f"  {p.name}  ({p.stat().st_size} 字节)")

if dup.exists():
    dup.unlink()
    print(f"\n✓ 已删除重复项: {dup.name}")

if main.exists() and not new.exists():
    main.rename(new)
    print(f"✓ 已改名: Obsidian.lnk → {new.name}")

print("\n=== 处理后 ===")
found = sorted(D.glob("*Obsidian*.lnk"))
for p in found:
    print(f"  {p.name}  ({p.stat().st_size} 字节)")
print(f"\n现在桌面只剩 {len(found)} 个 Obsidian 快捷方式")
