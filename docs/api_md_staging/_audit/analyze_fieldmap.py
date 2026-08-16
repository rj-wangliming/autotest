#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze field_map derivability from the existing three pieces:
upstream.produces + setup.extract + request.body ${prev.*} references."""
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

# per-interface: collect (upstream produces jsonpath -> field, extract var -> jsonpath, prev refs)
up_total = 0
up_with_produces = 0
extract_total = 0
extract_consumed = 0
full_chain = 0  # produces + extract + prev all aligned

for f in DOC_FILES:
    name = os.path.basename(f)
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    # upstream produces
    for it in (data.get("upstream") or []):
        if not isinstance(it, dict):
            continue
        up_total += 1
        if it.get("produces"):
            up_with_produces += 1
    # setup extract vars
    setup = data.get("setup")
    if not isinstance(setup, list):
        continue
    # collect extract var -> jsonpath, and prev refs in request.body
    req = data.get("request") or {}
    req_body_str = json.dumps(req.get("body"), ensure_ascii=False) if isinstance(req.get("body"), dict) else ""
    prev_refs = set(re.findall(r'\$\{prev\.([A-Za-z0-9_]+)\.(?:output\.)?([A-Za-z0-9_]+)', req_body_str))
    prev_flat = set(re.findall(r'\$\{prev\.([A-Za-z0-9_]+)\}', req_body_str))
    for s in setup:
        if not isinstance(s, dict):
            continue
        step = s.get("name", "")
        ext = s.get("extract")
        vars_ = []
        if isinstance(ext, dict):
            vars_ = list(ext.items())  # (var, jsonpath)
        elif isinstance(ext, list):
            for e in ext:
                if isinstance(e, dict) and e.get("var"):
                    vars_.append((e["var"], e.get("jsonpath", "")))
        for var, jp in vars_:
            extract_total += 1
            # consumed if any prev ref uses this var (step-scoped or flat)
            consumed = any(v == var for (st, v) in prev_refs) or var in prev_flat or \
                       re.search(r'\$\{prev\.' + re.escape(step) + r'\.[^}]*' + re.escape(var), req_body_str)
            if consumed:
                extract_consumed += 1

print(f"upstream 条目: {up_total}, 含 produces: {up_with_produces}")
print("setup extract 变量: %d, 被 prev 消费: %d (%d%%)" % (
    extract_total, extract_consumed, 100*extract_consumed//max(extract_total,1)))
