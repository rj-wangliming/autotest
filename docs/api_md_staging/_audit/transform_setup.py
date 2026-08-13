# -*- coding: utf-8 -*-
"""classroom 组 60 个文档 setup 参数引用改造。
用法：python3 transform_setup.py [--apply]
  dry-run（默认）：输出每文档 A/B 计数与修改摘要，不写盘。
  --apply：实际写盘并验证。
"""
import yaml, json, sys, os

STAGE = '/Users/swlim/.reasonix/global-workspace/api_md_staging'
FILES = json.load(open('/tmp/setup_classroom.json'))

APPLY = '--apply' in sys.argv


def match_api(api, key):
    return key in (api or '')


def classify(step):
    """返回 ('A'|'B'|None, request_body_dict or None, purpose_note or None, extract_name_newval or None)"""
    name = step.get('name')
    api = step.get('api', '')
    # ---------- A 类：教室按名称过滤 ----------
    if name in ('query_classroom', 'listClassroom') and 'classroom/select' in api:
        return ('A', {'searchKeyword': '${param.classroom_name}'}, '按名称过滤查询教室（searchKeyword=${param.classroom_name}），获取 classroomId', None)
    if name in ('query_classroom', 'listClassroom') and 'classroom/terminal/list' in api:
        return ('A', {'matchArr': [{'fieldName': 'classroomName', 'matchType': 'EQUAL', 'value': '${param.classroom_name}'}]},
                '按教室名精确过滤查询教室列表（matchArr.fieldName=classroomName），取 classroomId', None)
    if name in ('query_classroom', 'listClassroom') and 'classroom/list' in api:
        return ('A', {'matchArr': [{'fieldName': 'classroomName', 'matchType': 'EQUAL', 'value': '${param.classroom_name}'}]},
                '按教室名精确过滤分页查询教室（matchArr.fieldName=classroomName），取 classroomId', None)
    # ---------- A 类：策略按名称过滤 ----------
    if name == 'get_strategy' and 'classroom/strategy/list' in api:
        return ('A', {'matchArr': [{'fieldName': 'classroomStrategyName', 'matchType': 'EQUAL', 'value': '${param.strategy_name}'}]},
                '按策略名精确过滤获取教室策略（matchArr.fieldName=classroomStrategyName），取 classroomStrategyId', None)
    # ---------- A 类：镜像按名称过滤 ----------
    if name == 'listImage' and 'classroom/image/list' in api:
        prev_classroom = None
        return ('A', {'crId': '${prev.listClassroom.output.classroomId}',
                      'searchKeyword': '${param.student_image_name}',
                      'matchArr': [{'fieldName': 'imageName', 'matchType': 'EQUAL', 'value': '${param.student_image_name}'}]},
                '按镜像名精确过滤查询镜像（crId=${prev.listClassroom.output.classroomId}，searchKeyword=${param.student_image_name}），取 imageId', None)
    # ---------- A 类：无名称过滤参数 → 保持 itemArr[0] 并标注 ----------
    if name in ('query_seat', 'listSeat') and 'classroom/seat/list' in api:
        return ('A', None, '取第一条（无名称过滤）', None)
    if name == 'query_desktop' and 'classroom/desktop/list' in api:
        return ('A', None, '取第一条（无名称过滤）', None)
    if name == 'get_white_list' and 'classroom/networkWhitelist/list' in api:
        return ('A', None, '取第一条（无名称过滤）', None)
    if name == 'get_cluster_network' and 'classroom/image/getAssignedClusterAndNetwork' in api:
        return ('A', None, '取第一条（无名称过滤）', None)
    # ---------- B 类：创建教室绑定名称参数 ----------
    if name in ('create_classroom', 'createClassroom') and 'classroom/create' in api:
        return ('B', {'classroomName': '${param.classroom_name}'}, None,
                ('classroomName', '${param.classroom_name}'))
    # ---------- 其它：不改 ----------
    return (None, None, None, None)


