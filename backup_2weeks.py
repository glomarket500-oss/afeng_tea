#!/usr/bin/env python3
"""备份两周内 23 篇文章到 backup_2weeks_20261125/"""
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta

ARTICLES_DIR = Path(__file__).parent / "articles"
BACKUP_DIR = Path(__file__).parent / "backup_2weeks_20261125"
CST = timezone(timedelta(hours=8))

def parse_date(fname):
    import re
    m = re.match(r"(\d{8})", fname)
    if not m: return None
    try:
        return datetime.strptime(m.group(1), "%Y%m%d").replace(tzinfo=CST)
    except ValueError:
        return None

BACKUP_DIR.mkdir(exist_ok=True)
n = 0
for f in sorted(ARTICLES_DIR.glob("*.html")):
    dt = parse_date(f.name)
    if dt and datetime(2026, 11, 11, tzinfo=CST) <= dt <= datetime(2026, 11, 25, tzinfo=CST):
        shutil.copy2(f, BACKUP_DIR / f.name)
        n += 1
print(f"✅ 已备份 {n} 篇到 {BACKUP_DIR}")
