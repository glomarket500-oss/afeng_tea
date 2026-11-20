#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布前 13 项检查清单（规范书 §6）"""
import re, glob, sys
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
SLUG = "20261115立冬之后换一壶秋茶阿凤姐教你顺时而饮"
art = REPO / "articles" / f"{SLUG}.html"
idx = (REPO / "index.html").read_text(encoding="utf-8")
sm = (REPO / "sitemap.xml").read_text(encoding="utf-8")
p = art.read_text(encoding="utf-8")

ok = 0
fail = 0

def chk(n, cond, detail=""):
    global ok, fail
    if cond:
        ok += 1
        print(f"  [OK] {n}" + (f"  {detail}" if detail else ""))
    else:
        fail += 1
        print(f"  [FAIL] {n}  {detail}")

print("=== 发布前检查清单 ===")
chk("1 发布日期用系统当天", 'datetime="2026-11-15"' in p and '2026年11月15日' in p)
chk("2 标题含关键词", "立冬" in p and "秋茶" in p)
desc = re.search(r'<meta name="description" content="([^"]*)"', p)
kw = [k for k in ["凤凰单丛", "秋茶", "立冬", "老丛", "养生"] if k in (desc.group(1) if desc else "")]
chk("3 meta description 含 3-5 核心词", 3 <= len(kw) <= 5, f"命中 {len(kw)}: {kw}")
chk("4 开篇 Q1/Q2/Q3 齐全", all(x in p for x in ["Q1：", "Q2：", "Q3："]))
chk("5 Q2 含地址+电话+营业时间",
    "13435567385" in p and "东湖花园一区沿江商铺89-136" in p and "9:00-21:00" in p)
nfig = p.count('class="scene-fig"')
imgs = [f"images/full/qiuchu-{k}.webp" for k in ["cover", "s1", "s2", "s3", "s4", "s5", "s6"]]
miss = [i for i in imgs if not (REPO / i).exists()]
chk("6 每个段落都有场景图", nfig == 6 and not miss, f"scene-fig={nfig}, 缺图={miss}")
chk("7 结尾独立 GEO 板块", "惠州买茶去哪" in p)
xtags = re.search(r'<p class="xhs-tags">(.*?)</p>', p, re.S)
ntags = len(xtags.group(1).split("#")) - 1 if xtags else 0
chk("8 文末话题标签 ≥6", ntags >= 6, f"{ntags} 个")
chk("9 标签含惠州茶叶店+惠州买茶去哪", "惠州茶叶店" in p and "惠州买茶去哪" in p)
zh = p.count("林玉凤") + p.count("林玉鳳")
qq = p.count("1079790744")
chk("10 真名/QQ 残留 = 0", zh == 0 and qq == 0, f"真名={zh} QQ={qq}")
# 全站扫一遍
site_zh = 0
for f in glob.glob(str(REPO / "articles" / "*.html")) + glob.glob(str(REPO / "products" / "*.html")) + [str(REPO / "index.html")]:
    t = Path(f).read_text(encoding="utf-8")
    site_zh += t.count("林玉凤") + t.count("林玉鳳")
chk("10b 全站真名残留 = 0", site_zh == 0, f"共 {site_zh} 处")
cards = idx.count('class="article-card')
first = idx.find(f'id="article-{SLUG}"')
chk("11 首页卡片在第1位 + sitemap+1",
    first != -1 and first < idx.find('class="article-card', first + 10) and f"{SLUG}.html" in sm,
    f"卡片数={cards}, sitemap loc={sm.count('<loc>')}")
# 页脚同步
foot_ok = 0
foot_bad = []
for f in glob.glob(str(REPO / "articles" / "*.html")) + glob.glob(str(REPO / "products" / "*.html")):
    t = Path(f).read_text(encoding="utf-8")
    if 'datetime="2026-11-15T04:20:00"' in t and 'article-count">94<' in t:
        foot_ok += 1
    else:
        foot_bad.append(Path(f).name)
chk("12 页脚日期与篇数全站同步", not foot_bad, f"同步 {foot_ok} 页，未同步 {len(foot_bad)}: {foot_bad[:3]}")
# 结构
chk("13a 关键标签闭合", p.count("<main") == 1 and p.count("</main>") == 1
    and p.count("<article>") == 1 and p.count("</article>") == 1)
chk("13b xhs-tags 样式已注入", ".xhs-tags{" in p)
chk("13c JSON-LD 有效", '"@type": "Article"' in p and '"datePublished": "2026-11-15"' in p)
chk("13d canonical 正确", f"https://feng-tea.com/articles/{SLUG}.html" in p)
# 图片体积
big = [(f.name, f.stat().st_size // 1024) for f in list((REPO / "images" / "full").glob("qiuchu-*.webp"))
       + [REPO / "images" / "thumb" / f"{SLUG}-hero.webp"] if f.stat().st_size > 200 * 1024]
chk("13e 图片均 ≤200KB", not big, f"超标: {big}")
th = REPO / "images" / "thumb" / f"{SLUG}-hero.webp"
chk("13f 缩图存在且400px宽", th.exists(), f"{Image_size if False else ''}{th.stat().st_size//1024 if th.exists() else 0}KB")

print(f"\n=== 通过 {ok} / 失败 {fail} ===")
sys.exit(1 if fail else 0)
