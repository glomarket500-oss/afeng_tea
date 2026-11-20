# -*- coding: utf-8 -*-
"""把付费 LLM 任务挪进闲时窗口（00:30–08:30），省钱。
顺带把会落在凌晨的任务改为 deliver=local，避免半夜给站方推消息——
稿子照样进素材库，第二天 09:00 的发布报告会告诉站方发了什么。
按 cron-jobs-bulk-admin 技能：备份 → 改 → 验证
"""
import json
import shutil
from pathlib import Path

J = Path(r"C:\Users\Administrator\AppData\Local\hermes\cron\jobs.json")
BAK = J.with_suffix(J.suffix + ".bak_20261117_offpeak")
shutil.copy2(J, BAK)
print(f"备份: {BAK.name}\n")

# id -> (新cron表达式, 新显示名, deliver 设为 local 吗)
CHANGES = {
    "29c356765d6d": ("0 4 * * *",      "0 4 * * *",     True),   # 凤凰单丛-04做青篇：10:00 → 04:00
    "e07a2152c955": ("30 5 * * *",     "30 5 * * *",    True),   # 茶叶-19健康养生：19:00 → 05:30
    "45fe935fe1b9": ("0 2 * * 0",      "every sunday 02:00", True),  # 周评写稿：周日20:00 → 周日02:00
}

data = json.loads(J.read_text(encoding="utf-8"))
jobs = data["jobs"] if isinstance(data, dict) and "jobs" in data else data

for j in jobs:
    jid = j.get("id")
    if jid not in CHANGES:
        continue
    expr, display, local = CHANGES[jid]
    old = (j.get("schedule") or {}).get("expr")
    j["schedule"] = {"kind": "cron", "expr": expr, "display": display}
    j["schedule_display"] = display
    if local:
        j["deliver"] = "local"
    print(f"  {j['name']}")
    print(f"     时间: {old} → {expr}")
    print(f"     投递: {'改为 local（不半夜推消息）' if local else '不变'}")

J.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# 验证
data2 = json.loads(J.read_text(encoding="utf-8"))
jobs2 = data2["jobs"] if isinstance(data2, dict) and "jobs" in data2 else data2
print("\n=== 验证：所有付费 LLM 任务的时间与投递 ===")
for j in jobs2:
    if not j.get("enabled") or j.get("no_agent"):
        continue
    expr = (j.get("schedule") or {}).get("expr", "")
    hour = int(expr.split()[1]) if len(expr.split()) > 1 else -1
    in_offpeak = (hour >= 1 and hour < 8) or (hour == 0 and int(expr.split()[0]) >= 30)
    print(f"  {'✓闲时' if in_offpeak else '✗峰时'} {expr:14s} {j['name'][:22]:24s} deliver={str(j.get('deliver'))[:22]}")
