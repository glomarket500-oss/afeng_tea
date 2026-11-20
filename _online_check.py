#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""线上体检：对照更新后的交接规范书 §6 检查清单（17 项）"""
import urllib.request, urllib.parse, re, json, sys

UA = {"User-Agent": "Mozilla/5.0"}
SLUG = "20261115立冬之后换一壶秋茶阿凤姐教你顺时而饮"

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.status, r.read().decode("utf-8", "ignore")

st, b = get("https://feng-tea.com/articles/" + urllib.parse.quote(SLUG + ".html"))
print(f"文章 HTTP={st}  长度={len(b)}")
st2, idx = get("https://feng-tea.com/index.html")
st3, sm = get("https://feng-tea.com/sitemap.xml")

ok = fail = 0
def chk(n, cond, d=""):
    global ok, fail
    if cond: ok += 1; print(f"  [OK] {n}" + (f"  {d}" if d else ""))
    else: fail += 1; print(f"  [FAIL] {n}  {d}")

print("\n=== 线上检查清单 ===")
chk("1 发布日期=当天", 'datetime="2026-11-15"' in b, "2026-11-15")
desc = re.search(r'<meta name="description" content="([^"]*)"', b)
kw = [k for k in ["凤凰单丛","秋茶","立冬","老丛","养生","顺时而饮"] if k in (desc.group(1) if desc else "")]
chk("2 标题含关键词", "立冬" in b and "秋茶" in b)
chk("3 meta description 3-5 核心词", 3 <= len(kw) <= 5, f"{len(kw)}: {kw}")
chk("4 开篇 Q1/Q2/Q3 齐全", all(x in b for x in ["Q1：","Q2：","Q3："]))
chk("5 Q2 含地址+电话+营业时间",
    "13435567385" in b and "东湖花园一区沿江商铺89-136" in b and "9:00-21:00" in b)
nfig = b.count('class="scene-fig"')
chk("6 每段有场景图", nfig == 6, f"scene-fig={nfig}")
imgs = re.findall(r'<figure class="scene-fig"><img src="([^"]+)"[^>]*width="(\d+)" height="(\d+)"', b)
chk("6b img width/height=真实像素", bool(imgs), f"{len(imgs)} 张标注")
chk("7 结尾 GEO 板块", "惠州买茶去哪" in b)
xt = re.search(r'<p class="xhs-tags">(.*?)</p>', b, re.S)
xtags = re.findall(r'#([^\s#<]+)', xt.group(1)) if xt else []
top = re.search(r'<div class="tags">(.*?)</div>', b, re.S)
ttags = re.findall(r'#([^\s#<]+)', top.group(1)) if top else []
card = re.search(r'<article class="article-card[^>]*id="article-' + re.escape(SLUG) + r'".*?</article>', idx, re.S)
ctags = re.findall(r'#([^\s#<]+)', card.group(0)) if card else []
chk("8 底部 xhs-tags ≥6", len(xtags) >= 6, f"{len(xtags)}")
chk("9 标签含惠州茶叶店+惠州买茶去哪", "惠州茶叶店" in b and "惠州买茶去哪" in b)
at = re.search(r'<div class="article-tags">(.*?)</div>', b, re.S)
chk("10 顶部 .article-tags 模块存在(坑14)", at is not None, f"{len(re.findall(r'#', at.group(1))) if at else 0} 个")
chk("11 三处标签同一套(坑14/§4)", bool(xtags) and set(xtags)==set(ttags)==set(ctags) and len(ctags)>=6,
    f"顶{len(ttags)} 底{len(xtags)} 卡{len(ctags)}")
chk("12 三处标签顺序一致", xtags == ttags == ctags, f"顶{ttags[:3]} 底{xtags[:3]} 卡{ctags[:3]}")
mkt = re.search(r'<meta name="keywords" content="([^"]*)"', b)
jkw = re.search(r'"keywords"\s*:\s*(\[[^\]]*\]|"[^"]*")', b)
chk("13 meta keywords + JSON-LD keywords", mkt is not None and jkw is not None,
    f"meta={'有' if mkt else '无'} jsonld={'有' if jkw else '无'}")
og = re.search(r'<meta property="og:image" content="([^"]*)"', b)
tw = re.search(r'<meta name="twitter:image" content="([^"]*)"', b)
jl = re.search(r'"image"\s*:\s*\[\s*"([^"]*)"', b)
chk("14 og/twitter/JSON-LD image=本篇封面",
    all([og, tw, jl]) and all("homepage-hero" not in (m.group(1) if m else "") for m in (og,tw,jl)),
    f"og={og.group(1).split('/')[-1] if og else None}")
chk("15 首页卡片 description=摘要非标题",
    card is not None and '<meta itemprop="description" content="' in card.group(0)
    and "立冬之后" not in re.search(r'<meta itemprop="description" content="([^"]*)"', card.group(0)).group(1)[:6])
chk("16 FAQ 无重复前缀 A：A：", "A：A：" not in b and "A:A:" not in b)
zh = b.count("林玉凤") + b.count("林玉鳳")
chk("17 真名/QQ 残留=0", zh == 0 and b.count("1079790744") == 0, f"真名={zh}")
cards = idx.count('class="article-card')
first_pos = idx.find(f'id="article-{SLUG}"')
second_pos = idx.find('class="article-card', first_pos + 10)
chk("18 首页卡片第1位 + sitemap+1",
    first_pos != -1 and (second_pos == -1 or first_pos < second_pos)
    and f"{SLUG}.html" in sm, f"卡片={cards} sitemap={sm.count('<loc>')}")
foot = re.search(r'🔄 上次更新：<time datetime="([^"]*)"', b)
cnt = re.search(r'共 <span id="article-count">(\d+)</span>', b)
chk("19 页脚日期+篇数", foot is not None and cnt is not None, f"{foot.group(1) if foot else None} / {cnt.group(1) if cnt else None} 篇")
# 全站真名
zh_site = idx.count("林玉凤") + idx.count("林玉鳳")
chk("20 全站首页真名=0", zh_site == 0, f"{zh_site}")

print(f"\n=== 通过 {ok} / 失败 {fail} ===")
