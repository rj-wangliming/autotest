# -*- coding: utf-8 -*-
"""全量 setup 参数引用改造器（通用版，覆盖 5 组 224 文档）。

规则（按查询接口映射"名称过滤"字段）：
- 教室类: classroom/select → searchKeyword=${param.classroom_name}
          classroom/list, classroom/terminal/list → matchArr=[{fieldName:classroomName, EQUAL, ${param.classroom_name}}]
- 策略类: classroom/strategy/list → matchArr=[{fieldName:classroomStrategyName, EQUAL, ${param.strategy_name}}]
          space/strategy/tci/list, space/strategygroup/vdi/list → matchArr=[{fieldName:strategyName, EQUAL, ${param.strategy_name}}]
- 镜像类: classroom/image/list, spacetci/lessonImage/getLessonImageList → searchKeyword=${param.student_image_name} + matchArr=[{fieldName:imageName, EQUAL, ${param.student_image_name}}]
- 空间类: rcc/space/list → exactMatchArr=[{fieldName:spaceName, EQUAL, ${param.space_name}}]
- 无名称过滤（保持 itemArr[0] 标注）: seat/list, desktop/list, networkWhitelist/list, cluster, getAssignedClusterAndNetwork, agreement/template/list, vgpu/list
- 创建类: classroom/create → classroomName=${param.classroom_name}
          space/strategy/tci/create, space/strategygroup/vdi/create → name=${param.strategy_name}
          rcc/space/create → name=${param.space_name}（如有）
"""
import yaml, json, sys, os, glob, re

STAGE = '/Users/swlim/.reasonix/global-workspace/api_md_staging'
APPLY = '--apply' in sys.argv

# 查询接口 → (过滤 body, 标注说明)
QUERY_RULES = {
    'classroom/select': ({'searchKeyword': '${param.classroom_name}'}, '按名称过滤查询教室（searchKeyword=${param.classroom_name}）'),
    'classroom/list': ({'matchArr': [{'fieldName': 'classroomName', 'matchType': 'EQUAL', 'value': '${param.classroom_name}'}]},
                       '按教室名精确过滤（matchArr.fieldName=classroomName）'),
    'classroom/terminal/list': ({'matchArr': [{'fieldName': 'classroomName', 'matchType': 'EQUAL', 'value': '${param.classroom_name}'}]},
                                '按教室名精确过滤（matchArr.fieldName=classroomName）'),
    'classroom/strategy/list': ({'matchArr': [{'fieldName': 'classroomStrategyName', 'matchType': 'EQUAL', 'value': '${param.strategy_name}'}]},
                                '按策略名精确过滤（matchArr.fieldName=classroomStrategyName）'),
    'strategy/tci/list': ({'matchArr': [{'fieldName': 'strategyName', 'matchType': 'EQUAL', 'value': '${param.strategy_name}'}]},
                          '按策略名精确过滤（matchArr.fieldName=strategyName）'),
    'strategygroup/vdi/list': ({'matchArr': [{'fieldName': 'strategyName', 'matchType': 'EQUAL', 'value': '${param.strategy_name}'}]},
                               '按策略名精确过滤（matchArr.fieldName=strategyName）'),
    'classroom/image/list': ({'searchKeyword': '${param.student_image_name}',
                              'matchArr': [{'fieldName': 'imageName', 'matchType': 'EQUAL', 'value': '${param.student_image_name}'}]},
                             '按镜像名精确过滤（searchKeyword + matchArr.fieldName=imageName）'),
    'lessonImage/getLessonImageList': ({'searchKeyword': '${param.student_image_name}',
                                        'matchArr': [{'fieldName': 'imageName', 'matchType': 'EQUAL', 'value': '${param.student_image_name}'}]},
                                       '按镜像名精确过滤（searchKeyword + matchArr.fieldName=imageName）'),
    'space/list': ({'exactMatchArr': [{'fieldName': 'spaceName', 'matchType': 'EQUAL', 'value': '${param.space_name}'}]},
                   '按空间名精确过滤（exactMatchArr.fieldName=spaceName）'),
    # --- 补全：教室桌面/座位/白名单/镜像分配 ---
    'classroom/desktop/list': ({'matchArr': [{'fieldName': 'computerName', 'matchType': 'LIKE', 'value': '${param.desktop_name}'}]},
                               '按桌面名过滤（matchArr.fieldName=computerName）'),
    'classroom/seat/list': ({'exactMatchArr': [{'name': 'desktopName', 'valueArr': ['${param.desktop_name}']}]},
                            '按座位桌面名过滤（exactMatchArr.name=desktopName）'),
    'classroom/networkWhitelist/list': ({'matchArr': [{'fieldName': 'startIp', 'matchType': 'LIKE', 'value': '${param.start_ip}'}]},
                                        '按起始IP过滤（matchArr.fieldName=startIp）'),
    'classroom/image/assignImage/yetAssign/list': ({'searchKeyword': '${param.student_image_name}',
                                                    'matchArr': [{'fieldName': 'imageName', 'matchType': 'EQUAL', 'value': '${param.student_image_name}'}]},
                                                   '按镜像名过滤（searchKeyword + matchArr.fieldName=imageName）'),
    'space/classroom/cloudDesktop/list': ({'searchKeyword': '${param.desktop_name}',
                                           'matchArr': [{'fieldName': 'desktopName', 'matchType': 'LIKE', 'value': '${param.desktop_name}'}]},
                                          '按桌面名过滤（searchKeyword + matchArr.fieldName=desktopName）'),
    # --- 补全：空间发布 / 集群 / 统计 ---
    'space/publish': ({'name': '${param.space_name}'}, '按空间名过滤（name=${param.space_name}）'),
    'cluster/obtainComputeClusterList': ({'matchArr': [{'fieldName': 'clusterName', 'matchType': 'LIKE', 'value': '${param.cluster_name}'}]},
                                         '按集群名过滤（matchArr.fieldName=clusterName）'),
    'dashboard/statistics/getTrainingSpaceClusterList': ({'matchArr': [{'fieldName': 'clusterName', 'matchType': 'LIKE', 'value': '${param.cluster_name}'}]},
                                                         '按集群名过滤（matchArr.fieldName=clusterName）'),
}

