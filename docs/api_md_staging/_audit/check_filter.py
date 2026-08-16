#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skill #4: query setup steps extracting via [0] should have name-filter params
(searchKeyword/matchArr/exactMatchArr); otherwise they grab an arbitrary record."""
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

total_idx = 0
no_filter = []
has_filter = 0
for f in DOC_FILES:
    name = os.path.basename(f)
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    setup = data.get("setup")
    if not isinstance(setup, list):
        continue
    for s in setup:
        if not isinstance(s, dict):
            continue
        ext = s.get("extract")
        # collect jsonpaths from extract (dict or list form)
        jps = []
        if isinstance(ext, dict):
            jps = list(ext.values())
        elif isinstance(ext, list):
            for e in ext:
                if isinstance(e, dict) and e.get("jsonpath"):
                    jps.append(e["jsonpath"])
        # does any jsonpath use [0] indexing?
        uses_idx = any(isinstance(j, str) and "[0]" in j for j in jps)
        if not uses_idx:
            continue
        total_idx += 1
        # does this step have name filter in request.body?
        req = s.get("request") or {}
        body = req.get("body") if isinstance(req, dict) else None
        body_str = json.dumps(body, ensure_ascii=False) if body is not None else ""
        filtered = bool(re.search(r'matchArr|exactMatchArr|searchKeyword', body_str))
        step_name = s.get("name", "?")
        api = s.get("api", "?")
        if filtered:
            has_filter += 1
        else:
            no_filter.append((name, step_name, api))

print(f"用 [0] 提取的 setup 步骤: {total_idx}, 含名称过滤: {has_filter}, 无过滤: {len(no_filter)}")
for name, step, api in no_filter:
    print(f"  - {name} :: {step} ({api})")
