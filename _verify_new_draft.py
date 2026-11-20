# -*- coding: utf-8 -*-
"""验收刚生成的草稿：是否落盘、结构是否合规、隐私与题材是否干净"""
import re
from pathlib import Path
from datetime import datetime

D = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault\资料库\素材材料\茶叶素材")
files = sorted(D.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
print(f"素材库现有 {len(files)} 篇\n")

newest = files[0]
age_min = (datetime.now().timestamp() - newest.stat().st_mtime) / 60
print(f"最新一篇: {newest.name}")
print(f"  修改时间: {datetime.fromtimestamp(newest.stat().st_mtime):%Y-%m-%d %H:%M:%S}（{age_min:.0f} 分钟前）")
print(f"  大小: {newest.stat().st_size} 字节")

txt = newest.read_text(encoding="utf-8", errors="replace")
zh = len(re.findall(r"[\u4e00-\u9fa5]", txt))
print(f"  中文字数: {zh}")

print("\n=== 结构检查 ===")
checks = {
    "有标题(# )": bool(re.search(r"^# ", txt, re.M)),
    "场景开头": "场景开头" in txt,
    "四幕齐全": all(f"第{n}幕" in txt for n in "一二三四"),
    "尾声": "尾声" in txt,
    "FAQ": "FAQ" in txt or "Q：" in txt,
    "标签": "#" in txt,
    "联系方式/地址": ("地址" in txt) or ("沿江商铺" in txt) or ("惠州" in txt),
}
for k, v in checks.items():
    print(f"  {'✓' if v else '✗'} {k}")

print("\n=== 红线检查 ===")
red = {
    "真名林玉凤残留": "林玉凤" in txt,
    "QQ 号残留": "1079790744" in txt,
    "手机号残留": bool(re.search(r"13435567385", txt)),
    "陈皮题材（本站禁止）": any(k in newest.name or k in txt[:200] for k in ("陈皮", "新会", "柑普", "小青柑")),
}
for k, v in red.items():
    print(f"  {'⚠ 有' if v else '✓ 无'} {k}")

print("\n=== 前 300 字预览 ===")
print(txt[:300].replace("\n", " "))
