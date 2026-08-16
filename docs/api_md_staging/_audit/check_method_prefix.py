#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check downstream/upstream api fields missing HTTP method prefix (should be POST /xxx)."""
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

problems = {}
for f in DOC_FILES:
    name = os.path.basename(f)
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    for key in ("upstream", "downstream", "cleanup"):
        items = data.get(key)
        if not isinstance(items, list):
            continue
        for it in items:
            if not isinstance(it, dict):
                continue
            api = it.get("api", "")
            if not isinstance(api, str) or not api:
                continue
            # starts with '/' but no POST/GET prefix
            if re.match(r'^/[a-zA-Z]', api) and "POST" not in api and "GET" not in api:
                problems.setdefault(name, []).append(f"{key}.api 缺 HTTP 方法前缀: {api[:50]}")

print(f"缺 HTTP 方法前缀的条目数: {len(problems)}")
for name, ps in sorted(problems.items()):
    for p in ps:
        print(f"  {name}: {p}")
