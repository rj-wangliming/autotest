import requests

resp = requests.get('http://127.0.0.1:5001/api/execution/af49b0ad').json()
logs = resp.get('logs', [])
print('Logs count:', len(logs))

# Find FAIL/error lines
for i, line in enumerate(logs):
    txt = str(line) if not isinstance(line, str) else line
    if 'FAIL' in txt or 'error' in txt.lower() or '策略' in txt or 'vdi' in txt.lower() or 'vdiStrategyId' in txt:
        print(f'  [{i}] {txt[-300:]}')
