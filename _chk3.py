import puer_article as p
r = p.pick_topics(2)
print("RET", len(r), [x[0] for x in r])
