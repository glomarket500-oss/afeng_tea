# -*- coding: utf-8 -*-
"""补生成缺失配图（cover/s1 等），并从封面重做首页缩图；然后提交推送。
只补缺失的，不重做已生成的，避免无谓覆盖。
"""
import sys
import subprocess
import urllib.request
from pathlib import Path

sys.path.insert(0, r"C:\afeng_tea")
import publish_new as P

SLUG = "20261116茶叶出口量减价增新茶饮抢原料惠州茶客怎么选茶阿凤姐"
PREFIX = "a2026111679b460"
DRAFT = Path(r"C:\afeng_tea\weekly_drafts\20261116-周评-茶叶出口量减价增新茶饮.md")

raw_text = P.scrub(DRAFT.read_text(encoding="utf-8"))
title, lead, sections, faq, tags, preview = P.parse_draft(raw_text)
prompts = P.build_prompts(title, sections)
print(f"标题: {title}")
print(f"应有 {len(prompts)} 张，检查缺失…\n")

full = P.REPO / "images" / "full"
thumb = P.REPO / "images" / "thumb"
env = P.load_env()
key = env.get("SILICONFLOW_API_KEY")
if not key:
    raise SystemExit("缺少 SILICONFLOW_API_KEY")

made = []
for p in prompts:
    fp = full / f"{PREFIX}-{p['key']}.webp"
    if fp.exists() and fp.stat().st_size > 3000:
        print(f"  ↺ {p['key']} 已存在（{fp.stat().st_size // 1024}KB），跳过")
        continue
    print(f"  → 补生成 {p['key']}: {p['desc']}")
    raw = None
    for attempt in range(3):
        try:
            u = P.gen_image(key, p["desc"])
            raw = urllib.request.urlopen(u, timeout=150).read()
            break
        except Exception as e:
            print(f"      第{attempt + 1}次失败: {e}")
    if raw is None:
        print(f"      ❌ {p['key']} 仍未成功，稍后重试")
        continue
    w, h, sz = P.to_webp(raw, fp, 869, 489)
    warns = P.audit_image(fp)
    print(f"      ✓ {w}×{h} {sz // 1024}KB  像素检测: {'⚠ ' + ';'.join(warns) if warns else '通过'}")
    made.append(p["key"])
    if p["key"] == "cover":
        P.to_webp(raw, thumb / f"{SLUG}-hero.webp", 400)
        print("      ✓ 首页缩图已从封面重建")

print(f"\n补齐: {made or '无'}")

# 完整性硬校验：7 张必须全部存在且 >3KB
missing = [p["key"] for p in prompts
           if not (full / f"{PREFIX}-{p['key']}.webp").exists()
           or (full / f"{PREFIX}-{p['key']}.webp").stat().st_size <= 3000]
hero = thumb / f"{SLUG}-hero.webp"
if missing:
    print(f"❌ 仍缺: {missing} —— 不提交")
    sys.exit(1)
if not hero.exists():
    print("❌ 首页缩图缺失 —— 不提交")
    sys.exit(1)
print("✅ 7 张图 + 首页缩图 全部落盘")

files = [f"images/full/{PREFIX}-{p['key']}.webp" for p in prompts] + [f"images/thumb/{SLUG}-hero.webp"]
subprocess.run(["git", "add", "--"] + files, cwd=r"C:\afeng_tea")
r = subprocess.run(["git", "commit", "-m",
                    f"修《{title}》配图缺失：cover/s1 因 DNS 中断未落盘（线上 404），已补生成并从封面重建首页缩图"],
                   cwd=r"C:\afeng_tea", capture_output=True, text=True, encoding="utf-8", errors="replace")
print((r.stdout + r.stderr).strip()[:300])
p = subprocess.run(["git", "push", "origin", "main"], cwd=r"C:\afeng_tea",
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print(f"push rc={p.returncode} {(p.stdout + p.stderr).strip()[:200]}")
