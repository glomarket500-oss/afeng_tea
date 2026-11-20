#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""离线体检文章页：模块完整性 / 标签一致性 / JSON-LD 合法 / 图片文件与标注一致"""
import json
import re
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
FULL = REPO / "images" / "full"

ARTS = [a for a in sorted(REPO.glob("articles/2026111*.html"))
        if "三泡就淡" in a.name or "红泥炉" in a.name]

for art in ARTS:
    h = art.read_text(encoding="utf-8")
    print(f"\n===== {art.name[:40]}… =====")

    def has(pat, label):
        n = len(re.findall(pat, h, re.S))
        print(f"  {label:16s} {n}" + ("  ⚠ 缺失" if n == 0 else ""))
        return n

    has(r'class="lead"', "lead 导语")
    has(r'class="faq-q"', "FAQ 问")
    has(r'class="faq-a"', "FAQ 答")
    has(r'class="scene-fig"', "场景图 fig")
    has(r'geo-box|📍', "GEO 板块")
    has(r'class="xhs-tags"', "xhs-tags")
    has(r'class="article-tags"', "article-tags")
    has(r'class="tags"', "头部 tags")
    has(r'class="cta-box"', "CTA 板块")

    dup = len(re.findall(r"A：\s*A：", h))
    print(f"  FAQ 重复前缀    {dup}" + ("  ⚠ A：A：" if dup else "  ✅ 无"))

    def tags_of(seg):
        seg = re.sub(r"<[^>]*>", " ", seg)
        return re.findall(r"#[^\s#<>]+", seg)

    def grab(pat):
        m = re.search(pat, h, re.S)
        return m.group(1) if m else ""

    top = tags_of(grab(r'<div class="tags">(.*?)</div>'))
    bot = tags_of(grab(r'<div class="article-tags">(.*?)</div>'))
    xhs = tags_of(grab(r'<p class="xhs-tags">(.*?)</p>'))
    print(f"  标签 顶部={len(top)} 底部={len(bot)} xhs={len(xhs)}  "
          f"{'✅ 一致' if top and top == bot == xhs else '⚠ 不一致'}")

    for i, m in enumerate(re.findall(r'application/ld\+json">(.*?)</script>', h, re.S), 1):
        try:
            d = json.loads(m)
            print(f"  JSON-LD#{i} ✅ 合法  image={d.get('image')}")
        except Exception as e:
            print(f"  JSON-LD#{i} ❌ 非法: {e}")

    from PIL import Image
    for m in re.finditer(r'src="\.\./images/full/([^"]+)\.webp"[^>]*width="(\d+)" height="(\d+)"', h):
        fn, w, hh = m.group(1), int(m.group(2)), int(m.group(3))
        p = FULL / f"{fn}.webp"
        if not p.exists():
            print(f"  ❌ 图片缺失: {fn}")
            continue
        iw, ih = Image.open(p).size
        if (iw, ih) != (w, hh):
            print(f"  ⚠ {fn}: 实际 {iw}×{ih} ≠ 标注 {w}×{hh}")

    bad = [k for k in ["林玉凤", "林玉鳳", "1079790744", "107-9790-744",
                       "afeng-tea.vercel.app"] if k in h]
    print(f"  隐私红线: {'❌ 命中 ' + str(bad) if bad else '✅ 干净'}")
print()
