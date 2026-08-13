import yaml, json, sys

files = json.load(open('/tmp/setup_classroom.json'))
out = []
for f in files:
    txt = open(f, encoding='utf-8').read()
    if not txt.startswith('---'):
        out.append('NO_FMM ' + f)
        continue
    fm = txt.split('---', 2)[1]
    d = yaml.safe_load(fm)
    setup = d.get('setup')
    out.append('=' * 12 + ' ' + f)
    out.append(yaml.safe_dump(setup, allow_unicode=True, sort_keys=False).rstrip())
open('/Users/swlim/.reasonix/global-workspace/api_md_staging/_audit/setup_dump.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('dumped', len(out))
