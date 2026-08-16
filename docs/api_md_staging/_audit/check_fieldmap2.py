#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check upstream produces coverage and setup.extract -> ${prev} consumption chain
(which functionally implements field_map)."""
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

up_total = 0
up_with_produces = 0
up_with_fieldmap = 0
extract_vars_total = 0
extract_vars_consumed = 0
unconsumed = []
broken_chain = []

for f in DOC_FILES:
    name = os.path.basename(f)
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    # upstream produces/field_map
    for it in (data.get("upstream") or []):
        if not isinstance(it, dict):
            continue
        up_total += 1
        if it.get("produces"):
            up_with_produces += 1
        if it.get("field_map"):
            up_with_fieldmap += 1
    # setup extract vars and their consumption via ${prev.<var>} in request.body
    setup = data.get("setup")
    req_body_str = ""
    req = data.get("request") or {}
    if isinstance(req.get("body"), dict):
        import json as _json
        req_body_str = _json.dumps(req["body"], ensure_ascii=False)
    if isinstance(setup, list):
        for s in setup:
            if not isinstance(s, dict):
                continue
            step_name = s.get("name", "")
            ext = s.get("extract")
            vars_ = []
            if isinstance(ext, dict):
                vars_ = list(ext.keys())
            elif isinstance(ext, list):
                for e in ext:
                    if isinstance(e, dict) and e.get("var"):
                        vars_.append(e["var"])
            for v in vars_:
                extract_vars_total += 1
                # consumed if ${prev.<step>.*<v>} or ${prev.*<v>} appears in request body / setup / assertions
                pat = re.compile(r'\$\{prev\.' + re.escape(step_name) + r'\.[^}]*' + re.escape(v) + r'[^}]*\}'
                                 r'|\$\{prev\.[^}]*' + re.escape(v) + r'[^}]*\}')
                if pat.search(req_body_str) or pat.search(block):
                    extract_vars_consumed += 1
                else:
                    unconsumed.append((name, step_name, v))

print(f"upstream 条目: {up_total}, 含 produces: {up_with_produces}, 含 field_map: {up_with_fieldmap}")
print("setup extract 变量: %d, 被 prev 消费: %d" % (extract_vars_total, extract_vars_consumed))
print(f"未消费的 extract 变量: {len(unconsumed)}")
for n, s, v in unconsumed[:30]:
    print(f"  - {n} :: {s}.{v}")
