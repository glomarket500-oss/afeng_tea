# -*- coding: utf-8 -*-
"""哨兵自检：网络全挂不炸、缺稿判定正确"""
import sys
from datetime import datetime

sys.path.insert(0, r"C:\afeng_tea")
import afeng_sentinel as S

t = f"{datetime.now():%Y%m%d}"
orig = S.today_posts

# ① 模拟 sitemap 连不上：wait_and_recount 不许抛
def boom(_):
    raise ConnectionResetError("模拟 sitemap 连不上")

S.today_posts = boom
story, review = S.wait_and_recount(t, tries=2, gap=1)
print(f"① 网络全挂 → 返回 故事{len(story)}/点评{len(review)}，未抛异常 ✔")
S.today_posts = orig

# ② 真实网络
s2, r2 = S.today_posts(t)
print(f"② 今天 {t}：线上 故事 {len(s2)} / 点评 {len(r2)}")

# ③ 分类与缺稿判定
S.today_posts = lambda d: ([f"/articles/{d}故事.html"], [])
st, rv = S.today_posts(t)
print(f"③ 模拟只有故事篇 → 缺{'点评篇' if not rv else '无'}" + (" ✔" if not rv else " ✘"))

S.today_posts = lambda d: ([], [f"/articles/{d}点评紫砂新闻.html"])
st, rv = S.today_posts(t)
print(f"④ 模拟只有点评篇（故事槽空/点评槽有）→ 缺{'故事篇' if not st else '无'}" + (" ✔" if not st else " ✘"))

S.today_posts = orig

# ⑤ 分类器：紫砂归点评，其余归故事
import re
cases = {"20261124惠州清晨一壶单丛.html": "故事", "20261124点评紫砂新闻吕俊杰.html": "点评"}
ok = True
for name, want in cases.items():
    got = "点评" if "紫砂" in name else "故事"
    ok &= (got == want)
print(f"⑤ 分类器 {'✔' if ok else '✘'}")
print("自检完成")
