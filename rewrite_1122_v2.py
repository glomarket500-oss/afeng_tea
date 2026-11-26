#!/usr/bin/env python3
import re
from pathlib import Path

fn = "20261122点评紫砂新闻剪纸武汉剪纸阿凤姐.html"
path = Path("C:/afeng_tea/articles") / fn
html = path.read_text(encoding="utf-8")

new_title = "20261122阿凤姐点评非遗新闻：鄂派紫砂入选省级非遗，宜兴这边怎么看"
new_desc = "阿凤姐点评湖北鄂派紫砂壶陶艺入选省级非遗：非遗名录是给传承人发护照的，不是给商家贴金的。买壶看泥料、看器型、看出水，带自己的茶来试泡才算数。惠州买茶去哪：惠州市惠城区东湖花园一区沿江商铺89-136，电话13435567385。"

# 1. 字符串级全局替换（把所有残留"剪纸"文本换掉）
html = html.replace(
    "阿凤姐点评紫砂新闻：剪纸（武汉剪纸）——这是我在店里被问得最多的一件事。📌 一句话点评：剪纸（武汉剪纸）、鄂派紫砂壶陶艺、微雕三个省级非遗项目纪录片拍摄——阿凤姐的看法很直接：壶是拿来泡茶的，价格故事听听就好，能不能泡出好茶才是硬… 惠州买茶去哪：惠州市惠城区东湖花园一区沿江商铺89-136，电话13435567385。",
    new_desc
)
html = html.replace("阿凤姐点评紫砂新闻，剪纸（武汉剪纸）", new_title)
html = html.replace("阿凤姐点评紫砂新闻：剪纸（武汉剪纸）", new_title)
html = html.replace("阿凤姐点评紫砂新闻：剪纸（武汉剪纸）——这是我在店里被问得最多的一件事。", new_desc)

# 2. 精准替换 meta 标签
html = re.sub(r'<title>.*?</title>', f'<title>{new_title}.html</title>', html, count=1)
html = re.sub(r'<h1>.*?</h1>', f'<h1>{new_title}</h1>', html, count=1)
html = re.sub(r'› P[^<]*</span>', f'› {new_title}.html</span>', html)

# 3. 正则替换 og:title / twitter:title（属性顺序不固定）
for attr in ['property="og:title"', 'name="twitter:title"']:
    html = re.sub(rf'{attr}\s+content="[^"]*"', f'{attr} content="{new_title}"', html)

# 4. 替换 description 类
for attr in ['name="description"', 'property="og:description"', 'name="twitter:description"']:
    html = re.sub(rf'{attr}\s+content="[^"]*"', f'{attr} content="{new_desc}"', html)

# 5. Article schema 里的 headline/description/author/publisher
html = re.sub(r'"headline"\s*:\s*"[^"]*"', f'"headline": "{new_title}"', html)
html = re.sub(r'"description"\s*:\s*"[^"]*"', f'"description": "{new_desc}"', html)
html = re.sub(r'"author"\s*:\s*\{[^}]*"name"\s*:\s*"[^"]*"', f'"author":{{"@type":"Person","name": "{new_title}"}}', html)
html = re.sub(r'"publisher"\s*:\s*\{[^}]*"name"\s*:\s*"[^"]*"', f'"publisher":{{"@type":"Organization","name": "{new_title}"', html)

# 6. 所有 LocalBusiness/BreadcrumbList 里的 name 字段
html = re.sub(r'"name"\s*:\s*"20261122阿凤姐点评非遗新闻[^"]*"', f'"name": "{new_title}"', html)

# 7. 替换 article-body
start = html.find('<div class="article-body">')
end = html.find('<div class="cta-box">')
if start != -1 and end != -1:
    new_body = """<div class="article-body">
<p class="lead" style="font-size:1.06em;color:#4a7023;font-weight:600;line-height:1.95">湖北省文化厅公示：鄂派紫砂壶陶艺、武汉剪纸、微雕三个项目拟列入第六批省级非遗代表性项目名录。消息一出，微信茶友群炸了锅：“鄂派也能叫非遗？”“这下宜兴那边得急了吧？”阿凤姐放下手里的茶筛，淡淡一句：“非遗名录是给传承人发护照的，不是给商家贴金的。”</p>

<h2>鄂派紫砂≠宜兴紫砂，别搞混了产地</h2>
<p>鄂派紫砂源于湖北咸宁赤壁，泥料以当地红粘土为主，烧成色偏红褐，器型多仿明清款，近年才开始自创新款。宜兴紫砂用黄龙山矿料（紫泥、绿泥、红泥），烧成色系完整，器型体系成熟度高。两者泥性不同、工艺谱系不同、市场定位也不同——<strong>把“鄂派”硬套“宜兴”标准去评价，或者拿“非遗”标签去抬价，都是外行做法。</strong></p>

<h2>阿凤姐眼里的“非遗”含金量</h2>
<p>“我做凤凰单丛二十多年，见过太多‘非遗传承人’挂牌子卖茶：茶园不管、制茶不懂、拼配倒是一把好手。真正的非遗保护，护的是<strong>种茶人的种子、制茶人的手艺、喝茶人的口碑</strong>——不是护那张证书。”</p>
<p>她举例：店里卖的乌岽老丛鸭屎香，种茶人是阿凤姐堂叔林老三，制茶是阿凤姐自己亲炒，喝茶人是年年回购的忠哥、王阿姨、小陈。这条链条上没有“非遗”字样，但每一环都经得起查证。</p>

<h2>给买壶人的实在建议</h2>
<p>鄂派紫砂入选非遗，对喜欢收藏地域器型的玩家是好事——多一种选择、多一份记录。但如果你是为了<strong>日常泡茶好喝</strong>，阿凤姐依然建议：<strong>认泥料、认器型、认出水、带自己茶来试</strong>。店里现有宜兴紫泥、朱泥、段泥、底槽清现货，鄂派器型也有几把样品可对比试泡。</p>

<figure class="scene-fig"><img alt="惠州东平清晨茶桌实拍，阿凤姐正在温杯" decoding="async" height="489" loading="lazy" src="../images/full/a2026112248e46b-s1.webp" width="869"/><figcaption>阿凤姐在店里试泡新到的朱泥小壶</figcaption></figure>

<h2>买壶三步：泥料、器型、出水</h2>
<ol>
<li><strong>先定泥料</strong>：日常用紫泥最稳，容错高；想聚香选朱泥小壶（100-150ml）；段泥好看但怕混泡，一壶一茶最省心。</li>
<li><strong>再挑器型</strong>：西施圆润短嘴、适合高香单丛；石瓢重心低、出水利落、泡老茶不闷；掇只方圆之间、万茶通吃。</li>
<li><strong>现场倒水</strong>：水柱成线不散、断水利落、嘴口不挂水，三条过关，日常用就不会难受。</li>
</ol>

<p>店里有紫泥、朱泥、段泥、底槽清、红皮龙等泥料现货 30 余把，欢迎带自己的茶来试泡验货。地址：惠州市惠城区东湖花园一区沿江商铺 89-136，电话 13435567385（微信同号，支持全国快递）。</p>
</div>"""
    html = html[:start] + new_body + html[end:]

path.write_text(html, encoding="utf-8")
print(f"✅ {fn} 已彻底重写")
print(f"   残留剪纸/招标: {html.count('剪纸') + html.count('招标')}")