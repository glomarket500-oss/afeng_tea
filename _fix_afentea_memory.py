# -*- coding: utf-8 -*-
"""整理 afen-tea profile 的记忆：
1) 清掉 QQ 号 / 旧域名 / 真名（红线）
2) 追加 2026-11-17 的交接档案（当前真实状态）
"""
import re
from pathlib import Path

P = Path(r"C:\Users\Administrator\AppData\Local\hermes\profiles\afen-tea\memories\MEMORY.md")
txt = P.read_text(encoding="utf-8")
orig_len = len(txt)

# ---- 1) 红线清洗 ----
before = txt

# QQ 号（各种写法）
txt = re.sub(r"[，,、\s]*(?:QQ|qq|Qq)\s*[:：]?\s*1079790744", "", txt)
txt = txt.replace("1079790744", "")
# 旧域名
txt = txt.replace("https://afeng-tea.vercel.app/", "https://feng-tea.com")
txt = txt.replace("https://afeng-tea.vercel.app", "https://feng-tea.com")
# 真名
txt = txt.replace("林玉凤（阿凤姐）", "阿凤姐").replace("林玉鳳（阿鳳姐）", "阿鳳姐")
txt = txt.replace("Lin Yufeng/林玉凤", "阿凤姐").replace("林玉凤", "阿凤姐").replace("林玉鳳", "阿鳳姐")

# 清理因删除产生的空标点
txt = re.sub(r"联系方式：\s*📱\s*13435567385\s*，\s*地址", "联系方式：13435567385，地址", txt)
txt = re.sub(r"[，,]\s*[，,]", "，", txt)

cleaned = before != txt
print(f"红线清洗: {'✓ 有改动' if cleaned else '（无需改动）'}")
print(f"  QQ 残留: {txt.count('1079790744')}")
print(f"  真名残留: {txt.count('林玉凤') + txt.count('林玉鳳')}")
print(f"  旧域名残留: {txt.count('afeng-tea.vercel.app')}")

# ---- 2) 追加交接档案 ----
ARCHIVE = """

§
【2026-11-17 交接档案 · 由默认 profile 交接】
本 profile 负责：茶叶网站 https://feng-tea.com 的全部内容工作（写稿、编辑、配图、建页、发布、上线复核）。仓库 glomarket500-oss/afeng_tea，Vercel 自动部署。

知识库（唯一权威副本，先查再答）：
C:\\Users\\Administrator\\Desktop\\MianAI知识库\\MianAI知识库\\vault\\茶叶知识库\\
14 篇笔记，入口 00-总索引.md；每日新闻在 12-新闻素材\\YYYY-MM\\；检索 python kb_search.py <关键词>

素材库：...\\vault\\资料库\\素材材料\\茶叶素材\\（242 篇，每日发文从这里取稿）

流水线脚本（C:\\afeng_tea\\）：publish_new.py（九步：解析/生图/像素检测/建页/首页首卡/sitemap/页脚/推送/线上复核）、publish_daily.py、publish_weekly.py、next_draft.py（含 BAN_WORDS 陈皮过滤）

定时任务（现由默认 profile 运行，跑通后再迁入本 profile）：
03:30 采集真实新闻进知识库 → 07:00 写稿（晨语）→ 09:00 每日发文上线 → 周日 02:00 周评写稿 → 周日 20:25 周评上线

铁律：
1. 本站是茶叶站，陈皮/新会/柑普题材一律不生成、不推送、不上线
2. 文章绝不出现真名"林玉凤"、QQ、手机号；一律写"阿凤姐"
3. 只用免费配图模型 Kwai-Kolors/Kolors，付费模型禁用
4. 已上线文章一律不回改，站方自己检测修改
5. 改页面结构（布局/栅格/断点/栏位）前必须先问站方
6. 推送前必须以 origin/main 最新版为基准，不许在分叉仓库 push
7. 说"做好了"必须有实测证据（HTTP 状态、字节数、卡片数、图片尺寸）
8. 付费 LLM 任务尽量排在闲时 00:30–08:30
"""

if "2026-11-17 交接档案" not in txt:
    txt = txt.rstrip() + ARCHIVE
    print("交接档案: ✓ 已追加")
else:
    print("交接档案: 已存在，跳过")

P.write_text(txt, encoding="utf-8")
print(f"\n记忆文件: {orig_len} → {len(txt)} 字符")
