# -*- coding: utf-8 -*-
"""新增「任务卡死看门狗」定时任务：每 15 分钟一次，零 LLM
照抄已经在稳定运行的「飞书投递补发」任务结构（no_agent + script + deliver local）
"""
import json
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

J = Path(r"C:\Users\Administrator\AppData\Local\hermes\cron\jobs.json")
BAK = J.with_suffix(J.suffix + ".bak_20261117_watchdog")
shutil.copy2(J, BAK)
print(f"✓ 备份: {BAK.name}")

data = json.loads(J.read_text(encoding="utf-8"))
jobs = data["jobs"] if isinstance(data, dict) and "jobs" in data else data

# 已有就不重复建
for j in jobs:
    if j.get("script") == "afeng_watchdog.py":
        print(f"已存在: {j.get('name')} ({j.get('id')})，不重复创建")
        raise SystemExit(0)

# 找补发任务当模板
tpl = next((j for j in jobs if j.get("script") == "afeng_redeliver.py"), None)
if not tpl:
    print("✗ 找不到模板任务 afeng_redeliver.py")
    raise SystemExit(1)

new_id = uuid.uuid4().hex[:12]
now = datetime.now(timezone(timedelta(hours=8)))
job = {
    "id": new_id,
    "name": "任务卡死看门狗（零成本）",
    "prompt": "（脚本任务，无需 prompt）",
    "schedule": {"kind": "interval", "minutes": 15, "display": "every 15m"},
    "schedule_display": "every 15m",
    "script": "afeng_watchdog.py",
    "no_agent": True,
    "deliver": "local",
    "enabled": True,
    "state": "scheduled",
    "repeat": "forever",
    "model": None,
    "provider": None,
    "base_url": None,
    "pinned": False,
    "next_run_at": (now + timedelta(minutes=15)).isoformat(),
    "created_at": now.isoformat(),
}

jobs.append(job)
J.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# 验证
data2 = json.loads(J.read_text(encoding="utf-8"))
jobs2 = data2["jobs"] if isinstance(data2, dict) and "jobs" in data2 else data2
found = [j for j in jobs2 if j.get("id") == new_id]
print(f"\n✓ 已创建: {job['name']}  id={new_id}")
print(f"  调度: {job['schedule']['display']} ｜ script={job['script']} ｜ no_agent={job['no_agent']} ｜ deliver={job['deliver']}")
print(f"  任务总数: {len(jobs2)} ｜ 启用: {len([j for j in jobs2 if j.get('enabled')])}")
print(f"  验证: {'✓ 已写入' if found else '✗ 未找到'}")
