#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check success assertions depth: expect should reference concrete response fields
($.content.xxx / msgKey), not only $.status==SUCCESS."""
import os, glob, re, json
import yaml

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
DOC_FILES = sorted(f for f in glob.glob(os.path.join(DOCS_DIR, "*.md"))
                   if os.path.basename(f) not in (
                       "README.md", "SETUP_PARAM_SPEC.md", "business_rules.md",
                       "code_map_all.md", "error_code_map_tci_strategy.md",
                       "修订记录.md", "外部接口清单.md", "用例参数_VDI教师机镜像变更策略.md"))

def get_fm(lines):
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return None

shallow = []
total = 0
for f in DOC_FILES:
    name = os.path.basename(f)
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    assertions = data.get("assertions")
    if not isinstance(assertions, dict):
        continue
    succ = assertions.get("success")
    if not isinstance(succ, list) or not succ:
        continue
    total += 1
    succ_str = json.dumps(succ, ensure_ascii=False)
    # 深断言：含 $.content. 或 msgKey 或具体字段（排除纯 status）
    has_content = bool(re.search(r'\$\.content\.', succ_str))
    has_msgkey = bool(re.search(r'msgKey', succ_str))
    has_field = bool(re.search(r'content\.(id|taskId|classroomId|total|itemArr|\w+)', succ_str))
    if not (has_content or has_msgkey or has_field):
        shallow.append((name, succ_str[:80]))

print(f"有成功断言场景的接口: {total}")
print(f"成功断言仅 $.status==SUCCESS（浅断言）: {len(shallow)}")
for n, s in shallow[:30]:
    print(f"  {n}: {s}")
