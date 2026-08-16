#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check polling.terminal_states enum values are legal batch task states."""
import os, glob, yaml
from collections import Counter

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

# 合法状态（SK 批任务状态枚举）
LEGAL = {"SUCCESS", "FAILURE", "PARTIAL_SUCCESS", "PARTIAL_FAIL", "RUNNING",
         "PENDING", "PROCESSING", "DONE", "WAITING", "CANCELLED", "CANCEL", "ERROR"}

states = Counter()
unknown = {}
for f in DOC_FILES:
    name = os.path.basename(f)
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    ts = (data.get("polling") or {}).get("terminal_states") or {}
    for key in ("success", "failure", "fail"):
        vals = ts.get(key) or []
        for v in vals:
            if isinstance(v, str):
                states[v] += 1
                if v not in LEGAL:
                    unknown.setdefault(name, []).append(v)

print("terminal_states 状态值分布:")
for k, v in states.most_common():
    print(f"  {k}: {v}")
print(f"\n非标准状态: {len(unknown)}")
for name, vs in sorted(unknown.items()):
    print(f"  {name}: {vs}")
