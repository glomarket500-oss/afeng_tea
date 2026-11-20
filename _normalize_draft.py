# -*- coding: utf-8 -*-
"""草稿规范化器：把任意生成任务产出的 md 修成流水线能解析的格式
处理四类问题：
 1) 真名 林玉凤/林玉鳳 → 阿凤姐
 2) **第X幕·xxx** / **尾声** → ## 【第X幕：xxx】 / ## 【尾声】
 3) 缺 ## 【场景开头】 → 在标题后第一段前补上
 4) 🏷️ #a #b 行 → ## 标签 + 标签行
用法: python _normalize_draft.py <草稿.md> [--inplace]
不加 --inplace 只预览不改。
"""
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
inplace = "--inplace" in sys.argv
src = path.read_text(encoding="utf-8")
txt = src
log = []

# 1) 真名
n = txt.count("林玉凤") + txt.count("林玉鳳")
if n:
    txt = txt.replace("林玉凤（阿凤姐）", "阿凤姐").replace("林玉鳳（阿鳳姐）", "阿鳳姐")
    txt = txt.replace("林玉凤", "阿凤姐").replace("林玉鳳", "阿鳳姐")
    log.append(f"真名替换 {n} 处")

# 2) 幕标记：**第一幕·xxx** / **第一幕: xxx** / **尾声**
def fix_act(m):
    label = m.group(1).strip()
    rest = m.group(2).strip(" ·:：—-")
    label = re.sub(r"第([一二三四五六七八九十])幕", r"第\1幕", label)
    return f"## 【{label}：{rest}】" if rest else f"## 【{label}】"

before = txt
txt = re.sub(r"^\*\*\s*(第[一二三四五六七八九十]幕|场景开头|尾声)\s*[·:：—\-]?\s*([^*]*?)\s*\*\*\s*$",
             fix_act, txt, flags=re.M)
if txt != before:
    log.append("幕标记已转为 ## 【…】 格式")

# 3) 场景开头（若没有）
if "【场景开头】" not in txt:
    lines = txt.split("\n")
    idx = None
    for i, l in enumerate(lines):
        s = l.strip()
        if i == 0 or not s or s.startswith("#"):
            continue
        if s.startswith("##"):
            continue
        idx = i
        break
    if idx is not None:
        lines.insert(idx, "## 【场景开头】\n")
        txt = "\n".join(lines)
        log.append(f"补上【场景开头】（插在第 {idx+1} 行前）")

# 4) 标签行
m = re.search(r"^[^\n#]*🏷️?\s*((?:#[^\s#]+[ \t]*)+)$", txt, flags=re.M)
if m and "## 标签" not in txt:
    tagline = m.group(1).strip()
    txt = txt[:m.start()] + f"## 标签\n{tagline}" + txt[m.end():]
    log.append("标签行改为 ## 标签 段落")

if not log:
    print("无需修改，格式已合规")
    sys.exit(0)

print("将做的修改：")
for l in log:
    print(f"  · {l}")

if inplace:
    path.write_text(txt, encoding="utf-8")
    print(f"\n✓ 已写入 {path.name}（{len(src)} → {len(txt)} 字符）")
else:
    print("\n（预览模式，未写入。加 --inplace 生效）")
