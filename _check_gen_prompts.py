# -*- coding: utf-8 -*-
"""检查三个生成任务的 prompt：是否明确要求把草稿写进素材库、写到哪、投递到哪"""
import json
import re
from pathlib import Path

J = Path(r"C:\Users\Administrator\AppData\Local\hermes\cron\jobs.json")
data = json.loads(J.read_text(encoding="utf-8"))
jobs = data["jobs"] if isinstance(data, dict) and "jobs" in data else data

TARGETS = ["5ca6766a19a8", "29c356765d6d", "e07a2152c955"]   # 晨语茶事 / 做青篇 / 健康养生

for j in jobs:
    if j.get("id") not in TARGETS:
        continue
    p = j.get("prompt") or ""
    print("=" * 78)
    print(f"{j['name']}   [{j['id']}]")
    print(f"  模型: {j.get('model')} / {j.get('provider')}   定时: {j.get('schedule', {}).get('expr')}")
    print(f"  投递: {j.get('deliver')}")
    print(f"  prompt 长度: {len(p)} 字符")
    # 找与"存稿"相关的句子
    hits = [s.strip() for s in re.split(r"[。\n]", p)
            if re.search(r"write_file|保存|存档|素材|\.md|C:\\", s)]
    print("  ── 存稿相关指令 ──")
    if hits:
        for h in hits[:6]:
            print(f"    · {h[:150]}")
    else:
        print("    ⚠ 没找到任何存稿指令（可能只投飞书、不落盘）")
    # 是否有隐私/格式约束
    print(f"  ── 约束检查 ──")
    print(f"    模板结构(场景开头/四幕): {'有' if '场景开头' in p and '四幕' in p else '无'}")
    print(f"    隐私红线(不写手机号/QQ): {'有' if ('手机号' in p or 'QQ' in p) else '无'}")
    print(f"    标签要求(惠州茶叶店): {'有' if '惠州茶叶店' in p else '无'}")
