# -*- coding: utf-8 -*-
"""从已上线文章里把阿凤姐的实拍图下回来（线上图即她的原始照片），存作固定参考图"""
import re
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(r"C:\afeng_tea\images\afeng_ref")
OUT.mkdir(parents=True, exist_ok=True)
HDR = {"User-Agent": "Mozilla/5.0"}


def get(url, timeout=45):
    req = urllib.request.Request(quote_url(url), headers=HDR)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def quote_url(u):
    return urllib.parse.quote(u, safe=":/?&=%#")


# 最近几篇用过实拍照的文章
ARTICLES = [
    "https://feng-tea.com/articles/20261120惠州清晨第一杯茶六点半就烧上了水阿凤姐.html",
    "https://feng-tea.com/articles/20261119清晨六点半的惠州东平一壶凤凰单丛理年货单阿凤姐.html",
]
saved = []
for a in ARTICLES:
    try:
        html = get(a).decode("utf-8", "ignore")
    except Exception as e:
        print(f"✗ 抓不到文章 {a.split('/')[-1][:20]}: {type(e).__name__}")
        continue
    imgs = re.findall(r'src="\.\./images/(?:full|thumbs)/([^"]+)"', html)
    print(f"{a.split('/')[-1][:26]}  图 {len(imgs)} 张")
    for name in imgs:
        base = name.split("-")[0]
        url = f"https://feng-tea.com/images/full/{name}"
        dst = OUT / name
        if dst.exists():
            saved.append(dst)
            continue
        try:
            data = get(url)
            dst.write_bytes(data)
            saved.append(dst)
            print(f"   ↓ {name} {len(data)//1024}KB")
        except Exception as e:
            print(f"   ✗ {name} {type(e).__name__}")

print(f"\n共保存 {len(saved)} 张到 {OUT}")
