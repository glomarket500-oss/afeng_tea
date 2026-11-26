#!/usr/bin/env python3
"""
batch_fix_2weeks_round2.py — 第二轮修复：纯字符串替换，不重排 HTML
目标：补 geo:region/placename/position、补 LocalBusiness + BreadcrumbList schema、
      修正 article:published_time 为真实时间戳、补 prev/next 导航
"""
import re
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

ARTICLES_DIR = Path(__file__).parent / "articles"
CST = timezone(timedelta(hours=8))

STORE = {
    "name": "阿凤姐茶叶店（惠州凤凰茶业）",
    "street": "东湖花园一区沿江商铺89-136",
    "locality": "惠州市",
    "region": "广东省",
    "phone": "+8613435567385",
    "lat": 23.08,
    "lng": 114.40,
    "opening": "Mo-Su 09:00-21:00",
    "url": "https://feng-tea.com",
}

def parse_date(fname: str) -> datetime | None:
    m = re.match(r"(\d{8})", fname)
    if not m: return None
    try:
        return datetime.strptime(m.group(1), "%Y%m%d").replace(tzinfo=CST)
    except ValueError:
        return None

def list_two_week_articles():
    items = []
    for f in sorted(ARTICLES_DIR.glob("*.html")):
        if f.name.startswith("."): continue
        dt = parse_date(f.name)
        if dt and datetime(2026, 11, 11, tzinfo=CST) <= dt <= datetime(2026, 11, 25, tzinfo=CST):
            items.append({"path": f, "name": f.name, "date": dt})
    items.sort(key=lambda x: x["date"])
    return items

def get_real_published_time(html: str, fallback: datetime) -> str:
    """从 ld+json 的 datePublished 提取真实时间戳"""
    m = re.search(r'"datePublished"\s*:\s*"([^"]+)"', html)
    if m:
        return m.group(1)
    return fallback.strftime("%Y-%m-%dT%H:%M:%S+08:00")

def build_localbusiness_schema() -> str:
    s = STORE
    return f'''<script type="application/ld+json">{{"@context":"https://schema.org","@type":"LocalBusiness","@id":"{s['url']}/#store","name":"{s['name']}","image":"{s['url']}/images/afeng-avatar.webp","url":"{s['url']}","telephone":"{s['phone']}","priceRange":"¥¥","address":{{"@type":"PostalAddress","streetAddress":"{s['street']}","addressLocality":"{s['locality']}","addressRegion":"{s['region']}","postalCode":"516000","addressCountry":"CN"}},"geo":{{"@type":"GeoCoordinates","latitude":{s['lat']},"longitude":{s['lng']}}},"openingHoursSpecification":{{"@type":"OpeningHoursSpecification","dayOfWeek":["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],"opens":"09:00","closes":"21:00"}},"servesCuisine":"Tea","paymentAccepted":"Cash,Credit Card,WeChat Pay,Alipay"}}</script>'''

def build_breadcrumb_schema(filename: str, title: str) -> str:
    return f'''<script type="application/ld+json">{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"首页","item":"https://feng-tea.com/"}},{{"@type":"ListItem","position":2,"name":"茶韵讲古","item":"https://feng-tea.com/#knowledge"}},{{"@type":"ListItem","position":3,"name":"{title}","item":"https://feng-tea.com/articles/{filename}"}}]}}</script>'''

def clean_title(raw: str) -> str:
    t = raw.strip()
    t = re.sub(r"^[\U0001F300-\U0001FAFF\U00002600-\U000027BF\s]+", "", t)
    t = re.sub(r"\s*[\|\-]\s*阿凤姐的故事\s*$", "", t)
    t = re.sub(r"\s*#\w+", "", t)
    t = re.sub(r"[「」]", "", t)
    t = t.replace("：", "，")
    t = re.sub(r"\s+", " ", t).strip()
    return t

def fix_file(path: Path, dt: datetime, all_articles: list, idx: int):
    html = path.read_text(encoding="utf-8")
    orig = html

    # 1. geo:region meta
    geo_meta = f'<meta content="CN-{STORE["region"].replace("省","")[-2:]}" name="geo.region"/>\n<meta content="{STORE["locality"]}" name="geo.placename"/>\n<meta content="{STORE["lat"]:.2f};{STORE["lng"]:.2f}" name="geo.position"/>'
    if 'name="geo.region"' not in html:
        # 插到 canonical 之后
        if 'rel="canonical"' in html:
            m = re.search(r'<link[^>]*rel="canonical"[^>]*/>', html)
            if m:
                html = html[:m.end()] + "\n" + geo_meta + html[m.end():]
        else:
            # 插到 </head> 前
            html = html.replace("</head>", geo_meta + "\n</head>", 1)

    # 2. article:published_time 修正
    real_time = get_real_published_time(html, dt)
    html = re.sub(
        r'(<meta content=")[^"]*(" property="article:published_time"/>)',
        rf'\g<1>{real_time}\g<2>',
        html
    )

    # 3. LocalBusiness schema
    if '"@type": "LocalBusiness"' not in html and '"@type":"LocalBusiness"' not in html:
        lb = build_localbusiness_schema()
        html = html.replace("</head>", lb + "\n</head>", 1)

    # 4. BreadcrumbList schema
    if '"@type": "BreadcrumbList"' not in html and '"@type":"BreadcrumbList"' not in html:
        # 从 <title> 提取清洗后的标题
        m = re.search(r"<title>(.*?)</title>", html)
        title = clean_title(m.group(1)) if m else path.stem
        bc = build_breadcrumb_schema(path.name, title)
        html = html.replace("</head>", bc + "\n</head>", 1)

    # 5. prev/next 导航
    nav = re.search(r'<div class="article-nav">.*?</div>', html, re.DOTALL)
    if nav:
        prev_file = all_articles[idx - 1]["name"] if idx > 0 else None
        next_file = all_articles[idx + 1]["name"] if idx < len(all_articles) - 1 else None
        prev_title = clean_title(prev_file.replace(".html", "")) if prev_file else ""
        next_title = clean_title(next_file.replace(".html", "")) if next_file else ""
        prev_html = f'<a href="{prev_file}">← 上一篇：{prev_title}</a>' if prev_file else '<span></span>'
        next_html = f'<a href="{next_file}" style="text-align:right">下一篇：{next_title} →</a>' if next_file else '<span></span>'
        new_nav = f'<div class="article-nav">{prev_html}{next_html}</div>'
        html = html[:nav.start()] + new_nav + html[nav.end():]

    if html != orig:
        path.write_text(html, encoding="utf-8")
        return True
    return False

def main():
    articles = list_two_week_articles()
    print(f"两周内文章共 {len(articles)} 篇，开始第二轮修复...")
    fixed_count = 0
    for i, art in enumerate(articles):
        changed = fix_file(art["path"], art["date"], articles, i)
        if changed:
            fixed_count += 1
            print(f"  ✅ [{i+1}/{len(articles)}] {art['name']}")
        else:
            print(f"  ⏭️  [{i+1}/{len(articles)}] {art['name']} (无变化)")
    print(f"\n✅ 第二轮修复完成，共修改 {fixed_count} 篇")

if __name__ == "__main__":
    main()
