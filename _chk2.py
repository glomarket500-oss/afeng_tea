import puer_article as p
used = p._state().get("used", [])
pool = [t for t in p.TOPICS if t[0] not in used]
print("POOL_LEN", len(pool))
pool2 = pool or p.TOPICS
print("POOL2_LEN", len(pool2))
print("PICKED", len(pool2[:2]))
