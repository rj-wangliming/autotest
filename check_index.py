import sys
sys.path.insert(0, 'D:/tools/autotest')
from app.core.orchestrator import Orchestrator

o = Orchestrator()
api = '/rcc/classroom/image/student/create'
meta = o.index.get(api)
print('API:', api)
print('Meta found:', meta is not None)
if meta:
    req_body = (meta.get('request') or {}).get('body') or {}
    sid = req_body.get('strategyId')
    print('strategyId from index:', sid)
