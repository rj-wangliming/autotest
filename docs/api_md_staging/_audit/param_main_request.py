# -*- coding: utf-8 -*-
"""主请求体参数化：给主接口 request.body 的名称/搜索字段补 ${param.} 引用。

规则：
- /rcc/classroom/create: classroomName → ${param.classroom_name}
- /rcc/classroom/select: searchKeyword → ${param.classroom_name}
- /rcc/classroom/list: matchArr → [classroomName EQUAL ${param.classroom_name}]（若 matchArr 结构允许）
- /rcc/classroom/image/list: searchKeyword → ${param.student_image_name}（若存在）
- /space/strategygroup/vdi/create, /space/strategy/tci/create: name → ${param.strategy_name}
- /rcc/space/create: name → ${param.space_name}（若存在）
幂等：字段已有 ${param.} 或 ${prev.} 则跳过。
"""
import yaml, glob, os, sys

STAGE = '/Users/swlim/.reasonix/global-workspace/api_md_staging'
APPLY = '--apply' in sys.argv

RULES = {
    '/rcc/classroom/create': ('classroomName', '${param.classroom_name}'),
    '/rcc/classroom/select': ('searchKeyword', '${param.classroom_name}'),
    '/space/strategygroup/vdi/create': ('name', '${param.strategy_name}'),
    '/space/strategy/tci/create': ('name', '${param.strategy_name}'),
    '/rcc/space/create': ('name', '${param.space_name}'),
}


def transform(txt):
    assert txt.startswith('---')
    idx2 = txt.index('\n---')
    fm_raw = txt[3:idx2]
    d = yaml.safe_load(fm_raw)
    url = (d.get('api') or {}).get('url', '')
    if url not in RULES:
        return None, False
    field, param_ref = RULES[url]
    body = (d.get('request') or {}).get('body') or {}
    if field not in body:
        return None, False
    fv = body[field]
    # 支持 {type, description, ...} 或 {value: ...} 结构
    if isinstance(fv, dict):
        if 'value' in fv and isinstance(fv['value'], str) and '${' in fv['value']:
            return None, False  # 已参数化
        if 'value' in fv:
            fv['value'] = param_ref
        else:
            fv['value'] = param_ref
        body[field] = fv
    elif isinstance(fv, str) and '${' not in fv:
        body[field] = {'value': param_ref, 'type': 'String', 'description': fv}
    else:
        return None, False
    if 'request' not in d:
        d['request'] = {}
    d['request']['body'] = body
    new_fm = yaml.safe_dump(d, allow_unicode=True, sort_keys=False, default_flow_style=False, width=10000)
    return '---\n' + new_fm.rstrip('\n') + '\n' + txt[idx2:], True


files = [f for f in glob.glob(os.path.join(STAGE, '*.md'))
         if 'README' not in f and 'code_map' not in f and 'error_code_map' not in f and 'SETUP_PARAM' not in f]
report = []
for f in sorted(files):
    txt = open(f, encoding='utf-8').read()
    new_txt, ch = transform(txt)
    if ch:
        if APPLY:
            yaml.safe_load(new_txt[3:new_txt.index('\n---')])
            open(f, 'w', encoding='utf-8').write(new_txt)
        report.append(os.path.basename(f))
print(f'{"--apply 已写盘" if APPLY else "dry-run"}: 主请求体参数化 {len(report)} 个')
for r in report:
    print(' ', r)
