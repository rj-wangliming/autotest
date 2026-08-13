# -*- coding: utf-8 -*-
import yaml, json, sys, os, re
STAGE = '/Users/swlim/.reasonix/global-workspace/api_md_staging'
FILES = json.load(open('/tmp/setup_classroom.json'))

errors = []
param_steps = 0
files_with_param = 0
for f in FILES:
    txt = open(os.path.join(STAGE, f), encoding='utf-8').read()
    # front-matter 解析
    assert txt.startswith('---')
    idx2 = txt.index('\n---')
    try:
        d = yaml.safe_load(txt[3:idx2])
    except Exception as e:
        errors.append('%s FRONTMATTER PARSE FAIL: %s' % (f, e))
        continue
    setup = d.get('setup') or []
    has_param = False
    for s in setup:
        req = s.get('request') or {}
        body = req.get('body')
        if body:
            blob = yaml.safe_dump(body, allow_unicode=True)
            if '${param.' in blob:
                param_steps += 1
                has_param = True
            # 校验 body 结构合法性（yaml round-trip 已经保证）
    # 主请求 value 绑定检查
    req = d.get('request') or {}
    rb = req.get('body') or {}
    main_val = 0
    for k, v in rb.items():
        if isinstance(v, dict) and 'value' in v and '${param.' in str(v['value']):
            main_val += 1
    if has_param or main_val:
        files_with_param += 1
    # 校验正文完整性：以 # 开头的 markdown 标题应存在
    if '\n# ' not in txt[idx2:]:
        errors.append('%s BODY LOST' % f)

print('files=%d, files_with_param_binding=%d, param_setup_steps=%d' % (len(FILES), files_with_param, param_steps))
print('errors=%d' % len(errors))
for e in errors:
    print('  ', e)
