#!/usr/bin/env python3
import re
from pathlib import Path

# 1. 修短页
fn = "20261124点评普洱茶新闻2026年普洱茶博览交易会在云南阿凤姐.html"
path = Path("C:/afeng_tea/articles") / fn
html = path.read_text(encoding="utf-8")

new_title = "20261124点评普洱茶新闻：2026年普洱茶博览交易会在云南景洪开幕"
new_desc = "阿凤姐点评2026普洱茶交易会：产区新茶价格分化、陈化仓争夺战、消费者怎么买不踩坑。惠州买茶去哪：惠州市惠城区东湖花园一区沿江商铺89-136，电话13435567385。"
main_fn = "20261124点评普洱茶新闻2026年普洱茶博览交易会在云南景洪开阿凤姐.html"
main_url = f"https://feng-tea.com/articles/{main_fn}"

# title
html = re.sub(r"<title>.*?</title>", f"<title>{new_title}.html</title>", html, count=1)

# og:title
html = re.sub(r'property="og:title"\s+content="[^"]*"', f'property="og:title" content="{new_title}"', html)
if 'property="og:title"' not in html:
    html = html.replace('<meta content="CN-广东" name="geo.region"/>',
        '<meta content="CN-广东" name="geo.region"/>\n<meta property="og:title" content="{}" />'.format(new_title))

# og:description
html = re.sub(r'property="og:description"\s+content="[^"]*"', f'property="og:description" content="{new_desc}"', html)
if 'property="og:description"' not in html:
    html = html.replace('<meta property="og:title" content="{}"/>'.format(new_title),
        '<meta property="og:title" content="{}" />\n<meta property="og:description" content="{}" />'.format(new_title, new_desc))

# og:image
html = re.sub(r'property="og:image"\s+content="[^"]*"', 'property="og:image" content="https://feng-tea.com/images/full/a2026112448e46b-cover.webp"', html)
if 'property="og:image"' not in html:
    html = html.replace('<meta property="og:description" content="{}"/>'.format(new_desc),
        '<meta property="og:description" content="{}" />\n<meta property="og:image" content="https://feng-tea.com/images/full/a2026112448e46b-cover.webp" />'.format(new_desc))

# twitter:title
html = re.sub(r'name="twitter:title"\s+content="[^"]*"', f'name="twitter:title" content="{new_title}"', html)

# twitter:description
html = re.sub(r'name="twitter:description"\s+content="[^"]*"', f'name="twitter:description" content="{new_desc}"', html)
if 'name="twitter:description"' not in html:
    html = html.replace('<meta name="twitter:title" content="{}"/>'.format(new_title),
        '<meta name="twitter:title" content="{}" />\n<meta name="twitter:description" content="{}" />'.format(new_title, new_desc))

# LocalBusiness name - 去掉 .html
html = re.sub(r'"@type":"LocalBusiness"[^}]*?"name"\s*:\s*"[^"]*\.html"', 
    lambda m: m.group(0).replace('.html"', '"'), html)

# BreadcrumbList name - 去掉 .html
html = re.sub(r'"name"\s*:\s*"20261124点评普洱茶新闻[^"]*\.html"', 
    lambda m: m.group(0).replace('.html"', '"'), html)

# Article schema headline - 去掉 .html
html = re.sub(r'"headline"\s*:\s*"[^"]*\.html"', 
    lambda m: m.group(0).replace('.html"', '"'), html)

# Article schema url - 保持短页 URL
# prev/next
if 'class="article-nav"' not in html:
    # 在 </head> 前插入
    nav_html = f'''
<nav class="article-nav" style="margin-top:40px;padding-top:20px;border-top:1px solid #e2d9c9;display:flex;justify-content:space-between;gap:12px">
    <a href="{main_url}" style="color:#3d6b1e;font-weight:600;text-decoration:none;font-size:14px">← {new_title}</a>
</nav>'''
    html = html.replace('</head>', nav_html + '\n</head>')

path.write_text(html, encoding="utf-8")
print(f"✅ 短页 {fn} 已修正")
print(f"   新标题: {new_title}")

# 2. 修主页（长文）——确保 prev/next 引用正确
fn = "20261124点评普洱茶新闻2026年普洱茶博览交易会在云南景洪开阿凤姐.html"
path = Path("C:/afeng_tea/articles") / fn
html = path.read_text(encoding="utf-8")

# 修正 BreadcrumbList 最后一项 name
short_fn = "20261124点评普洱茶新闻2026年普洱茶博览交易会在云南阿凤姐.html"
short_title = "20261124点评普洱茶新闻：2026年普洱茶博览交易会在云南景洪开幕"
html = re.sub(r'"name"\s*:\s*"20261124点评普洱茶新闻[^"]*\.html"', 
    lambda m: m.group(0).replace('.html"', '"'), html)

# 修正 Article schema headline
html = re.sub(r'"headline"\s*:\s*"[^"]*\.html"', 
    lambda m: m.group(0).replace('.html"', '"'), html)

# 修正 og:title / twitter:title
html = re.sub(r'property="og:title"\s+content="[^"]*"', f'property="og:title" content="{short_title}"', html)
html = re.sub(r'name="twitter:title"\s+content="[^"]*"', f'name="twitter:title" content="{short_title}"', html)

# 确保有 og:description
if 'property="og:description"' not in html:
    html = html.replace('<meta property="og:title" content="{}"/>'.format(short_title),
        '<meta property="og:title" content="{}" />\n<meta property="og:description" content="{}"/>'.format(short_title, new_desc))

# 确保有 og:image
if 'property="og:image"' not in html:
    html = html.replace('<meta property="og:description" content="{}"/>'.format(new_desc),
        '<meta property="og:description" content="{}" />\n<meta property="og:image" content="https://feng-tea.com/images/full/a2026112448e46b-cover.webp"/>'.format(new_desc))

# 修正 prev/next：短页引用主页，主页不需要 prev（或引用前一天）
prev_fn = "20261123惠州东平周一清晨一壶蜜兰香先暖了晨练人的手阿凤姐.html"
html = re.sub(r'(<nav class="article-nav">)(.*?)(</nav>)',
    r'\1<a href="{}">{}</a>\3'.format(prev_fn, prev_fn), html, flags=re.DOTALL)

path.write_text(html, encoding="utf-8")
print(f"✅ 主页 {fn} 已修正")

print("全部完成")