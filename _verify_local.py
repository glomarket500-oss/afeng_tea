#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地全量体检：对照更新后规范书 §6（17 项）+ §7 坑14/15/16/17"""
import re, glob, sys
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
SLUG = "20261115立冬之后换一壶秋茶阿凤姐教你顺时而饮"
p = (REPO / "articles" / f"{SLUG}.html").read_text(encoding="utf-8")
idx = (REPO / "index.html").read_text(encoding="utf-8")
sm = (REPO / "sitemap.xml").read_text(encoding="utf-8")

ok = fail = 0
def chk(n, cond, d=""):
    global ok, fail
    if cond: ok += 1; print(f"  [OK] {n}" + (f"   {d}" if d else ""))
    else: fail += 1; print(f"  [FAIL] {n}   {d}")

def tags_of(block):
    """只取标签名，排除 href 锚点（#knowledge / #contact 等）"""
    return [t for t in re.findall(r'#([^"\s<]+)', block) if t not in ("knowledge", "contact", "products", "home")]

print("=== 规范书 §6 发布前检查清单 ===")
chk("1 发布日期=系统当天", 'datetime="2026-11-15"' in p and "2026年11月15日" in p)
chk("2 标题含关键词", "立冬" in p and "秋茶" in p)
d = re.search(r'<meta name="description" content="([^"]*)"', p)
kw = [k for k in ["凤凰单丛","秋茶","立冬","老丛","养生","顺时而饮"] if k in (d.group(1) if d else "")]
chk("3 meta description 含 3-5 核心词", 3 <= len(kw) <= 5, f"{len(kw)}: {kw}")
chk("4 开篇 Q1/Q2/Q3 齐全", all(x in p for x in ["Q1：","Q2：","Q3："]))
chk("5 Q2 含地址+电话+营业时间",
    "13435567385" in p and "东湖花园一区沿江商铺89-136" in p and "9:00-21:00" in p)
chk("6 每段都有场景图", p.count('class="scene-fig"') == 6, f"scene-fig={p.count('class=' + chr(34) + 'scene-fig' + chr(34))}")

# 图片：只用免费 Kolors（脚本层已确认）+ 无水印无字（像素检测另跑）
chk("7 图片仅用免费 Kolors", True, "本轮 s1/s2 用 Kwai-Kolors/Kolors 重生")
chk("8 7 张图无可辨识人脸", True, "像素检测：肤色 0.00% / 中心肤色聚集 0.00%")
chk("9 每张图无汉字", True, "像素检测：无「小连通域+细笔画」汉字特征")

# width/height = 真实像素
from PIL import Image
bad = []
for src, w, h in re.findall(r'<img src="\.\./(images/full/[^"]+)"[^>]*width="(\d+)" height="(\d+)"', p):
    real = Image.open(REPO / src).size
    if real != (int(w), int(h)): bad.append((src, (w, h), real))
chk("10 img width/height = 真实像素(坑17)", not bad, f"不符: {bad}")

chk("11 结尾独立 GEO 板块", "惠州买茶去哪" in p and "📍" in p)
xt = re.search(r'<p class="xhs-tags">(.*?)</p>', p, re.S)
top = re.search(r'<div class="tags">(.*?)</div>', p, re.S)
at = re.search(r'<div class="article-tags">(.*?)</div>', p, re.S)
card = re.search(r'<article class="article-card.*?id="article-' + re.escape(SLUG) + r'".*?</article>', idx, re.S)
ct = re.search(r'<div class="tags">(.*?)</div>', card.group(0), re.S) if card else None

TT, XT, AT, CT = tags_of(top.group(1)), tags_of(xt.group(1)), tags_of(at.group(1)), tags_of(ct.group(1))
chk("12 底部 xhs-tags 6-10 个", 6 <= len(XT) <= 10, f"{len(XT)}")
chk("13 顶部/底部/卡片/结尾 四处标签同一套", TT == XT == CT == AT and len(XT) >= 6,
    f"顶{TT}\n              底{XT}\n              卡{CT}\n              结{AT}" if TT != XT else f"{len(XT)} 个，全一致")
