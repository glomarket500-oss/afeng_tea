# -*- coding: utf-8 -*-
r"""修复 cron/jobs.json 的非法转义（单反斜杠路径导致 \U \A \D 等非法序列）
原理：从左到右扫描，遇到 \ 时判断下一个字符是否属于 JSON 合法转义
      （" \ / b f n r t u）——不是就补一个 \ 变成 \\ 。
写回后立即 json.loads 验证，再统计任务数。
"""
import json
import shutil
from pathlib import Path

P = Path(r"C:\Users\Administrator\AppData\Local\hermes\cron\jobs.json")
BAK = P.with_suffix(".json.bak_corrupt_20261117")
shutil.copy2(P, BAK)
print(f"✓ 已备份损坏文件: {BAK.name}")

raw = P.read_text(encoding="utf-8")
VALID = set('"\\/bfnrtu')

out = []
i = 0
fixed = 0
while i < len(raw):
    ch = raw[i]
    if ch == "\\":
        nxt = raw[i + 1] if i + 1 < len(raw) else ""
        if nxt in VALID:
            # 合法转义：原样保留（\u 还要带上 4 位十六进制，交给 json 自己校验）
            out.append(ch)
            out.append(nxt)
            i += 2
            continue
        # 非法转义：补一个反斜杠，让 \X 变成 \\X
        out.append("\\\\")
        fixed += 1
        i += 1
        continue
    out.append(ch)
    i += 1

new = "".join(out)
print(f"修正非法转义: {fixed} 处")

# 验证
try:
    data = json.loads(new)
    print("✓ 修复后 JSON 合法")
except json.JSONDecodeError as e:
    print(f"✗ 仍然失败: {e.msg} 行{e.lineno}列{e.colno}")
    # 打印位置供进一步判断
    print(repr(new[max(0, e.pos-80):e.pos+80]))
    raise SystemExit(1)

# 原子写回
tmp = P.with_suffix(".json.repairing")
tmp.write_text(new, encoding="utf-8")
tmp.replace(P)
print(f"✓ 已写回 ({len(raw)} → {len(new)} 字符)")

# 统计
data2 = json.loads(P.read_text(encoding="utf-8"))
jobs = data2.get("jobs", data2) if isinstance(data2, dict) else data2
on = [j for j in jobs if j.get("enabled")]
print(f"\n任务总数 {len(jobs)} 个 / 启用 {len(on)} 个")
for j in on:
    print(f"  {(j.get('schedule') or {}).get('expr','?'):14s} {j['name'][:26]}")

# 抽查路径是否还原正确
sample = None
for j in jobs:
    p = j.get("prompt") or ""
    if "MianAI" in p:
        import re
        m = re.search(r"[A-Za-z]:[^\s，。]*MianAI[^\s，。]*", p)
        if m:
            sample = m.group(0)
            break
print(f"\n路径抽查: {sample}")
