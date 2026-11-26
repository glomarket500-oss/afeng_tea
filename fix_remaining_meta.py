#!/usr/bin/env python3
import re

# 11-20: 修正 head 里残留的旧标题
fn = "20261120说紫砂紫砂之家紫砂壶茶具建盏收藏精阿凤姐.html"
new_title = "20261120阿凤姐的紫砂避坑指南：二十年茶人教你四步买对壶.html"
with open("C:/afeng_tea/articles/" + fn, "r", encoding="utf-8") as f:
    html = f.read()

html = re.sub(r'<link href="https://feng-tea\.com/articles/[^"]*" rel="canonical"/>',
              f'<link href="https://feng-tea.com/articles/{fn}" rel="canonical"/>', html)
html = re.sub(r'property="og:title" content="[^"]*"',
              f'property="og:title" content="{new_title}"', html)
html = re.sub(r'property="og:url" content="[^"]*"',
              f'property="og:url" content="https://feng-tea.com/articles/{fn}"', html)
html = re.sub(r'name="twitter:title" content="[^"]*"',
              f'name="twitter:title" content="{new_title}"', html)
html = re.sub(r'"headline"\s*:\s*"[^"]*"', f'"headline": "{new_title}"', html)
html = re.sub(r'"url"\s*:\s*"[^"]*"', f'"url": "https://feng-tea.com/articles/{fn}"', html)
html = re.sub(r'"name"\s*:\s*"20261120阿凤姐的紫砂避坑指南[^"]*"',
              f'"name": "{new_title}"', html)

with open("C:/afeng_tea/articles/" + fn, "w", encoding="utf-8") as f:
    f.write(html)
print("11-20 head metadata 已修正")

# 11-22/11-23 清晨篇的 article-nav 链接指向旧剪纸篇标题，改为新标题
new_jianzi = "20261122阿凤姐点评非遗新闻：鄂派紫砂入选省级非遗，宜兴这边怎么看.html"
for fn in ["20261122周日清晨的惠州东平用一壶鸭屎香叫醒整条江边阿凤姐.html",
           "20261123惠州东平周一清晨一壶蜜兰香先暖了晨练人的手阿凤姐.html"]:
    with open("C:/afeng_tea/articles/" + fn, "r", encoding="utf-8") as f:
        html = f.read()
    html = re.sub(r'>点评紫砂新闻剪纸武汉剪纸阿凤姐<', f'>{new_jianzi}<', html)
    html = re.sub(r'剪纸武汉剪纸', '鄂派紫砂入选省级非遗', html)
    with open("C:/afeng_tea/articles/" + fn, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"{fn} nav 链接已修正")

# 11-24 短页：补 og:title、Article schema、prev/next
fn = "20261124点评普洱茶新闻2026年普洱茶博览交易会在云南阿凤姐.html"
with open("C:/afeng_tea/articles/" + fn, "r", encoding="utf-8") as f:
    html = f.read()
new_title = "20261124点评普洱茶新闻2026年普洱茶博览交易会在云南景洪开幕.html"
main_article = "20261124点评普洱茶新闻2026年普洱茶博览交易会在云南景洪开阿凤姐.html"

if 'property="og:title"' not in html:
    html = html.replace('<meta property="og:locale" content="zh_CN"/>',
                       '<meta property="og:locale" content="zh_CN"/>\n<meta property="og:title" content="{}"/>'.format(new_title))
if 'name="twitter:card"' not in html:
    html = html.replace('</head>',
        '<meta name="twitter:card" content="summary_large_image"/>\n<meta name="twitter:title" content="{}"/>\n</head>'.format(new_title))
if '"@type":"Article"' not in html and '"@type": "Article"' not in html:
    schema = '<script type="application/ld+json">{"@context":"https://schema.org","@type":"Article","headline":"' + new_title + '","url":"https://feng-tea.com/articles/' + fn + '","datePublished":"2026-11-24T20:30:00+08:00","author":{"@type":"Person","name":"阿凤姐"},"publisher":{"@type":"Organization","name":"凤凰茶业"}}</script>'
    html = html.replace('</head>', schema + '\n</head>')
if 'class="article-nav"' in html:
    html = re.sub(r'(<nav class="article-nav">)(.*?)(</nav>)',
        r'\1<a href="{}">{}</a>\3'.format(main_article, main_article), html, flags=re.DOTALL)

with open("C:/afeng_tea/articles/" + fn, "w", encoding="utf-8") as f:
    f.write(html)
print("11-24 短页 metadata 已补全")

print("全部修正完成")