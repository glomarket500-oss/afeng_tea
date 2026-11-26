#!/usr/bin/env python3
import re
from pathlib import Path

def rewrite(path, new_title, new_body, figure_alt, figure_src):
    fn = path.name
    html = path.read_text(encoding="utf-8")
    # 1. 标题
    html = re.sub(r"<title>.*?</title>", f"<title>{new_title}.html</title>", html, count=1)
    html = re.sub(r"<h1>.*?</h1>", f"<h1>{new_title}</h1>", html, count=1)
    # 2. 面包屑
    html = re.sub(r'› P[^<]*</span>', f'› {new_title}.html</span>', html)
    # 3. meta 描述
    for attr in ['name="description"', 'property="og:description"', 'name="twitter:description"']:
        html = re.sub(rf'{attr}\s+content="[^"]*"', f'{attr} content="{new_title} 阿凤姐从二十年泡茶经验说：{new_title[:30]}"', html)
    # 4. og:title / twitter:title
    for attr in ['property="og:title"', 'name="twitter:title"']:
        html = re.sub(rf'{attr}\s+content="[^"]*"', f'{attr} content="{new_title}"', html)
    # 5. schema headline/name
    html = re.sub(r'"headline"\s*:\s*"[^"]*"', f'"headline": "{new_title}"', html)
    html = re.sub(r'"name"\s*:\s*"2026112[0-9][^"]*"', f'"name": "{new_title}"', html)
    # 6. article-body 替换
    start = html.find('<div class="article-body">')
    end = html.find('<div class="cta-box">')
    if start != -1 and end != -1:
        new_body_html = f"""<div class="article-body">
{new_body}
</div>"""
        html = html[:start] + new_body_html + html[end:]
    path.write_text(html, encoding="utf-8")
    print(f"✅ {fn} 已重写")
    print(f"   残留【场景开头】: {html.count('【场景开头】')}, 买壶人该记住: {html.count('买壶人该记住的四件事')}")

# ===== 11-24 致敬手艺人 =====
rewrite(
    Path("C:/afeng_tea/articles/20261124点评紫砂新闻致敬手艺人阿凤姐.html"),
    "20261124阿凤姐点评紫砂新闻：致敬手艺人，一把壶的一生比人还长",
    """<p class="lead" style="font-size:1.06em;color:#4a7023;font-weight:600;line-height:1.95">宜兴陶艺家陈洪明先生八十岁，还在做壶。媒体写了篇《致敬手艺人》，朋友圈转了好几圈。阿凤姐把那篇文章翻出来，指着其中一句给我看：“壶有灵性，养它的人有耐心。”她放下手机：“这话对，但我要补一句——<strong>耐心是给壶的，灵性是自己喝出来的。</strong>”</p>

<h2>老艺人为什么说“壶有灵性”</h2>
<p>陈洪明从十五岁学艺，做了一辈子紫砂。他说壶有灵性，其实是说泥料会记住人：同样的茶，新壶和养了三年的壶，泡出来是两个味道。这背后是紫砂的双重透气性——既能保香，又能透水汽，时间一长，茶汤里那点物质渗进气孔，壶身就“熟”了。</p>
<p>阿凤姐的解读很实在：“<strong>灵性不是玄学，是物理。</strong>你每天用它泡同一种茶，气孔里存的都是那个茶香，下一次注水，它反哺给你。就像我店里的老丛蜜兰香，泡到第八泡还有兰香，不是茶耐泡，是壶把香气存住了。”</p>

<h2>一把壶能用多久？阿凤姐算了笔账</h2>
<p>有茶友问：“几十块的壶和几千块的壶，差别到底在哪？”阿凤姐掰着指头说：<strong>泥料纯不纯、窑温够不够、出水顺不顺。</strong>“泥料差的壶，用半年气孔就堵死了，泡什么茶都一个味；窑温不足的壶，胎体发虚，泡茶容易吸串味。真正的好壶，用十年二十年，越用越润。”</p>

<h2>阿凤姐的养壶三戒</h2>
<ol>
<li><strong>一壶一茶</strong>：单丛这种高香茶，最怕串味。蜜兰香、鸭屎香、锯朵仔，各配一把，别混着泡。</li>
<li><strong>用后必洗必晾</strong>：茶渣倒掉、温水冲净、口朝下晾干。闷在壶里过夜，茶垢一厚，香就闷住了。</li>
<li><strong>别用洗洁精</strong>：紫砂会吸附，洗洁精残留在气孔里，一泡茶就全吐出来。</li>
</ol>

<figure class="scene-fig"><img alt="阿凤姐在店里养了五年的朱泥小壶，壶身已有包浆" decoding="async" height="489" loading="lazy" src="../images/full/a2026112448e46b-s2.webp" width="869"/><figcaption>阿凤姐养了五年的朱泥小壶</figcaption></figure>

<p>店里现有宜兴紫泥、朱泥、段泥现货，从入门到收藏级都有。地址：惠州市惠城区东湖花园一区沿江商铺 89-136，电话 13435567385（微信同号，支持全国快递）。</p>""",
    "阿凤姐在店里养了五年的朱泥小壶，壶身已有包浆",
    "../images/full/a2026112448e46b-s2.webp"
)

