# -*- coding: utf-8 -*-
"""补洗：迁移后合并进来的旧稿里残留的真名/QQ"""
import re
from pathlib import Path

D = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault\资料库\素材材料\茶叶素材")


def scrub(txt):
    txt = txt.replace("林玉凤（阿凤姐）", "阿凤姐").replace("林玉鳳（阿鳳姐）", "阿鳳姐")
    txt = txt.replace("林玉凤", "阿凤姐").replace("林玉鳳", "阿鳳姐")
    txt = re.sub(r"[ \t]*(?:💬\s*)?QQ\s*[：:]\s*107[-‑]?9790[-‑]?744", "", txt)
    return txt.replace("1079790744", "")


n = 0
for p in sorted(D.glob("*.md")):
    txt = p.read_text(encoding="utf-8", errors="replace")
    new = scrub(txt)
    if new != txt:
        p.write_text(new, encoding="utf-8")
        n += 1
        print(f"  ✓ {p.name}")

print(f"\n补洗 {n} 篇")
left = [p.name for p in D.glob("*.md") if "林玉凤" in p.read_text(encoding="utf-8", errors="replace")]
print(f"真名残留: {len(left)} 篇")
for x in left:
    print(f"  ⚠ {x}")
