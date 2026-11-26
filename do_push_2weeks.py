import sys
sys.path.insert(0, 'C:/afeng_tea')
from git_push_api import push_via_api

REPO = 'C:/afeng_tea'
try:
    sha = push_via_api(REPO)
    print('PUSH_RESULT:', sha)
except Exception as e:
    print('PUSH_ERROR:', e)