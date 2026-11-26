import re
txt = open('C:/Users/Administrator/.git-credentials', encoding='utf-8', errors='replace').read()
m = re.search(r'https://[^:@\s]+:([^@\s]+)@github\.com', txt)
print('有token:', bool(m))
print('长度:', len(m.group(1)) if m else 0)