# -*- coding: utf-8 -*-
"""诊断 cron/jobs.json 的 JSON 损坏位置"""
import json
from pathlib import Path

P = Path(r"C:\Users\Administrator\AppData\Local\hermes\cron\jobs.json")
raw = P.read_text(encoding="utf-8")
print(f"文件大小: {len(raw)} 字符 / {len(raw.splitlines())} 行")

# 定位错误
try:
    json.loads(raw)
    print("✓ JSON 合法，无需修复")
except json.JSONDecodeError as e:
    print(f"✗ 解析失败: {e.msg}  行 {e.lineno} 列 {e.colno} (char {e.pos})")
    start = max(0, e.pos - 160)
    end = min(len(raw), e.pos + 160)
    print("\n--- 出错位置上下文 ---")
    print(repr(raw[start:end]))
    print("\n--- 可读形式 ---")
    print(raw[start:end].replace("\\", "\\\\"))

# 统计可疑转义
import re
bad = list(re.finditer(r'\\(?!["\\/bfnrtu])', raw))
print(f"\n非法转义 \\X 出现 {len(bad)} 处")
for m in bad[:10]:
    seg = raw[max(0, m.start()-60):m.start()+40]
    print(f"  char {m.start()}: ...{seg}...")
