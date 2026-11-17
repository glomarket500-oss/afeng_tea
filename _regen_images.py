# -*- coding: utf-8 -*-
"""补生成今天这篇的 7 张配图 + 首页缩略图
原因：第一次发布时用的是没有 PIL 的解释器，图片全部生成失败（线上 404）。
现在用专用 venv（3.14 + Pillow）重跑 make_images，文件名与页面引用完全一致，不用改 HTML。
"""
import os
import sys
import time
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
os.chdir(REPO)
sys.path.insert(0, str(REPO))

import publish_new as P  # noqa: E402

DRAFT = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault\资料库\素材材料\茶叶素材\2026-11-17-清晨第一杯茶先叫醒叶子.md")
PREFIX = "a202611178f138d"
SLUG = "20261117清晨第一杯茶先叫醒叶子惠州东平的六点十分阿凤姐"

t0 = time.time()
raw = P.scrub(DRAFT.read_text(encoding="utf-8"))
title, lead, sections, faq, tags, preview = P.parse_draft(raw)
print(f"标题: {title}")
print(f"幕数: {len(sections)}  标签: {len(tags)}")
print()

prompts, dims, audit_log = P.make_images(PREFIX, title, sections, SLUG)

print()
print("=" * 50)
full = REPO / "images" / "full"
thumb = REPO / "images" / "thumb"
ok, bad = [], []
for p in prompts:
    f = full / f"{PREFIX}-{p['key']}.webp"
    if f.exists() and f.stat().st_size > 5000:
        ok.append((p["key"], f.stat().st_size))
    else:
        bad.append(p["key"])
hero = thumb / f"{SLUG}-hero.webp"
print(f"✓ 成品: {len(ok)} 张  " + "  ".join(f"{k}={s//1024}KB" for k, s in ok))
print(f"✗ 失败: {bad if bad else '无'}")
print(f"{'✓' if hero.exists() else '✗'} 首页缩略图: {hero.name[:36]}… {hero.stat().st_size//1024 if hero.exists() else 0}KB")
print(f"质检问题: {audit_log if audit_log else '无'}")
print(f"耗时: {time.time()-t0:.0f} 秒")
