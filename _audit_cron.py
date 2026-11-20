# -*- coding: utf-8 -*-
"""cron 任务重复度审计：按触发时刻 + 主题家族 找重叠，估算每日 LLM 调用量"""
import json
import re
import collections
from pathlib import Path

JOBS = Path(r"C:\Users\Administrator\AppData\Local\hermes\cron\jobs.json")
data = json.loads(JOBS.read_text(encoding="utf-8"))
jobs = data["jobs"] if isinstance(data, dict) and "jobs" in data else data

rows = []
for j in jobs:
    sch = j.get("schedule") or {}
    expr = sch.get("expr") or ""
    disp = sch.get("display") or j.get("schedule_display") or ""
    m = re.match(r"^(\d+)\s+(\d+)\s", expr) or re.match(r"^(\d+)\s+(\d+)\s+", expr)
    if m:
        hhmm = f"{int(m.group(2)):02d}:{int(m.group(1)):02d}"
        daily = expr.split()[2] == "*" if len(expr.split()) > 2 else True
    else:
        hhmm = disp if "every" not in disp else "每周: " + disp
        rc = j.get("repeat") or {}
        daily = False
    if isinstance(j.get("repeat"), dict) and j["repeat"].get("times") is not None:
        daily = True
    prov = j.get("provider") or ""
    rows.append({
        "id": j.get("id"), "name": j.get("name"), "at": hhmm,
        "enabled": j.get("enabled"), "model": j.get("model"),
        "paid": "deepseek" in str(prov).lower() or "deepseek" in str(j.get("model")).lower(),
        "deliver": (j.get("deliver") or "")[:26],
        "no_agent": j.get("no_agent"), "daily": daily,
        "status": j.get("last_status"),
    })

print(f"任务总数: {len(rows)}  启用: {sum(1 for r in rows if r['enabled'])}")
print(f"走 LLM 的: {sum(1 for r in rows if not r['no_agent'])}  纯脚本: {sum(1 for r in rows if r['no_agent'])}")
print(f"付费模型(deepseek)任务: {sum(1 for r in rows if r['paid'] and not r['no_agent'])}\n")

# 同一时刻撞车
by_time = collections.defaultdict(list)
for r in rows:
    if r["enabled"]:
        by_time[r["at"]].append(r)

print("=" * 74)
print("同一时刻触发的任务（>=2 个 = 撞车）")
print("=" * 74)
for t in sorted(by_time, key=lambda x: (len(x), x)):
    grp = by_time[t]
    if len(grp) < 2:
        continue
    print(f"\n【{t}】{len(grp)} 个任务：")
    for r in grp:
        tag = "脚本" if r["no_agent"] else ("付费LLM" if r["paid"] else "LLM")
        print(f"   - {r['name'][:26]:28s} {tag:6s} {r['id']}")

# 主题家族
FAM = {
    "茶叶系列": r"^茶叶-\d",
    "凤凰单丛系列": r"^凤凰单丛-\d",
    "化妆品系列": r"^(化妆品|化妆品香水)-",
    "提醒类": r"(提醒|报时|天气预报|起床|早餐|午饭|晚饭|下午茶知识)",
    "周评": r"周评|每周",
}
print("\n" + "=" * 74)
print("按主题家族统计（每日 LLM 调用量 = 直接的钱）")
print("=" * 74)
tot = 0
for fam, pat in FAM.items():
    mem = [r for r in rows if re.match(pat, r["name"] or "") and r["enabled"]]
    llm = [r for r in mem if not r["no_agent"]]
    daily_n = sum(1 for r in llm if r["daily"])
    tot += daily_n
    print(f"  {fam:10s} 共 {len(mem):2d} 个，走LLM {len(llm):2d} 个，其中每日触发 {daily_n:2d} 次")
print(f"\n  → 每日仅这几族就产生约 {tot} 次 LLM 任务调用")

others = [r for r in rows if not any(re.match(p, r["name"] or "") for p in FAM.values())]
if others:
    print("\n  未归类的任务：")
    for r in others:
        print(f"   - {r['name'][:30]:32s} {r['at']}  {r['id']}")