# 无名称过滤接口 → 标注"取第一条"
NO_FILTER_NOTE = '取第一条（无名称过滤）'

# 创建类 → name 字段参数化
CREATE_RULES = {
    'classroom/create': ('classroomName', '${param.classroom_name}'),
    'strategy/tci/create': ('name', '${param.strategy_name}'),
    'strategygroup/vdi/create': ('name', '${param.strategy_name}'),
    'space/create': ('name', '${param.space_name}'),
}


def match_api(api, key):
    return key in (api or '')


def transform_frontmatter(txt):
    assert txt.startswith('---'), 'front-matter missing'
    idx2 = txt.index('\n---')
    fm_raw = txt[3:idx2]
    d = yaml.safe_load(fm_raw)
    setup = d.get('setup') or []
    a = b = 0
    changed = False
    for step in setup:
        name = step.get('name', '')
        api = step.get('api', '')
        ex = step.get('extract', {})
        ex_str = json.dumps(ex, ensure_ascii=False) if ex else ''
        step_str = json.dumps(step, ensure_ascii=False)
        # 幂等保护：该步骤已含 ${param.} 参数引用则跳过（避免重复/覆盖已精细改造）
        if '${param.' in step_str:
            continue
        # A 类：查询步骤（extract 用 [0]）且接口在规则表
        if '[0]' in ex_str:
            matched = False
            for key, (body, note) in QUERY_RULES.items():
                if match_api(api, key):
                    if 'request' not in step:
                        step['request'] = {}
                    step['request']['body'] = body
                    step['purpose'] = note
                    a += 1
                    changed = True
                    matched = True
                    break
            if not matched:
                # 无名称过滤接口：标注（不重复）
                old = step.get('purpose', '')
                if '取第一条' not in old:
                    step['purpose'] = (old + '；' if old else '') + NO_FILTER_NOTE
                    changed = True
        # B 类：创建类（请求体 name 字段参数化）
        for key, (field, param_ref) in CREATE_RULES.items():
            if match_api(api, key):
                if 'request' not in step:
                    step['request'] = {}
                body = step['request'].get('body') or {}
                body[field] = param_ref
                step['request']['body'] = body
                b += 1
                changed = True
                break
    if not changed:
        return None, a, b, False
    new_fm = yaml.safe_dump(d, allow_unicode=True, sort_keys=False, default_flow_style=False, width=10000)
    new_txt = '---\n' + new_fm.rstrip('\n') + '\n' + txt[idx2:]
    return new_txt, a, b, True


def verify(txt):
    idx2 = txt.index('\n---')
    yaml.safe_load(txt[3:idx2])
    return True


# 处理全部文档
files = [f for f in glob.glob(os.path.join(STAGE, '*.md'))
         if 'README' not in f and 'code_map' not in f and 'error_code_map' not in f and 'SETUP_PARAM' not in f]
report = []
for f in sorted(files):
    txt = open(f, encoding='utf-8').read()
    try:
        res = transform_frontmatter(txt)
    except Exception as e:
        report.append((os.path.basename(f), 'ERROR', str(e)[:60]))
        continue
    new_txt, a, b, ch = res
    if ch:
        if APPLY:
            assert verify(new_txt), f'{f} YAML verify failed'
            open(f, 'w', encoding='utf-8').write(new_txt)
        report.append((os.path.basename(f), f'A{a}+B{b}', ''))
print(f'{"--apply 已写盘" if APPLY else "dry-run 预览"}: 修改 {len(report)} 个文档')
for r in report[:20]:
    print(' ', r)