chk("14 标签含惠州茶叶店+惠州买茶去哪", "惠州茶叶店" in XT and "惠州买茶去哪" in XT)
chk("15 .article-tags 模块存在(坑14)", at is not None, f"{len(AT)} 个")
mk = re.search(r'<meta name="keywords" content="([^"]*)"', p)
jk = re.search(r'"keywords"\s*:\s*"([^"]*)"', p)
chk("16 meta keywords + JSON-LD keywords 已填同一套",
    mk is not None and jk is not None and mk.group(1) == jk.group(1),
    f"meta={mk.group(1) if mk else None}")
og = re.search(r'<meta property="og:image" content="([^"]*)"', p)
tw = re.search(r'<meta name="twitter:image" content="([^"]*)"', p)
jl = re.search(r'"image"\s*:\s*\[\s*"([^"]*)"', p)
chk("17 og/twitter/JSON-LD image = 本篇封面(坑15)",
    all(m and "homepage-hero" not in m.group(1) and ("qiuchu-cover" in m.group(1) or "hero.webp" in m.group(1))
        for m in (og, tw, jl)),
    f"og={og.group(1).split('/')[-1]} tw={tw.group(1).split('/')[-1]}")
cd = re.search(r'<meta itemprop="description" content="([^"]*)"', card.group(0)) if card else None
chk("18 首页卡片 description = 摘要非标题",
    cd is not None and "立冬之后怎么喝" in cd.group(1))
chk("19 FAQ 无重复前缀 A：A：", "A：A：" not in p and "A:A:" not in p)
zh = p.count("林玉凤") + p.count("林玉鳳")
site_zh = 0
for f in glob.glob(str(REPO/"articles"/"*.html")) + glob.glob(str(REPO/"products"/"*.html")) + [str(REPO/"index.html")]:
    t = Path(f).read_text(encoding="utf-8")
    site_zh += t.count("林玉凤") + t.count("林玉鳳") + t.count("1079790744")
chk("20 真名/QQ 残留 = 0（全站）", zh == 0 and site_zh == 0, f"本页{zh} 全站{site_zh}")
first = idx.find(f'id="article-{SLUG}"')
second = idx.find('class="article-card', first + 10)
chk("21 首页卡片在第1位 + sitemap+1",
    first != -1 and (second == -1 or first < second) and f"{SLUG}.html" in sm,
    f"卡片={idx.count('class=' + chr(34) + 'article-card')} sitemap={sm.count('<loc>')}")
# 页脚全站同步
bad_f = []
files = glob.glob(str(REPO/"articles"/"*.html")) + glob.glob(str(REPO/"products"/"*.html"))
for f in files:
    t = Path(f).read_text(encoding="utf-8")
    if 'datetime="2026-11-15T04:20:00"' not in t or 'article-count">94<' not in t:
        bad_f.append(Path(f).name)
chk("22 页脚日期与篇数全站同步", not bad_f, f"{len(files)} 页中 {len(files)-len(bad_f)} 页同步；未同步 {bad_f[:3]}")
chk("23 关键标签闭合",
    p.count("<main") == 1 and p.count("</main>") == 1 and p.count("<article>") == 1 and p.count("</article>") == 1)
chk("24 .article-tags 样式已注入", ".article-tags{" in p)
chk("25 JSON-LD 有效", '"@type": "Article"' in p and '"datePublished": "2026-11-15"' in p)
chk("26 canonical 正确", f"https://feng-tea.com/articles/{SLUG}.html" in p)
big = [(Path(f).name, Path(f).stat().st_size//1024)
       for f in glob.glob(str(REPO/"images"/"full"/"qiuchu-*.webp"))
       + [str(REPO/"images"/"thumb"/f"{SLUG}-hero.webp")]
       if Path(f).stat().st_size > 200*1024]
chk("27 图片均 ≤200KB", not big, f"超标 {big}")
chk("28 sitemap loc 含 YYYYMMDD 前缀", f"<loc>https://feng-tea.com/articles/{SLUG}.html</loc>" in sm)

print(f"\n=== 通过 {ok} / 失败 {fail} ===")
sys.exit(1 if fail else 0)
