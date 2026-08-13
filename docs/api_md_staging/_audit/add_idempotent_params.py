# -*- coding: utf-8 -*-
"""给创建类 setup 步骤加 idempotent 标记 + 生成 params 清单。

规则：
- 创建类步骤（api 含 create/add/assign/import）→ 加 idempotent: true
- 扫描所有 ${param.xxx} 引用 → 生成 params 段（required/optional）
"""
import yaml, glob, os, sys, re, json

STAGE = '/Users/swlim/.reasonix/global-workspace/api_md_staging'
APPLY = '--apply' in sys.argv

CREATE_PAT = re.compile(r'(create|add|assign|import)', re.IGNORECASE)


def transform(txt):
    assert txt.startswith('---')
    idx2 = txt.index('\n---')
    fm_raw = txt[3:idx2]
    d = yaml.safe_load(fm_raw)
    changed = False
    setup = d.get('setup') or []
    for step in setup:
        api = step.get('api', '')
        # 创建类步骤加 idempotent
        if CREATE_PAT.search(api or '') and 'idempotent' not in step:
            step['idempotent'] = True
            changed = True
    # 生成 params 清单
    all_refs = []
    for label, obj in [('main', d.get('request', {}).get('body', {})), ('setup', setup)]:
        s = json.dumps(obj, ensure_ascii=False)
        for m in re.finditer(r'\$\{param\.([\w.]+)\}', s):
            v = m.group(1).split('.')[0]
            if v not in all_refs:
                all_refs.append(v)
    if all_refs and 'params' not in d:
        d['params'] = {'required': [{'name': v, 'desc': '', 'used_by': '见 setup/request'} for v in all_refs]}
        changed = True
    if not changed:
        return None, False
    new_fm = yaml.safe_dump(d, allow_unicode=True, sort_keys=False, default_flow_style=False, width=10000)
    return '---\n' + new_fm.rstrip('\n') + '\n' + txt[idx2:], True


files = [f for f in glob.glob(os.path.join(STAGE, '*.md'))
         if 'README' not in f and 'code_map' not in f and 'error_code_map' not in f
         and 'SETUP_PARAM' not in f and '用例参数' not in f]
report = []
for f in sorted(files):
    txt = open(f, encoding='utf-8').read()
    new_txt, ch = transform(txt)
    if ch:
        if APPLY:
            yaml.safe_load(new_txt[3:new_txt.index('\n---')])
            open(f, 'w', encoding='utf-8').write(new_txt)
        report.append(os.path.basename(f))
print(f'{"--apply 已写盘" if APPLY else "dry-run"}: 修改 {len(report)} 个文档')
for r in report[:15]:
    print(' ', r)