# ===== 11-25 一把壶可以泡一杯茶 =====
rewrite(
    Path("C:/afeng_tea/articles/20261125点评紫砂新闻一把壶可以泡一杯茶阿凤姐.html"),
    "20261125阿凤姐点评紫砂新闻：一把壶可以泡一杯茶，也可以泡一个人",
    """<p class="lead" style="font-size:1.06em;color:#4a7023;font-weight:600;line-height:1.95">《一把壶可以泡一杯茶》这标题上了热搜——紫砂壶界一位年轻作者写自己第一把全手工壶：从打泥片、起身筒、做壶盖，到进窑、出窑、开壶，前后四十天。阿凤姐看到这标题先笑了：“<strong>一把壶可以泡一杯茶，也可以泡一个人。</strong>我见过太多人，泡着泡着，就把自己泡明白了。”</p>

<h2>全手工壶为什么贵？贵在四十天的“废”</h2>
<p>年轻作者说他的壶“废”了三次才成：第一次泥片干了开裂，第二次身筒合不拢，第三次壶盖配不上。阿凤姐点头：“这就是全手工的代价。模具壶一天出几十把，全手工一把要四十天。贵不是贵在泥料，是贵在<strong>那四十天里反复重来、不将就</strong>。”</p>

<h2>从做壶到泡茶，道理是通的</h2>
<p>阿凤姐用自己制茶的经历类比：“我做凤凰单丛，做青那一步最讲究。同一批茶青，我堂叔做出来花香显，我做出来就淡一点，差别就在<strong>那半小时的手感</strong>。做壶、做茶、做人，都一样——<strong>差一点，就差很多。</strong>”</p>

<h2>新手第一把壶怎么选？</h2>
<ul>
<li><strong>预算</strong>：入门 200-500 元，选紫泥西施或石瓢，泥料真、器型稳，练手不心疼。</li>
<li><strong>看出水</strong>：倒水时水柱成线、断水利落、壶嘴不挂水。这三条过，日常用就舒坦。</li>
<li><strong>听声音</strong>：轻敲壶身，声音清脆均匀是好泥；闷哑发木，多半窑温不够或泥料掺了东西。</li>
</ul>

<figure class="scene-fig"><img alt="阿凤姐把新到的全手工朱泥壶放在茶盘上比对" decoding="async" height="489" loading="lazy" src="../images/full/a2026112548e46b-s1.webp" width="869"/><figcaption>阿凤姐比对新到的全手工朱泥壶</figcaption></figure>

<p>一把好壶，配一泡好茶，是茶桌上最值得的投入。地址：惠州市惠城区东湖花园一区沿江商铺 89-136，电话 13435567385（微信同号，支持全国快递）。</p>""",
    "阿凤姐把新到的全手工朱泥壶放在茶盘上比对",
    "../images/full/a2026112548e46b-s1.webp"
)