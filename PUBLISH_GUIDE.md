# 阿凤姐茶网站 - 全自动发布工具

## 用法

### 1. 准备文章
把文章内容整理好，每段之间用空行分隔。

### 2. 运行发布脚本

```bash
# 写入文章但不推送（测试用）
python publish_article.py \
  --title "🍵 阿凤姐夜话｜XXXXX" \
  --id "article-xxxxxx" \
  --category chaye \
  --tags "凤凰单丛,茶文化,惠州茶叶店" \
  --body "第一段正文。\n\n第二段正文。\n\n## 第三段标题\n\n第三段内容。"

# 写入并自动推送到 GitHub（需要配置 Token）
python publish_article.py \
  --title "🍵 阿凤姐夜话｜XXXXX" \
  --id "article-xxxxxx" \
  --category chaye \
  --tags "凤凰单丛,茶文化,惠州茶叶店" \
  --body "第一段正文。\n\n第二段正文。" \
  --push
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--title` | ✅ | 文章标题 |
| `--id` | ✅ | 唯一标识（英文，如 `article-yashixiang`） |
| `--body` | ✅ | 正文内容，段落用 `\n\n` 分隔 |
| `--category` | | 分类：`chaye`(茶文化) / `jieri`(节日) / `qiju`(茶具) / `pinzhong`(品种) / `paocha`(泡茶) |
| `--tags` | | 标签，逗号分隔 |
| `--date` | | 发布日期，默认今天 |
| `--push` | | 加这个参数会自动推送到 GitHub |

### 3. GitHub Token 配置（只需一次）

运行以下命令配置 HTTPS Token（替换 YOUR_TOKEN）：

```bash
git remote set-url origin https://YOUR_TOKEN@github.com/glomarket500-oss/afeng_tea.git
```

之后 `--push` 就能自动推送到 GitHub，Vercel 自动部署。

## 文章分类对照

- `chaye` 💭 茶文化（默认）
- `jieri` 🎁 节日专题
- `qiju` 🫖 茶具器用
- `pinzhong` 🌿 茶叶品种
- `paocha` 🍵 泡茶技巧
