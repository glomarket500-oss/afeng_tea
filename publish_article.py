#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿凤姐茶网站 - 全自动文章发布流水线
用法：python publish_article.py --title "文章标题" --body "文章内容" --category chaye
"""

import argparse
import re
import os
import subprocess
import sys
from datetime import datetime

REPO_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "afeng_tea_repo")
INDEX_HTML = os.path.join(REPO_DIR, "index.html")

def escape_html(text):
    """转义HTML特殊字符"""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def generate_article_html(article_id, title, body, category, tags, date_str):
    """
    根据网站模板生成 article HTML 片段
    """
    # 生成 meta description（前150字）
    desc = body[:150].replace("\n", " ") + "..." if len(body) > 150 else body
    desc = escape_html(desc)
    
    # 生成 abstract（第一段作为导读摘要）
    first_para = body.split("\n")[0] if body else ""
    abstract = escape_html(first_para)
    
    # 把正文按段落拆分成 <p> 标签
    body_paragraphs = []
    for para in body.strip().split("\n"):
        para = para.strip()
        if not para:
            continue
        # 处理标题行（以 # 或 ## 开头）
        if para.startswith("## "):
            body_paragraphs.append(f'        <h4>{escape_html(para[3:])}</h4>')
        elif para.startswith("# "):
            body_paragraphs.append(f'        <h3>{escape_html(para[2:])}</h3>')
        else:
            body_paragraphs.append(f'        <p>{escape_html(para)}</p>')
    
    body_html = "\n".join(body_paragraphs)
    
    # 生成 tags HTML
    tags_html = "\n".join([f'        <span class="tag">#{t}</span>' for t in tags])
    
    # ISO 日期格式
    iso_date = datetime.strptime(date_str, "%Y年%m月%d日").strftime("%Y-%m-%d")
    
    article_html = f'''<!-- Article: {title} -->
            <article class="article-card" id="{article_id}" data-category="{category}" itemscope itemtype="https://schema.org/Article">
                <h3 itemprop="headline">{title} <span style="background:#e53935;color:white;font-size:0.65em;padding:2px 8px;border-radius:8px;margin-left:5px;">NEW</span></h3>

                <meta itemprop="description" content="{desc}">

                <p itemprop="abstract"><strong>【开篇导读】</strong>{abstract}</p>

                <div itemprop="articleBody">
{body_html}
                </div>

                <div class="tags" itemprop="keywords">
{tags_html}
                </div>

                <div class="author-box" itemprop="author" itemscope itemtype="https://schema.org/Person">
                    <p><strong>✍️ 作者：</strong><span itemprop="name">阿凤姐（林玉凤）</span>，<span itemprop="description">惠州茶叶店主理人，专注潮州凤凰单丛与新会陈皮</span></p>
                    <p><strong>🏪 店铺：</strong>阿凤姐茶叶店（惠州东平老茶街）</p>
                    <p><strong>📍 地址：</strong>惠州市惠城区东湖花园一区沿江商铺89-136（凤凰茶业）</p>
                    <p><strong>📱 电话：</strong>13435567385 | <strong>💬 QQ：</strong>1079790744</p>
                    <p><strong>⏰ 营业时间：</strong>每天9:00-21:00，全年无休</p>
                    <p><strong>🗓️ 发布时间：</strong><time itemprop="datePublished" datetime="{iso_date}">{date_str}</time></p>
                </div>
            </article>
'''
    return article_html

def insert_article_into_index(article_html):
    """
    将文章插入到 index.html 的 <div class="article-list"> 最前面
    """
    with open(INDEX_HTML, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到 <div class="article-list"> 后面第一个 <!-- Article: 注释
    pattern = r'(<div class="article-list">\s*\n)(<!-- Article:)'
    replacement = r'\1' + article_html + '\n' + r'            \2'
    
    new_content = re.sub(pattern, replacement, content, count=1)
    
    # 检查是否插入成功
    if new_content == content:
        # 备用方案：直接在 <div class="article-list"> 后面插入
        marker = '<div class="article-list">'
        idx = content.find(marker)
        if idx == -1:
            print("ERROR: 找不到 <div class='article-list'>")
            return False
        
        insert_pos = idx + len(marker)
        # 找到该标记后面的换行符
        nl_idx = content.find('\n', insert_pos)
        if nl_idx != -1:
            insert_pos = nl_idx + 1
        
        new_content = content[:insert_pos] + article_html + '\n' + content[insert_pos:]
    
    with open(INDEX_HTML, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ 文章已插入到 {INDEX_HTML}")
    return True

def git_commit_and_push(commit_msg):
    """
    git add → commit → push
    需要配置好 GitHub Token 才能 push
    """
    os.chdir(REPO_DIR)
    
    # git add
    result = subprocess.run(["git", "add", "index.html"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"⚠️ git add 警告: {result.stderr}")
    
    # git commit
    result = subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True)
    if result.returncode != 0:
        if "nothing to commit" in result.stdout.lower() or "nothing to commit" in result.stderr.lower():
            print("ℹ️ 没有变更需要提交")
            return True
        print(f"❌ git commit 失败: {result.stderr}")
        return False
    
    print(f"✅ 已提交: {commit_msg}")
    
    # git push (需要 token 配置好 HTTPS 或 SSH)
    result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ git push 失败: {result.stderr}")
        print("💡 提示: 请检查 GitHub Token 是否已配置")
        return False
    
    print("🚀 已推送到 GitHub，Vercel 将自动部署！")
    return True

def main():
    parser = argparse.ArgumentParser(description='阿凤姐茶网站文章发布工具')
    parser.add_argument('--title', required=True, help='文章标题')
    parser.add_argument('--body', required=True, help='文章正文（段落用\\n分隔）')
    parser.add_argument('--id', required=True, help='文章ID（英文唯一标识，如 article-yashixiang）')
    parser.add_argument('--category', default='chaye', 
                        choices=['chaye', 'jieri', 'qiju', 'pinzhong', 'paocha'],
                        help='文章分类')
    parser.add_argument('--tags', default='凤凰单丛,茶文化,惠州茶叶店', help='标签，逗号分隔')
    parser.add_argument('--date', default=datetime.now().strftime('%Y年%m月%d日'), help='发布日期')
    parser.add_argument('--push', action='store_true', help='是否自动推送到 GitHub')
    
    args = parser.parse_args()
    
    tags = [t.strip() for t in args.tags.split(",")]
    
    # 生成文章 HTML
    article_html = generate_article_html(
        article_id=args.id,
        title=args.title,
        body=args.body,
        category=args.category,
        tags=tags,
        date_str=args.date
    )
    
    # 插入到 index.html
    if not insert_article_into_index(article_html):
        sys.exit(1)
    
    # 自动推送（需要 Token 配置好）
    if args.push:
        commit_msg = f"Add article: {args.title} ({args.date})"
        git_commit_and_push(commit_msg)
    else:
        print("ℹ️ 文章已写入本地 index.html，运行命令时加 --push 可自动推送到 GitHub")
        print(f"📁 文件位置: {INDEX_HTML}")

if __name__ == '__main__':
    main()
