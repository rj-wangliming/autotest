import yaml, json, sys

files = json.load(open('/tmp/setup_classroom.json'))
out = []
for f in files:
    txt = open(f, encoding='utf-8').read()
    fm = txt.split('---', 2)[1]
    d = yaml.safe_load(fm)
    setup = d.get('setup') or []
    parts = []
    for s in setup:
        api = s.get('api', '')
        if isinstance(api, str) and api.startswith('内部调用'):
            api = '<INT>'
        has_req = 'request' in s
        has_ext = 'extract' in s
        parts.append('{}({})(req={},ext={})'.format(s.get('name'), api.split(' ')[-1], has_req, has_ext))
    out.append('{} | {}'.format(f, ' ; '.join(parts)))
sys.stdout.write('\n'.join(out))
