#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""步骤8：一次原子提交并推送（规范书 §4 步骤8）"""
import subprocess, sys
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
SLUG = "20261115立冬之后换一壶秋茶阿凤姐教你顺时而饮"

def run(cmd, **kw):
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, **kw)
    print(f"$ {' '.join(cmd)}\n{r.stdout}{r.stderr}")
    return r

# 只加本次发布涉及的文件
run(["git", "add", "index.html", "sitemap.xml"])
run(["git", "add", f"articles/{SLUG}.html"])
run(["git", "add", "articles/", "products/"])          # 页脚同步
run(["git", "add", "images/full/qiuchu-cover.webp", "images/full/qiuchu-s1.webp",
     "images/full/qiuchu-s2.webp", "images/full/qiuchu-s3.webp",
     "images/full/qiuchu-s4.webp", "images/full/qiuchu-s5.webp",
     "images/full/qiuchu-s6.webp",
     f"images/thumb/{SLUG}-hero.webp"])

r = run(["git", "status", "--short"])
staged = [l for l in r.stdout.split("\n") if l and not l.startswith("??")]
print(f"\n暂存 {len(staged)} 个文件 / 未暂存 {len([l for l in r.stdout.split(chr(10)) if l.startswith('??')])} 个")

r = run(["git", "diff", "--cached", "--stat"])
if not staged:
    print("!! 没有暂存内容，中止")
    sys.exit(1)

msg = ("發布新文章《立冬之后，换一壶秋茶》（2026-11-15）："
       "封面＋6 張場景圖＋開篇 Q&A 三問＋結尾 GEO 板塊；同步頁腳與 sitemap")
r = run(["git", "commit", "-m", msg])
if r.returncode != 0:
    print("!! commit 失败，中止")
    sys.exit(1)

r = run(["git", "log", "--oneline", "-1"])
print("\n=== 准备推送 ===")
r = run(["git", "push", "origin", "main"])
print("\npush 返回码:", r.returncode)
