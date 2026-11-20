# -*- coding: utf-8 -*-
"""每天抓「紫砂壶」真实新闻（Tavily）→ 存知识库，供「今日一壶」点评用

为什么要单独抓：
  知识库 12-新闻素材/ 是综合茶行业新闻，紫砂条目稀，常被"茶博会"这类泛新闻挤掉。
  阿凤姐要点评的是**紫砂壶本身**的新闻（宜兴、泥料、造假、监管、拍卖、非遗、展会），
  所以单开一路抓取，带原文链接，点评时才敢落到具体事上。

产物：vault\\茶叶知识库\\12-新闻素材\\紫砂壶\\YYYY-MM-DD.md
去重：.teapot_news_seen.json 记 URL，同一件事不重复点评
"""
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

KB = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault\茶叶知识库")
OUT_DIR = KB / "12-新闻素材" / "紫砂壶"
SEEN = Path(r"C:\afeng_tea\.teapot_news_seen.json")
ENV = Path(r"C:\Users\Administrator\AppData\Local\hermes\.env")

QUERIES = [
    "紫砂壶 宜兴 最新消息",
    "紫砂 泥料 造假 查处",
    "紫砂壶 市场 监管 新闻",
    "紫砂 非遗 传承人 宜兴",
]


def _keys():
    out = []
    try:
        for line in ENV.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("TAVILY_API_KEY") and "=" in line:
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
                if v and v not in out:
                    out.append(v)
    except Exception:
        pass
    return out


def _norm_date(s):
    """Tavily 的 published_date 有时是 'Wed, 18 Nov 2026 …' 这种 RFC 格式"""
    s = (s or "").strip()
    if not s:
        return ""
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return m.group(0)
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return ""


def _search(key, query, days=7):
    body = json.dumps({
        "api_key": key, "query": query, "topic": "news",
        "days": days, "max_results": 10,
        "search_depth": "basic", "include_answer": False,
    }).encode()
    req = urllib.request.Request("https://api.tavily.com/search", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=50) as r:
        return json.loads(r.read().decode("utf-8")).get("results", [])


def _seen():
    if SEEN.exists():
        try:
            return json.loads(SEEN.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def fetch(save=True):
    """返回本次抓到的新条目列表 [{title, url, date, snippet}]"""
    keys = _keys()
    if not keys:
        print("⚠ 没找到 TAVILY key（hermes\\.env）")
        return []

    seen = set(_seen())
    items, tried = [], 0
    for q in QUERIES:
        res = None
        alt = list(keys[tried % len(keys):] + keys[:tried % len(keys)])
        for key in alt[:2]:                      # 遇到 401/超时换下一个 key
            try:
                res = _search(key, q)
                break
            except Exception as e:
                print(f"  ⚠ 搜索「{q}」失败（{type(e).__name__}），换 key 重试：{str(e)[:60]}")
        tried += 1
        if res is None:
            continue
        for r in res:
            url = (r.get("url") or "").strip()
            title = re.sub(r"\s+", " ", (r.get("title") or "")).strip()
            if not url or url in seen:
                continue
            # 标题必须像新闻、且明确讲紫砂/宜兴/壶（"彭sr在户外"这类垃圾条目挡在门外）
            if len(title) < 10:
                continue
            if not any(k in title for k in ("紫砂", "宜兴", "陶都", "泥料", "壶")):
                continue
            if re.search(r"(排行榜|京东|淘宝|天猫|1688|拼多多|旗舰店|优惠|券后|秒杀|包邮|卖家|促销|已售)", title):
                continue
            # 电商/导购站整站排除（它们的"新闻"其实是商品列表）
            if re.search(r"(taobao|tmall|jd\.com|1688|pinduoduo|suning|zhe800|smzdm|xiaohongshu)", url):
                continue
            body_txt = re.sub(r"\s+", " ", (r.get("content") or ""))
            if re.search(r"(卖家|￥|促销|包邮|已售|销量|优惠券|下单)", body_txt[:200]):
                continue
            # 掐掉站点名尾巴："—紫砂之家" "－紫砂壶·茶具·建盏·收藏精华" 这类导航标题
            if re.search(r"[—\-－_|｜].*(网|之家|商城|官网|首页|频道)$", title) or title.count("·") >= 2:
                continue
            title = re.split(r"\s*[—\-－_|｜]\s*(?:紫砂之家|宜兴.*网|.*官网|.*商城)", title)[0].strip()
            if len(title) < 10:
                continue
            pd = _norm_date(r.get("published_date"))
            if not pd:
                continue
            try:
                age = (datetime.now() - datetime.strptime(pd, "%Y-%m-%d")).days
                if age < 0 or age > 7:
                    continue
            except Exception:
                continue
            seen.add(url)
            items.append({
                "title": title[:120],
                "url": url,
                "date": pd,
                "snippet": re.sub(r"\s+", " ", (r.get("content") or ""))[:400],
            })

    if not items:
        print("  今天没有新的紫砂新闻（全部去重后为空）")
        return []

    items.sort(key=lambda x: x["date"], reverse=True)
    print(f"  ✓ 抓到 {len(items)} 条新紫砂新闻")
    for it in items[:5]:
        print(f"    · {it['date']} {it['title'][:52]}")

    if save:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        day = datetime.now().strftime("%Y-%m-%d")
        fp = OUT_DIR / f"{day}-紫砂壶新闻.md"
        lines = [f"# {day} 紫砂壶新闻（{len(items)} 条，Tavily 采集）", ""]
        for it in items:
            lines += [f"## {it['title']}", f"- 日期：{it['date']}", f"- 链接：{it['url']}",
                      f"- 摘要：{it['snippet']}", ""]
        fp.write_text("\n".join(lines), encoding="utf-8")
        SEEN.write_text(json.dumps(sorted(seen)[-600:], ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  已写入 {fp}")
    return items


if __name__ == "__main__":
    fetch()