def transform_frontmatter(txt):
    """解析 front-matter 并改造，返回 (new_txt, a_count, b_count, main_req_notes, changed)"""
    assert txt.startswith('---'), 'front-matter missing'
    idx2 = txt.index('\n---')
    fm_raw = txt[3:idx2]
    d = yaml.safe_load(fm_raw)
    setup = d.get('setup') or []
    a = b = 0
    changed = False
    for step in setup:
        kind, body, note, extract_new = classify(step)
        if kind is None:
            continue
        if kind == 'A':
            a += 1
            if body is not None:
                if 'request' not in step:
                    step['request'] = {}
                step['request']['body'] = body
                changed = True
            if note:
                old = step.get('purpose', '')
                if '取第一条（无名称过滤）' not in old and '按' not in old[:2]:
                    # 标注：若 purpose 是简单描述则追加说明
                    if '获取' in old or '查询' in old or 'ID' in old:
                        step['purpose'] = old + '；' + note
                    else:
                        step['purpose'] = note
                elif note.startswith('按名称') or note.startswith('按策略') or note.startswith('按镜像'):
                    step['purpose'] = note
                changed = True
        elif kind == 'B':
            b += 1
            if 'request' not in step:
                step['request'] = {}
            step['request']['body'] = body
            changed = True
            if extract_new:
                evar, evalue = extract_new
                ext = step.get('extract')
                if isinstance(ext, dict) and evar in ext:
                    oldv = ext[evar]
                    if isinstance(oldv, str) and not oldv.startswith('$'):
                        ext[evar] = evalue
    # ---------- 主请求补充绑定（仅 select/list/create 三个查询/创建主接口） ----------
    main_req_notes = []
    api_url = (d.get('api') or {}).get('url', '')
    req_body = (d.get('request') or {}).get('body') or {}
    if api_url == '/rcc/classroom/select' and 'searchKeyword' in req_body:
        if isinstance(req_body['searchKeyword'], dict):
            if 'value' not in req_body['searchKeyword']:
                req_body['searchKeyword']['value'] = '${param.classroom_name}'
                changed = True
                main_req_notes.append('request.body.searchKeyword.value=${param.classroom_name}')
    elif api_url == '/rcc/classroom/list' and 'matchArr' in req_body:
        if isinstance(req_body['matchArr'], dict) and 'value' not in req_body['matchArr']:
            req_body['matchArr']['value'] = [{'fieldName': 'classroomName', 'matchType': 'EQUAL', 'value': '${param.classroom_name}'}]
            changed = True
            main_req_notes.append('request.body.matchArr.value=[classroomName EQUAL ${param.classroom_name}]')
    elif api_url == '/rcc/classroom/create' and 'classroomName' in req_body:
        if isinstance(req_body['classroomName'], dict) and 'value' not in req_body['classroomName']:
            req_body['classroomName']['value'] = '${param.classroom_name}'
            changed = True
            main_req_notes.append('request.body.classroomName.value=${param.classroom_name}')
    if not changed:
        return None, a, b, main_req_notes, False
    new_fm = yaml.safe_dump(d, allow_unicode=True, sort_keys=False, default_flow_style=False)
    new_txt = '---\n' + new_fm.rstrip('\n') + '\n' + txt[idx2:]
    return new_txt, a, b, main_req_notes, True


def verify(txt):
    idx2 = txt.index('\n---')
    yaml.safe_load(txt[3:idx2])
    return True


report = []
for f in FILES:
    path = os.path.join(STAGE, f)
    txt = open(path, encoding='utf-8').read()
    new_txt, a, b, main_notes, changed = transform_frontmatter(txt)
    if APPLY:
        if changed:
            open(path, 'w', encoding='utf-8').write(new_txt)
        verify(open(path, encoding='utf-8').read())
    report.append((f, a, b, main_notes, changed))

if APPLY:
    print('APPLIED')
total_a = total_b = 0
for f, a, b, notes, changed in report:
    total_a += a
    total_b += b
    extra = ('  [主请求] ' + '; '.join(notes)) if notes else ''
    flag = '' if changed else '  <无改造>'
    print('%-52s A=%d B=%d%s%s' % (f, a, b, extra, flag))
print('TOTAL A=%d B=%d over %d docs' % (total_a, total_b, len(report)))
