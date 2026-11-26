# -*- coding: utf-8 -*-
import re, sys
p = r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault\资料库\素材材料\茶叶素材\2026-11-23-惠州东平周一清晨阿凤姐一壶蜜兰香先暖了晨练人的手.md"
t = open(p, encoding="utf-8").read()
bad = ["林玉凤", "林玉鳳", "陈皮", "陳皮", "新会", "柑普", "小青柑", "13435567385", "微信同号", "QQ", "电话", "手机"]
hits = [b for b in bad if b in t]
print("红线:", "OK 无违规词" if not hits else ("命中 -> " + str(hits)))
body = t.split("## 标签")[0]
print("正文中文字数(含FAQ):", len(re.findall(r"[\u4e00-\u9fff]", body)))
print("全文中文字数:", len(re.findall(r"[\u4e00-\u9fff]", t)))
print("FAQ组数:", t.count("**Q："))
tagsec = t.split("## 标签")[1].split("## 联系方式")[0]
print("标签数:", len(re.findall(r"#\S+", tagsec)))
print("必含标签:", "#惠州茶叶店" in t, "#惠州买茶去哪" in t)
print("段落标题:", re.findall(r"^## 【[^】]+】", t, flags=re.M))
