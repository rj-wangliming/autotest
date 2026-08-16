#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check idempotency annotation on operational interfaces + failure assertion trigger."""
import os, glob, re
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

OP_PAT = re.compile(r'/(create|delete|edit|add|assign|update|batchCreate|batchConfig|batchDelete|bind|publish|shutdown|restart|powerOff|start|end|closeTerminal)$|/(create|delete|edit|add|assign|update)$')

problems = {}
op_total = 0
for f in DOC_FILES:
    name = os.path.basename(f)
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    url = (data.get("api") or {}).get("url", "")
    # idempotency for operational interfaces
    if OP_PAT.search(url):
        op_total += 1
        if not data.get("idempotency"):
            problems.setdefault(name, []).append("操作类接口缺 idempotency 标注")
    # failure assertion trigger
    assertions = data.get("assertions")
    if isinstance(assertions, dict):
        fail = assertions.get("failure")
        if isinstance(fail, list):
            for i, sc in enumerate(fail):
                if isinstance(sc, dict) and not sc.get("trigger"):
                    problems.setdefault(name, []).append(f"失败场景 #{i+1} 缺 trigger（触发条件）")

print(f"操作类接口: {op_total}")
print(f"有问题的文件: {len(problems)}")
for name, ps in sorted(problems.items()):
    print(f"\n{name}:")
    for p in ps:
        print(f"  - {p}")
if not problems:
    print("✅ 幂等性 + 失败 trigger 全部完整")
