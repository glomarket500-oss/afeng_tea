# -*- coding: utf-8 -*-
"""审计启用中 cron 任务的最近执行情况"""
import json
from pathlib import Path

J = Path(r"C:\Users\Administrator\AppData\Local\hermes\cron\jobs.json")
data = json.loads(J.read_text(encoding="utf-8"))
jobs = data["jobs"] if isinstance(data, dict) and "jobs" in data else data

rows = [j for j in jobs if j.get("enabled")]
print(f"启用中任务: {len(rows)} 个（暂停 {len(jobs) - len(rows)} 个）\n")

print(f"{'时间':16s} {'任务':24s} {'类型':6s} {'上次执行':17s} {'状态':10s} 错误")
print("-" * 108)
for j in sorted(rows, key=lambda x: str((x.get("schedule") or {}).get("expr", ""))):
    expr = (j.get("schedule") or {}).get("expr") or ""
    kind = "脚本" if j.get("no_agent") else "LLM"
    lr = (j.get("last_run_at") or "从未")[:16].replace("T", " ")
    st = j.get("last_status") or "-"
    err = (j.get("last_error") or j.get("last_delivery_error") or "")
    err = err.replace("\n", " ")[:44]
    print(f"{expr:16s} {j['name'][:24]:24s} {kind:6s} {lr:17s} {st:10s} {err}")

print("\n=== 异常的（有错误 或 状态不是 ok）===")
bad = [j for j in rows if (j.get("last_status") not in (None, "ok")) or j.get("last_error") or j.get("last_delivery_error")]
for j in bad:
    print(f"  ✗ {j['name']}")
    print(f"      status={j.get('last_status')}  last_run={j.get('last_run_at')}")
    e = (j.get("last_error") or "")[:200]
    d = (j.get("last_delivery_error") or "")[:200]
    if e:
        print(f"      error: {e}")
    if d:
        print(f"      deliver: {d}")
if not bad:
    print("  （无）")
