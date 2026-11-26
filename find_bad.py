import json
with open('C:/afeng_tea/audit_report.json','r',encoding='utf-8') as f:
    data = json.load(f)
articles = data.get('articles', data.get('results', []))
print("总条目:", len(articles))
for item in articles:
    score = item.get('total_score', item.get('score', 0))
    if score < 60:
        print(f"不合格: {item.get('filename','')} score={score}")