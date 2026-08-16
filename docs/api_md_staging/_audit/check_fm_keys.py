#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check front-matter required data-layer keys present (skill #7)."""
import os, glob, re
import yaml

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
DOC_FILES = sorted(f for f in glob.glob(os.path.join(DOCS_DIR, "*.md"))
                   if os.path.basename(f) not in (
                       "README.md", "SETUP_PARAM_SPEC.md", "business_rules.md",
                       "code_map_all.md", "error_code_map_tci_strategy.md",
                       "修订记录.md", "外部接口清单.md", "用例参数_VDI教师机镜像变更策略.md"))

REQUIRED = ["api", "response", "assertions", "idempotency"]  # must-have
OPTIONAL = ["request", "setup", "upstream", "downstream", "cleanup", "polling", "constraints", "params"]

def get_fm(lines):
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return None

problems = {}
for f in DOC_FILES:
    name = os.path.basename(f)
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    missing = [k for k in REQUIRED if k not in data]
    if missing:
        problems.setdefault(name, []).append(f"缺必要字段: {missing}")

print(f"缺必要字段的文件: {len(problems)}")
for name, ps in sorted(problems.items()):
    for p in ps:
        print(f"  {name}: {p}")
if not problems:
    print("✅ 所有文档 front-matter 必要字段齐全")

# 统计各字段覆盖率
from collections import Counter
cnt = Counter()
for f in DOC_FILES:
    name = os.path.basename(f)
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    for k in REQUIRED + OPTIONAL:
        if k in data:
            cnt[k] += 1
print("\n字段覆盖率:")
for k in REQUIRED + OPTIONAL:
    print(f"  {k}: {cnt.get(k,0)}/{len(DOC_FILES)}")
