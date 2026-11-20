# -*- coding: utf-8 -*-
"""知识库迁移：从你看不到的账户目录搬到桌面可见的位置
A = C:\\Users\Administrator\Desktop\\MianAI知识库\\MianAI知识库\\vault      （内容全在这）
B = C:\\Users\\Administrator\\Desktop\\MianAI知识库\\MianAI知识库\\vault （桌面上看得见）
步骤：1) B 的 3 篇素材并入 A  2) A 整体搬进 B  3) 改所有脚本/cron/笔记里的路径
运行：python _migrate_vault.py [--apply]
"""
import json
import re
import shutil
import sys
from pathlib import Path

APPLY = "--apply" in sys.argv
SRC = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault")
DST = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault")
SRC_KB = SRC / "资料库" / "素材材料" / "茶叶素材"
DST_KB = DST / "资料库" / "素材材料" / "茶叶素材"
DUP = SRC / "资料库" / "素材材料" / "_重复待确认"

print("=== 迁移前 ===")
print(f"  A 素材: {len(list(SRC_KB.glob('*.md')))} 篇 ｜ A 笔记: {len(list((SRC/'茶叶知识库').glob('*.md')))} 篇")
print(f"  B 素材: {len(list(DST_KB.glob('*.md')))} 篇 ｜ B 顶层: {[p.name for p in DST.iterdir()]}")

# ---- 1) B 的素材并入 A ----
moved_in = []
if DST_KB.exists():
    for p in sorted(DST_KB.glob("*.md")):
        target = SRC_KB / p.name
        if target.exists():
            DUP.mkdir(parents=True, exist_ok=True)
            if APPLY:
                shutil.move(str(p), str(DUP / f"{p.stem}-来自B{p.suffix}"))
            moved_in.append(f"{p.name} → _重复待确认")
        else:
            if APPLY:
                shutil.move(str(p), str(target))
            moved_in.append(f"{p.name} → A/茶叶素材")

print(f"\n=== 1) B 的 {len(moved_in)} 篇素材并入 A ===")
for m in moved_in:
    print(f"  {m}")

# ---- 2) A 整体搬进 B ----
plan = []
for item in sorted(SRC.iterdir()):
    tgt = DST / item.name
    if not tgt.exists():
        plan.append((item, tgt, "整体移动"))
    elif item.is_dir():
        for sub in sorted(item.rglob("*.md")):
            rel = sub.relative_to(item)
            t = tgt / rel
            plan.append((sub, t, "合并" if not t.exists() else "跳过(已存在)"))

print(f"\n=== 2) 搬移计划（{len(plan)} 项）===")
by_top = {}
for s, t, k in plan:
    by_top.setdefault(s.relative_to(SRC).parts[0], []).append(k)
for k, v in by_top.items():
    print(f"  {k}: {len(v)} 项（移动 {v.count('整体移动')} / 合并 {v.count('合并')} / 跳过 {v.count('跳过(已存在)')}）")

if APPLY:
    for s, t, k in plan:
        if k == "跳过(已存在)":
            continue
        t.parent.mkdir(parents=True, exist_ok=True)
        if k == "整体移动" and s.is_dir():
            shutil.move(str(s), str(t))
        else:
            shutil.move(str(s), str(t))

# ---- 3) 改引用 ----
TARGETS = list(Path(r"C:\afeng_tea").glob("*.py"))
TARGETS += list(Path(r"C:\Users\Administrator\AppData\Local\hermes\scripts").glob("*.py"))
TARGETS.append(Path(r"C:\Users\Administrator\AppData\Local\hermes\cron\jobs.json"))
TARGETS += list((DST / "茶叶知识库").glob("*.md")) if (DST / "茶叶知识库").exists() else []
TARGETS += list((SRC / "茶叶知识库").glob("*.md")) if (SRC / "茶叶知识库").exists() else []

pat_bs = re.compile(r"Users[\\]+a[\\]+Desktop")
pat_fs = re.compile(r"Users/Administrator/Desktop")

changed = []
for f in TARGETS:
    if not f.exists() or f.suffix not in (".py", ".json", ".md"):
        continue
    try:
        txt = f.read_text(encoding="utf-8")
    except Exception:
        continue
    if f.suffix == ".json":
        # ⚠️ JSON 必须走解析→改值→重新序列化，绝不能对原文做反斜杠替换
        #    （2026-11-17 事故：原文替换把 C:\\Users\\a 改成 C:\Users，\U 成了非法转义，cron 停摆 73 分钟）
        import json as _json
        try:
            data = _json.loads(txt)
        except Exception:
            print(f"  ⚠ 跳过（JSON 无法解析，交给专门修复脚本）: {f.name}")
            continue
        n_py = 0
        for job in (data.get("jobs", data) if isinstance(data, dict) else data):
            if not isinstance(job, dict):
                continue
            for key in ("prompt", "script", "workdir", "name"):
                v = job.get(key)
                if isinstance(v, str) and ("Users\\a\\Desktop" in v or "Users/a/Desktop" in v):
                    job[key] = pat_bs.sub(lambda m: "Users\\Administrator\\Desktop", v)
                    job[key] = pat_fs.sub(lambda m: "Users/Administrator/Desktop", job[key])
                    n_py += 1
        if n_py:
            new = _json.dumps(data, ensure_ascii=False, indent=2)
            changed.append((f, n_py))
            if APPLY:
                f.write_text(new, encoding="utf-8")
        continue

    new = pat_bs.sub(lambda m: "Users\\Administrator\\Desktop", txt)
    new = pat_fs.sub(lambda m: "Users/Administrator/Desktop", new)
    if new != txt:
        n = len(pat_bs.findall(txt)) + len(pat_fs.findall(txt))
        changed.append((f, n))
        if APPLY:
            f.write_text(new, encoding="utf-8")

print(f"\n=== 3) 路径引用更新（{len(changed)} 个文件）===")
for f, n in changed:
    print(f"  {f.name}: {n} 处")

# ---- 4) Obsidian 指向新位置 ----
CFG = Path(r"C:\Users\Administrator\AppData\Roaming\obsidian\obsidian.json")
if APPLY and CFG.exists():
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    cfg["vaults"] = {"c74677726c5ea0e6": {"path": str(DST), "ts": 1794850889805, "open": True}}
    CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== 4) Obsidian 已指向 {DST} ===")

if not APPLY:
    print("\n（预览模式。加 --apply 执行）")
else:
    print(f"\n=== 迁移后 ===")
    kb = DST / "资料库" / "素材材料" / "茶叶素材"
    print(f"  B 素材: {len(list(kb.glob('*.md')))} 篇")
    print(f"  B 笔记: {len(list((DST/'茶叶知识库').glob('*.md')))} 篇")
    left = list(SRC.rglob("*.md")) if SRC.exists() else []
    print(f"  A 里剩余 md: {len(left)} 篇（应为 0）")
