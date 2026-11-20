# -*- coding: utf-8 -*-
"""把 8 个生活提醒/茶语任务改为 no_agent 脚本直跑（零 LLM 费用）
按 cron-jobs-bulk-admin 技能：备份 → 改 → 三项验证
"""
import json
import shutil
from pathlib import Path

J = Path(r"C:\Users\Administrator\AppData\Local\hermes\cron\jobs.json")
BAK = J.with_suffix(J.suffix + ".bak_20261116_reminder2script")
shutil.copy2(J, BAK)
print(f"备份: {BAK.name}")

SCRIPT = "afeng_reminder.py"
TARGETS = {
    "479296f685fa": "起床提醒-5点",
    "42c8635b3976": "早间报时-6点",
    "71c1e2ad40a4": "天气预报-7点",
    "94f0901fdac0": "茶叶资讯-8点",
    "1c3e7010f1df": "早餐提醒-10点",
    "be8884a73505": "午饭提醒-11点",
    "f4e0a7ca681a": "下午茶知识-15点",
    "792591c45d07": "晚饭提醒-17点",
}

data = json.loads(J.read_text(encoding="utf-8"))
jobs = data["jobs"] if isinstance(data, dict) and "jobs" in data else data

hit, miss = [], []
for j in jobs:
    jid = j.get("id")
    if jid not in TARGETS:
        continue
    j["no_agent"] = True
    j["script"] = SCRIPT
    j["model"] = None
    j["provider"] = None
    j["base_url"] = None
    j["prompt"] = (f"零 LLM：调度器直跑 {SCRIPT}，按时段输出提醒/天气/茶语。"
                   f"（原地址 {TARGETS[jid]}）")
    j["skills"] = []
    j["skill"] = None
    hit.append(TARGETS[jid])
for k, name in TARGETS.items():
    if not any(j.get("id") == k for j in jobs):
        miss.append(name)

J.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n已改为脚本直跑 {len(hit)} 个：")
for h in hit:
    print(f"  - {h}")
if miss:
    print(f"⚠ 未找到: {miss}")

# ===== 验证 =====
data2 = json.loads(J.read_text(encoding="utf-8"))
jobs2 = data2["jobs"] if isinstance(data2, dict) and "jobs" in data2 else data2
bad = [j["name"] for j in jobs2 if j.get("id") in TARGETS
       and not (j.get("no_agent") and j.get("script") == SCRIPT)]
print(f"\n=== 验证 1：字段 ===")
print(f"  应改 {len(TARGETS)}，已改 {sum(1 for j in jobs2 if j.get('id') in TARGETS and j.get('no_agent') and j.get('script') == SCRIPT)}")
print(f"  未生效（应为 0）: {bad}")

print(f"\n=== 验证 2：仍有残留 LLM 的（应为 0）===")
llm_left = [j["name"] for j in jobs2 if j.get("id") in TARGETS
            and j.get("enabled") and not j.get("no_agent")]
print(f"  {llm_left or '无'}")

en_llm = [j for j in jobs2 if j.get("enabled") and not j.get("no_agent")]
en_script = [j for j in jobs2 if j.get("enabled") and j.get("no_agent")]
print(f"\n=== 验证 3：全站配额 ===")
print(f"  启用中 LLM 任务: {len(en_llm)} 个")
for j in sorted(en_llm, key=lambda x: str(x.get("schedule", {}).get("expr", ""))):
    print(f"     {(j.get('schedule') or {}).get('expr',''):14s} {j['name'][:26]}")
print(f"  启用中脚本任务: {len(en_script)} 个")
for j in en_script:
    print(f"     {(j.get('schedule') or {}).get('expr',''):14s} {j['name'][:26]}  ← {j.get('script')}")
print(f"  已暂停: {sum(1 for j in jobs2 if not j.get('enabled'))} 个")
