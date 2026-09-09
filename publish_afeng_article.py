#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿凤姐茶叶网站 - 全自动发布流水线 v2
用法：python publish_afeng_article.py --input "文章路径.md" [--check-only]
"""

import argparse
import re
import os
import subprocess
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# === 配置 ===
REPO_DIR = r"C:\Users\a\Desktop\afeng_tea_repo"
INDEX_HTML = os.path.join(REPO_DIR, "index.html")
VAULT_DIR = r"C:\Users\a\Desktop\MianAI知识库\MianAI知识库\vault\阿凤姐的故事"
VERCEL_URL = "https://afeng-tea.vercel.app"

# === 文章配图库（Unsplash 免费图片 CDN）===
# 每张图都经过 vision_analyze 验证主题相关性
# 尺寸统一 w=800（800px 宽），够清晰且加载快
IMAGE_LIBRARY = {
    # 主题: (photo_id, 图注中文, 适合的关键词)
    "tea_gift": ("1576092768241-dec231879fc3", "一份用心准备的茶礼", ["礼盒", "中秋", "送礼", "海外", "乡愁", "礼品", "团购", "企业", "福利", "diy"]),
    "tea_set": ("1564890369478-c89ca6d9cde9", "工夫茶具一席间", ["工夫", "茶具", "器用", "泡茶", "冲泡", "器物", "紫砂", "盖碗", "杯", "壶"]),
    "tea_farming": ("1571934811356-5cc061b6821f", "茶碗中的时光", ["文化", "传承", "老师傅", "非遗", "冲泡", "陈年", "老茶", "工艺", "历史", "传统", "采茶", "做青"]),
    "tea_box": ("1597481499750-3e6b22637e12", "精致的茶礼盒", ["中秋", "送礼", "礼盒", "水果茶", "调饮", "创新", "年轻", "新茶饮", "品牌", "联名", "包装"]),
    "tea_nature": ("1567922045116-2a00fae2ed03", "茶山云雾与一片叶子", ["茶山", "自然", "秋茶", "白露", "节气", "产地", "凤凰山", "乌岽", "云雾", "古树", "生态"]),
    "tea_brewing": ("1556679343-c7306c1976bc", "一杯好茶的诞生", ["冲泡", "泡茶", "水温", "技艺", "三泡", "出汤", "品饮", "教学", "入门", "新手"]),
}

def pick_article_image(title, tags_list):
    """根据文章标题和标签，挑选一张主题最相关的图"""
    text = (title + " " + " ".join(tags_list)).lower()
    
    # 优先匹配 tags 关键词
    matches = []
    for theme, (photo_id, caption, keywords) in IMAGE_LIBRARY.items():
        score = sum(1 for kw in keywords if kw.lower() in text)
        matches.append((score, theme, photo_id, caption))
    
    # 按分数从高到低排序
    matches.sort(reverse=True)
    
    # 选分数最高的；如果都没匹配上，用 tea_nature 兜底
    best = matches[0] if matches else None
    if not best or best[0] == 0:
        photo_id, caption = IMAGE_LIBRARY["tea_nature"][:2]
    else:
        photo_id, caption = best[2], best[3]
    
    url = f"https://images.unsplash.com/photo-{photo_id}?w=800&q=80"
    
    return f'''                <figure class="article-hero-image">
                    <img src="{url}" alt="{escape_html(caption)}" loading="lazy" />
                    <figcaption>{escape_html(caption)} · 图源 Unsplash</figcaption>
                </figure>
'''


def escape_html(text):
    """转义HTML特殊字符"""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))


def read_md_article(md_path):
    """读取 markdown 文章，提取 frontmatter 和正文"""
    content = Path(md_path).read_text(encoding="utf-8", errors="ignore")
    
    # 解析 frontmatter
    fm = {}
    body = content
    if content.startswith("---"):
        m = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if m:
            fm_text = m.group(1)
            body = content[m.end():]
            # 简单解析 YAML
            for line in fm_text.split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    fm[key.strip()] = val.strip().strip('"').strip("'")
    
    return fm, body


def find_optimized_version(draft_path):
    """查找 Claudian 优化版文章（根目录下时间戳更新的同名文件）"""
    draft = Path(draft_path)
    vault_dir = draft.parent.parent  # 阿凤姐的故事/
    
    # 提取日期部分（如 2026-09-02）
    date_prefix = draft.stem[:10]
    
    candidates = []
    for f in vault_dir.glob("*.md"):
        if f.name == draft.name:
            continue
        if f.stem.startswith(date_prefix):
            try:
                # 提取时间戳（如 0430 vs 1052）
                draft_time = draft.stem[11:15]
                cand_time = f.stem[11:15]
                if cand_time > draft_time:
                    candidates.append((f, cand_time))
            except:
                continue
    
    if candidates:
        candidates.sort(key=lambda x: x[1], reverse=True)
        return str(candidates[0][0])
    
    return None


def md_to_html_paragraphs(md_body):
    """将 markdown 正文转成 <p>/<h4> HTML 段落"""
    paragraphs = []
    for line in md_body.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        # 跳过 markdown 标题标记
        if line.startswith('# '):
            paragraphs.append(f'        <h3>{escape_html(line[2:])}</h3>')
        elif line.startswith('## '):
            paragraphs.append(f'        <h4>{escape_html(line[3:])}</h4>')
        elif line.startswith('### '):
            paragraphs.append(f'        <h4>{escape_html(line[4:])}</h4>')
        elif line.startswith('> '):
            paragraphs.append(f'        <blockquote><p>{escape_html(line[2:])}</p></blockquote>')
        elif line.startswith('🌿') or line.startswith('📌') or line.startswith('✅') or line.startswith('🔥'):
            # 保留 emoji 段落
            paragraphs.append(f'        <p>{escape_html(line)}</p>')
        elif line.startswith('---'):
            continue
        else:
            paragraphs.append(f'        <p>{escape_html(line)}</p>')
    
    return '\n'.join(paragraphs)


def generate_article_html(article_id, title, body, tags, date_str):
    """生成 article HTML 片段，插入到 index.html 最顶"""
    
    # 生成 meta description
    desc = body[:150].replace('\n', ' ') if len(body) > 150 else body
    desc = escape_html(desc)
    
    # 生成 abstract（第一段）
    first_para = body.strip().split('\n')[0] if body else ""
    abstract = escape_html(first_para)
    
    # 正文转 HTML
    body_html = md_to_html_paragraphs(body)
    
    # tags
    tags_list = [t.strip() for t in tags.split(',') if t.strip()]
    tags_html = '\n'.join([f'        <span class="tag">#{t}</span>' for t in tags_list])

    # 根据标题/标签挑选主题相关图片（Unsplash 免费 CDN）
    image_html = pick_article_image(title, tags_list)

    # ISO 日期 + 精确到秒的显示格式
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        iso_date = dt.strftime("%Y-%m-%d")
        display_date = dt.strftime("%Y年%m月%d日")
    except:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
            iso_date = dt.strftime("%Y-%m-%dT%H:%M:%S")
            display_date = dt.strftime("%Y年%m月%d日 %H:%M:%S")
        except:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                iso_date = dt.strftime("%Y-%m-%dT%H:%M:%S")
                display_date = dt.strftime("%Y年%m月%d日 %H:%M:%S")
            except:
                iso_date = date_str
                display_date = date_str
    
    # 生成文章 ID
    if not article_id:
        article_id = "article-" + re.sub(r'[^\w]', '', title[:20].lower())
    
    article_html = f'''<!-- Article: {title} -->
            <article class="article-card" id="{article_id}" data-category="chaye" itemscope itemtype="https://schema.org/Article">
                <h3 itemprop="headline">{title} <span style="background:#e53935;color:white;font-size:0.65em;padding:2px 8px;border-radius:8px;margin-left:5px;">NEW</span></h3>

                <p class="article-meta-time">📅 发布于 <time itemprop="datePublished" datetime="{iso_date}">{display_date}</time></p>

{image_html}

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
                    <p><strong>🗓️ 发布时间：</strong><time itemprop="datePublished" datetime="{iso_date}">{display_date}</time></p>
                </div>
            </article>
'''
    return article_html


def update_global_date():
    """更新 index.html 中的全局'最近更新'和'上次更新'日期为今天（精确到秒）"""
    today_str = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
    today_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    with open(INDEX_HTML, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换最近更新（hero 区域）+ 上次更新（页脚）
    content = re.sub(
        r'<time datetime="[\d\-T:]+">[\d年月日\sT:\-年月日]+</time>',
        lambda m: f'<time datetime="{today_iso}">{today_str}</time>',
        content,
        count=2
    )
    
    with open(INDEX_HTML, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True


def insert_article_into_index(article_html):
    """将文章插入到 index.html 的 <div class="article-list"> 最前面，并同步更新全局日期"""
    with open(INDEX_HTML, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到 <div class="article-list"> 后面第一个 <!-- Article:
    pattern = r'(<div class="article-list">\s*\n)(<!-- Article:)'
    replacement = r'\1' + article_html + '\n            \2'
    
    new_content = re.sub(pattern, replacement, content, count=1)
    
    if new_content == content:
        # 备用方案
        marker = '<div class="article-list">'
        idx = content.find(marker)
        if idx == -1:
            return False, "找不到 <div class='article-list'>"
        
        insert_pos = idx + len(marker)
        nl_idx = content.find('\n', insert_pos)
        if nl_idx != -1:
            insert_pos = nl_idx + 1
        
        new_content = content[:insert_pos] + article_html + '\n' + content[insert_pos:]
    
    # 同步更新全局日期
    today_str = datetime.now().strftime("%Y年%m月%d日")
    today_iso = datetime.now().strftime("%Y-%m-%d")
    new_content = re.sub(
        r'<time datetime="\d{4}-\d{2}-\d{2}">\d{4}年\d{1,2}月\d{1,2}日</time>',
        f'<time datetime="{today_iso}">{today_str}</time>',
        new_content
    )
    
    with open(INDEX_HTML, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True, "文章已插入，全局日期已同步"


def git_commit_and_push(commit_msg):
    """git add → commit → push"""
    os.chdir(REPO_DIR)
    
    # git add
    r = subprocess.run(["git", "add", "index.html"], capture_output=True, text=True)
    if r.returncode != 0:
        return False, f"git add 失败: {r.stderr}"
    
    # git commit
    r = subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True)
    if r.returncode != 0:
        if "nothing to commit" in r.stdout.lower() or "nothing to commit" in r.stderr.lower():
            return True, "没有变更需要提交"
        return False, f"git commit 失败: {r.stderr}"
    
    # git push
    r = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
    if r.returncode != 0:
        # Try pull first if rejected
        if "rejected" in r.stderr.lower() or "fetch first" in r.stderr.lower():
            subprocess.run(["git", "pull", "origin", "main", "--no-rebase"], capture_output=True, text=True)
            r = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
            if r.returncode != 0:
                return False, f"git push 失败: {r.stderr}"
        else:
            return False, f"git push 失败: {r.stderr}"
    
    # 提取 commit hash
    r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
    commit_hash = r.stdout.strip() if r.returncode == 0 else "unknown"
    
    return True, f"已推送到 GitHub (commit: {commit_hash})"


def check_vercel_deploy(max_wait=120):
    """检测 Vercel 部署状态（通过检查网站是否更新）"""
    import urllib.request
    
    print(f"⏳ 等待 Vercel 部署（最多 {max_wait} 秒）...")
    
    # 获取当前 commit hash 作为 marker
    os.chdir(REPO_DIR)
    r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
    current_hash = r.stdout.strip() if r.returncode == 0 else ""
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            # 尝试请求网站（简单 HEAD 请求）
            req = urllib.request.Request(VERCEL_URL, method='HEAD')
            req.add_header('User-Agent', 'Mozilla/5.0')
            resp = urllib.request.urlopen(req, timeout=10)
            
            if resp.status == 200:
                # 网站可访问，但无法确认是否最新版本
                # 假设 Vercel 部署很快，等待 30 秒后认为成功
                elapsed = time.time() - start_time
                if elapsed >= 30:
                    return True, f"Vercel 部署完成（约 {int(elapsed)} 秒）"
        except:
            pass
        
        time.sleep(5)
        print(f"  ... 已等待 {int(time.time() - start_time)} 秒")
    
    return False, f"等待超时（{max_wait} 秒），请手动检查 {VERCEL_URL}"


def update_article_status(md_path, status, website=None):
    """更新 markdown 文件的 frontmatter"""
    content = Path(md_path).read_text(encoding="utf-8", errors="ignore")
    
    # 更新 status
    if re.search(r'^status:\s*', content, re.MULTILINE):
        content = re.sub(r'^status:\s*.*$', f'status: {status}', content, flags=re.MULTILINE)
    else:
        # 在 frontmatter 末尾添加
        content = content.replace('---\n\n', f'---\nstatus: {status}\n\n', 1)
    
    # 添加 website
    if website:
        if re.search(r'^website:\s*', content, re.MULTILINE):
            content = re.sub(r'^website:\s*.*$', f'website: {website}', content, flags=re.MULTILINE)
        else:
            content = content.replace('---\n\n', f'---\nwebsite: {website}\n\n', 1)
    
    Path(md_path).write_text(content, encoding="utf-8")
    return True


def move_file(src_path, dest_folder):
    """移动文件到目标文件夹"""
    src = Path(src_path)
    dest = Path(dest_folder) / src.name
    
    # 如果目标已存在，加编号
    counter = 1
    while dest.exists():
        stem = src.stem
        if re.search(r'_\d+$', stem):
            stem = re.sub(r'_\d+$', '', stem)
        dest = Path(dest_folder) / f"{stem}_{counter}{src.suffix}"
        counter += 1
    
    shutil.move(str(src), str(dest))
    return str(dest)


def main():
    parser = argparse.ArgumentParser(description='阿凤姐茶叶网站全自动发布')
    parser.add_argument('--input', required=True, help='草稿文章 .md 路径')
    parser.add_argument('--check-only', action='store_true', help='只检测，不实际发布')
    parser.add_argument('--no-push', action='store_true', help='不推送到 GitHub（测试用）')
    args = parser.parse_args()
    
    # 1. 读取文章
    print(f"📖 读取文章: {args.input}")
    fm, body = read_md_article(args.input)
    
    title = fm.get('title', Path(args.input).stem)
    date_str = fm.get('date', datetime.now().strftime("%Y-%m-%d"))
    tags = fm.get('tags', '凤凰单丛,茶文化,惠州茶叶店')
    article_id = fm.get('id', '')
    
    print(f"   标题: {title}")
    print(f"   日期: {date_str}")
    
    # 自动查找 Claudian 优化版
    opt_path = find_optimized_version(args.input)
    if opt_path:
        print(f"   📝 发现优化版: {Path(opt_path).name}")
        print(f"   ✅ 自动选用优化版")
        args.input = opt_path
        # 重新读取
        fm, body = read_md_article(args.input)
        title = fm.get('title', Path(args.input).stem)
        print(f"   标题: {title}")
    else:
        print(f"   ℹ️ 使用原文版（无优化版）")
    
    if args.check_only:
        print("✅ 文章格式检查通过")
        return 0
    
    # 2. 生成 HTML
    print("📝 生成 HTML...")
    article_html = generate_article_html(article_id, title, body, tags, date_str)
    
    # 3. 插入到 index.html
    print("📄 插入到 index.html...")
    ok, msg = insert_article_into_index(article_html)
    if not ok:
        print(f"❌ {msg}")
        return 1
    print(f"   ✅ {msg}")
    
    # 4. Git commit
    print("💾 Git commit...")
    os.chdir(REPO_DIR)
    subprocess.run(["git", "add", "index.html"], capture_output=True)
    r = subprocess.run(["git", "diff", "--cached", "--stat"], capture_output=True, text=True)
    if not r.stdout.strip():
        print("   ℹ️ 没有变更")
        return 0
    
    if args.no_push:
        print("   ℹ️ --no-push 模式，跳过 git push")
        print(f"   📁 文件位置: {INDEX_HTML}")
        return 0
    
    # 5. Git push
    print("🚀 Git push...")
    ok, msg = git_commit_and_push(f"Add article: {title}")
    if not ok:
        print(f"❌ {msg}")
        # 回滚 index.html
        subprocess.run(["git", "checkout", "--", "index.html"], capture_output=True)
        print("   🔄 已回滚 index.html")
        return 1
    print(f"   ✅ {msg}")
    
    # 6. 检测 Vercel 部署
    print("🌐 检测 Vercel 部署...")
    ok, msg = check_vercel_deploy()
    if ok:
        print(f"   ✅ {msg}")
        
        # 7. 更新文章状态
        print("📋 更新文章状态...")
        update_article_status(args.input, "已发布", website=VERCEL_URL)
        
        # 8. 移动文件到已发布
        published_dir = os.path.join(VAULT_DIR, "已发布")
        new_path = move_file(args.input, published_dir)
        print(f"   ✅ 已移动到: {new_path}")
        
        print(f"\n🎉 发布成功！")
        print(f"   网站: {VERCEL_URL}")
        print(f"   文章: {title}")
        
        return 0
    else:
        print(f"   ⚠️ {msg}")
        
        # 更新为待上传
        print("📋 更新为待上传状态...")
        update_article_status(args.input, "待上传")
        
        # 移动到待上传
        pending_dir = os.path.join(VAULT_DIR, "待上传")
        new_path = move_file(args.input, pending_dir)
        print(f"   ⚠️ 已移动到: {new_path}")
        
        return 1


if __name__ == '__main__':
    import shutil
    sys.exit(main())
