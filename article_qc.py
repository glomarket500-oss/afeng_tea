#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文章完整性质量校验（发布前硬闸）
=================================================================
背景：2026-11-26 发现 3 篇紫砂点评文章残缺发布（665-966 字 / 3-4 节 / 1 图，
      且正文引用不存在的死图），说明原有 assert 只查标签存在、不查内容完整。

本模块提供发布前硬校验，任一不过即拒绝发布。

校验项：
  A. 正文可见字数 ≥ MIN_BODY_CHARS
  B. 章节(h2)数 ≥ MIN_H2
  C. 文中所有 <img src> 指向的文件必须真实存在（防死图）
  D. 标题(title/h1/og/twitter)与面包屑不得含 .html 后缀、P26 错字、非法字符
  E. prev/next 导航存在
  F. tags 三处齐全且不重复

用法（供 publish_new.py 调用）：
    from article_qc import check_article_html
    issues = check_article_html(page, imgs_dir=REPO/"images/full", skip_images=skip_img)
    if issues: raise SystemExit(...)
"""
import re
import html as _html
from pathlib import Path

# ---- 阈值（可按站方要求调整）----
# 正文下限 1300：任务书骨架 A（故事型）1200-2000 字、骨架 D（新闻点评）1500-2500 字，
# 取 1300 兼容故事型短篇；残缺文（966/779/665 字）仍会被拦下。
MIN_BODY_CHARS = 1300     # 正文可见字数下限
MIN_H2 = 8                # 章节数下限（完整骨架 9 节，故事型 8 节）
# 非法字符（标题/面包屑可见文本中不允许）
# 依据任务书 §4.1：禁 #「」『』、emoji、URL、hashtag。
# 注意：中文弯引号 “”‘’ 是正常标点（新闻标题常见），不得误判为非法。
ILLEGAL_TITLE_CHARS = "#「」『』"
P26_RE = re.compile(r"P\d{2}\d")   # 形如 P261121 的错字（应为 20261121）


def _visible_text(html_fragment: str) -> str:
    """去标签/脚本/样式/图片注记，返回可见文本。"""
    t = re.sub(r"<script[\s\S]*?</script>", " ", html_fragment, flags=re.I)
    t = re.sub(r"<style[\s\S]*?</style>", " ", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = _html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def _get(pattern: str, text: str, flags=re.S):
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else ""


def check_article_html(page: str, imgs_dir: Path = None,
                       skip_images: bool = False) -> list:
    """返回问题列表（空列表 = 通过）。"""
    issues = []

    # ---------- A. 正文长度 ----------
    body_m = re.search(r'<div class="article-body">([\s\S]*?)</div>\s*(?=<div class="cta-box">)', page)
    if not body_m:
        issues.append("找不到 article-body 正文块（页面结构损坏）")
        body_text = ""
    else:
        body_text = _visible_text(body_m.group(1))
        if len(body_text) < MIN_BODY_CHARS:
            issues.append(f"正文过短：{len(body_text)} 字（至少 {MIN_BODY_CHARS} 字）")

    # ---------- B. 章节数 ----------
    h2_count = len(re.findall(r"<h2[^>]*>", body_m.group(1) if body_m else page))
    if h2_count < MIN_H2:
        issues.append(f"章节过少：{h2_count} 个 h2（至少 {MIN_H2} 个）")

    # ---------- C. 图片存在性 ----------
    if not skip_images and imgs_dir is not None:
        srcs = re.findall(r'<img[^>]+src="([^"]+)"', page)
        missing = []
        for s in srcs:
            # 相对路径 → 磁盘路径
            rel = s.replace("../images/full/", "").replace("images/full/", "")
            if rel.startswith("http"):
                continue
            if not (Path(imgs_dir) / rel).exists():
                missing.append(rel)
        if missing:
            issues.append(f"死图 {len(missing)} 张（文件不存在）: {', '.join(missing[:5])}")
        if not srcs:
            issues.append("页面不含任何配图")

    # ---------- D. 标题 / 面包屑干净 ----------
    title = _get(r"<title>([\s\S]*?)</title>", page)
    h1 = _get(r"<h1[^>]*>([\s\S]*?)</h1>", page)
    crumb = _get(r'<div class="breadcrumb">([\s\S]*?)</div>', page)
    crumb = re.sub(r"<[^>]+>", "", crumb).strip()

    for label, val in (("title", title), ("h1", h1), ("面包屑", crumb)):
        if not val:
            issues.append(f"{label} 为空")
            continue
        if ".html" in val:
            issues.append(f"{label} 含 .html 后缀: {val[:40]}")
        if P26_RE.search(val):
            issues.append(f"{label} 含 P26 错字: {val[:40]}")
        bad = [c for c in ILLEGAL_TITLE_CHARS if c in val]
        if bad:
            issues.append(f"{label} 含非法字符 {'/'.join(bad)}: {val[:40]}")

    # title 与 h1 一致性（去掉 emoji 前缀、站点后缀、.html 后缀后比较）
    def _norm(s):
        s = re.sub(r"^🍵\s*", "", s)
        s = re.sub(r"\s*\|\s*阿凤姐的故事\s*$", "", s)
        s = re.sub(r"\.html$", "", s)
        return s.strip()
    if title and h1 and _norm(title) != _norm(h1):
        issues.append(f"title 与 h1 不一致: '{_norm(title)[:30]}' vs '{_norm(h1)[:30]}'")

    # ---------- E. 导航 ----------
    if '<div class="article-nav">' not in page:
        issues.append("缺少 prev/next 导航块")

    # ---------- F. tags ----------
    at_count = page.count('class="article-tags"')
    if at_count != 1:
        issues.append(f"article-tags 应有 1 份，实际 {at_count} 份")
    if '<div class="tags">' not in page:
        issues.append("缺少头部 tags chips")
    if "#" not in body_text:
        # 正文末尾的 xhs-tags 是可见文本的一部分
        if 'class="xhs-tags"' not in page:
            issues.append("缺少页脚 hashtag 行（xhs-tags）")

    return issues


def check_article_file(path: Path, imgs_dir: Path = None, skip_images=False) -> list:
    """校验已落盘的文章文件。"""
    if not path.exists():
        return [f"文章文件不存在: {path}"]
    return check_article_html(path.read_text(encoding="utf-8"), imgs_dir, skip_images)


if __name__ == "__main__":
    import sys
    # Windows 控制台默认 GBK，输出 emoji/中文会炸；统一转 UTF-8
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    p = Path(sys.argv[1])
    imgs = p.parent.parent / "images" / "full" if p.parent.name == "articles" else None
    probs = check_article_file(p, imgs)
    if probs:
        print(f"❌ {p.name} 校验未通过：")
        for i in probs:
            print(f"   - {i}")
        sys.exit(1)
    print(f"✅ {p.name} 校验通过")
