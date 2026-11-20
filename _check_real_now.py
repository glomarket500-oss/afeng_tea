# -*- coding: utf-8 -*-
"""检查：阿凤姐实拍图库现在还能不能取到图（图片文件夹是否还在）"""
import sys
from pathlib import Path

sys.path.insert(0, r"C:\afeng_tea")
import real_photos as RP

src = RP.SRC
print(f"实拍目录: {src}")
files = list(src.glob("*.*")) if src.exists() else []
print(f"  目录存在: {src.exists()}  文件数: {len(files)}")

man = RP.load_manifest() if hasattr(RP, "load_manifest") else {}
print(f"  标签清单条目: {len(man)}")

picked = RP.pick("紫砂壶 茶席", "紫砂壶 茶席 场景", need=3, want_person=True)
print(f"  实际能取到: {len(picked)} 张")
for m in picked:
    print("   ", m.get("file"), m.get("w"), "×", m.get("h"))
