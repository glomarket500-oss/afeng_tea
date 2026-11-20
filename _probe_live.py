# -*- coding: utf-8 -*-
"""探测文章页 + 7 张图 + 首页缩图的线上状态，带重试"""
import sys
import time
import urllib.request
import urllib.parse

SLUG = "20261116茶叶出口量减价增新茶饮抢原料惠州茶客怎么选茶阿凤姐"
PREFIX = "a2026111679b460"
SITE = "https://feng-tea.com"

targets = [("文章页", f"{SITE}/articles/{SLUG}.html")]
targets += [(f"图-{k}", f"{SITE}/images/full/{PREFIX}-{k}.webp") for k in
            ("cover", "s1", "s2", "s3", "s4", "s5", "s6")]
targets += [("首页缩图", f"{SITE}/images/thumb/{SLUG}-hero.webp")]


def probe(url, tries=4):
    u = urllib.parse.urlsplit(url)
    url2 = urllib.parse.urlunsplit((u.scheme, u.netloc, urllib.parse.quote(u.path), "", ""))
    last = "?"
    for i in range(tries):
        try:
            req = urllib.request.Request(url2, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.status, len(r.read())
        except urllib.error.HTTPError as e:
            return e.code, 0
        except Exception as e:
            last = type(e).__name__
            time.sleep(3 + i * 3)
    return 0, last


bad = []
for name, url in targets:
    code, size = probe(url)
    ok = code == 200 and (size if isinstance(size, int) else 0) > 1000
    print(f"  {'✓' if ok else '✗'} {name:10s} HTTP {code}  {size}")
    if not ok:
        bad.append(name)
print("\n" + ("✅ 全部可达" if not bad else f"❌ 异常: {bad}"))
sys.exit(0 if not bad else 1)
