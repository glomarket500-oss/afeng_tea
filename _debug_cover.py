# -*- coding: utf-8 -*-
"""定位：og:image / twitter:image / JSON-LD image 三处谁是漏的"""
import sys
import re
import json
from pathlib import Path

sys.path.insert(0, r"C:\afeng_tea")
import publish_new as P

draft = Path(sys.argv[1])
raw = P.scrub(draft.read_text(encoding="utf-8"))
title, lead, sections, faq, tags, preview = P.parse_draft(raw)
tagged = list(tags)
for t in P.CASE_TAGS:
    if t not in tagged:
        tagged.append(t)
tagged = tagged[:10]
if not lead:
    lead = P.synth_lead(title, sections, faq)
qa, used = P.build_qa(faq, title)
faq_rest = [f for f in faq if f[0] not in used]
slug = P.make_slug(title, "20261115")
prefix = "a20261115DEBUG"
desc = (lead[:110].replace("\n", " ") + " 惠州买茶去哪：X，电话Y。")[:300]
meta = {"title": title, "slug": slug, "prefix": prefix, "desc": desc,
        "date": "2026-11-15", "zh_date": "2026年11月15日 20:00", "zh_date_only": "2026年11月15日",
        "new_dt": "2026-11-15T20:00", "prev_slug": "", "prev_title": ""}
prompts = P.build_prompts(title, sections)
dims = {p["key"]: (869, 489) for p in prompts}
page = P.build_page(meta, lead, qa, sections, faq_rest, tagged, preview, prompts, dims)

cover = f"{P.SITE}/images/full/{prefix}-cover.webp"
print("标题:", title)
print("lead 含换行:", "\n" in lead, "| lead 含双引号:", '"' in lead)
print("\n封面 URL 在页面出现次数:", page.count(f"{prefix}-cover.webp"), "（期望 ≥3）")

og = re.search(r'<meta property="og:image" content="([^"]*)"', page)
tw = re.search(r'<meta name="twitter:image" content="([^"]*)"', page)
tw2 = re.search(r'<meta property="twitter:image" content="([^"]*)"', page)
print("og:image     :", og.group(1) if og else "(未找到)")
print("twitter:image:", (tw or tw2).group(1) if (tw or tw2) else "(未找到)")
print("twitter 用的是 name= 还是 property=:", "name=" if tw else ("property=" if tw2 else "都没有"))

for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
    try:
        d = json.loads(m.group(1))
        print("JSON-LD      : ✓ 合法, image =", d.get("image"))
    except Exception as e:
        print("JSON-LD      : ✗ 非法:", e)
        print("  片段:", m.group(1)[:200].replace("\n", "\\n"))
