# -*- coding: utf-8 -*-
import re
p = r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault\资料库\素材材料\茶叶素材\2026-11-23-惠州东平周一清晨阿凤姐一壶蜜兰香先暖了晨练人的手.md"
t = open(p, encoding="utf-8").read()
def zh(s): return len(re.findall(r"[\u4e00-\u9fff]", s))
main = t.split("## FAQ")[0]
print("正文(标题+导语+六段)中文字数:", zh(main))
print("FAQ 中文字数:", zh(t.split("## FAQ")[1].split("## 标签")[0]))
print("全文:", zh(t))
