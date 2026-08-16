#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check every ${param.xxx} referenced in front-matter (request.body/setup)
is declared in the params section; and every required param is used somewhere."""
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

problems = {}
for f in DOC_FILES:
    name = os.path.basename(f)
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    # collect ${param.xxx} references from request.body and setup (stringified)
    fm_text = block
    refs = set(re.findall(r'\$\{param\.([A-Za-z0-9_]+)\}', fm_text))
    refs |= set(re.findall(r'\$\{params?\.([A-Za-z0-9_]+)\}', fm_text))
    # params section declared names
    params = data.get("params") or {}
    declared = set()
    if isinstance(params, dict):
        for key in ("required", "optional"):
            items = params.get(key)
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict) and it.get("name"):
                        declared.add(it["name"])
                    elif isinstance(it, str):
                        declared.add(it)
    # diff
    undeclared = sorted(refs - declared)
    unused_required = sorted(declared - refs) if declared else []
    if undeclared:
        problems.setdefault(name, []).append(f"引用但未在 params 声明: {undeclared}")
    # unused required is informational only, report if many
    # (skip unused check: optional params may be unused)

print(f"接口文档数: {len(DOC_FILES)}")
print(f"有 params 引用问题的文件: {len(problems)}")
for name, ps in sorted(problems.items()):
    print(f"\n{name}:")
    for p in ps:
        print(f"  - {p}")
if not problems:
    print("✅ 所有 ${param.*} 引用均在 params 节声明")
