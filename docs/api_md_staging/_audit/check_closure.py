#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check producer-consumer closure: create/add/assign endpoints must assert produced ID
and have its output consumed downstream."""
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

PRODUCER_PAT = re.compile(r'/(create|add|assign|batchCreate|batchConfig|bind|publish)$|/(create|add|assign)$')

problems = {}
producers = 0
for f in DOC_FILES:
    name = os.path.basename(f)
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    url = (data.get("api") or {}).get("url", "")
    if not PRODUCER_PAT.search(url):
        continue
    producers += 1
    # 1. success assertion must assert produced ID
    assertions = data.get("assertions") or {}
    succ = assertions.get("success") if isinstance(assertions, dict) else None
    succ_str = json.dumps(succ, ensure_ascii=False) if succ is not None else ""
    has_id_assert = bool(re.search(r'\$\.content\.(id|taskId|classroomId|strategyId|imageId|desktopId)\b', succ_str)) \
                    or bool(re.search(r'content\.(id|taskId)', succ_str))
    async_flag = (data.get("api") or {}).get("async")
    has_polling = bool(data.get("polling"))
    if not has_id_assert:
        problems.setdefault(name, []).append("成功断言未断言产出 ID（$.content.id/taskId）")
    if async_flag and not has_polling:
        problems.setdefault(name, []).append("async 但无 polling")
    # 2. output consumed: cleanup/delete_api or downstream referencing the produced resource
    has_cleanup = bool(data.get("cleanup"))
    has_del = False
    setup = data.get("setup")
    if isinstance(setup, list):
        for s in setup:
            if isinstance(s, dict) and (s.get("delete_api") or s.get("cleanup")):
                has_del = True
    if not has_cleanup and not has_del:
        # info only (some producers cleaned by their own setup recreate)
        problems.setdefault(name, []).append("无 cleanup/delete_api（产出资源未被清理或消费）")

print(f"create/add/assign 类接口数: {producers}")
print(f"闭包有问题的: {len(problems)}")
for name, ps in sorted(problems.items()):
    print(f"\n{name}:")
    for p in ps:
        print(f"  - {p}")
