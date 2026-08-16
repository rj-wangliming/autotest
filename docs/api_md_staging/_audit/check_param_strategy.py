#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check 参数取值策略 section: table has param/strategy rows."""
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

# front-matter 有无 params 节（参数取值策略）
no_params = []
with_params = []
for f in DOC_FILES:
    name = os.path.basename(f)
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    params = data.get("params")
    req = data.get("request") or {}
    body = req.get("body") if isinstance(req, dict) else None
    has_body_params = isinstance(body, dict) and len(body) > 0
    if has_body_params and not params:
        no_params.append(name)
    elif params:
        with_params.append(name)

print(f"有 request.body 参数的接口中:")
print(f"  有 params 节: {len(with_params)}")
print(f"  无 params 节: {len(no_params)}")
for n in no_params:
    print(f"    {n}")
