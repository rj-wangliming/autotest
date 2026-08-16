#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check setup assert path (jsonpath) + params desc empty rate."""
import os, glob, re, json
import yaml

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
API = "/Users/swlim/Desktop/ruijie/api_json/api.json"
ROOT = "/Users/swlim/Desktop/ruijie/SpaceRCDC/rcdc-rcc-module-development-RCC-Space_V1.1_R1"

known = set()
d = json.load(open(API, encoding="utf-8"))
for name, spec in d.get("definitions", {}).items():
    for p in spec.get("properties", {}).keys():
        known.add(p)
FIELD_RE = re.compile(r'(?:private|public|protected)\s+(?!class\b|static\b|final\b)[\w<>\[\],\s\.]+?\s+(\w+)\s*(?:=.*)?;', re.M)
for dp, _, fs in os.walk(ROOT):
    for fn in fs:
        if not fn.endswith(".java"):
            continue
        src = open(os.path.join(dp, fn), encoding="utf-8", errors="ignore").read()
        for m in FIELD_RE.finditer(src):
            known.add(m.group(1))
# wrapper fields
known |= {"status", "message", "msgKey", "msgArgArr", "content", "itemArr", "total"}

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
assert_total = 0
param_total = 0
param_empty = 0
for f in DOC_FILES:
    name = os.path.basename(f)
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    # setup assert
    setup = data.get("setup")
    if isinstance(setup, list):
        for s in setup:
            if not isinstance(s, dict):
                continue
            for a in (s.get("assert") or []):
                if not isinstance(a, dict):
                    continue
                path = a.get("path", "")
                assert_total += 1
                if not isinstance(path, str) or not path.startswith("$"):
                    problems.setdefault(name, []).append(f"assert path 非 \$ 开头: {path}")
                    continue
                m = re.search(r'([A-Za-z0-9_]+)$', path)
                tf = m.group(1) if m else ""
                if tf and tf not in known:
                    problems.setdefault(name, []).append(f"assert path 字段 {tf} 不在 DTO")
    # params desc
    params = data.get("params")
    if isinstance(params, dict):
        for key in ("required", "optional"):
            items = params.get(key)
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict) and "name" in it:
                        param_total += 1
                        if not it.get("desc"):
                            param_empty += 1

print(f"setup assert 总数: {assert_total}")
print(f"assert 问题文件: {len(problems)}")
for name, ps in sorted(problems.items()):
    for p in ps:
        print(f"  {name}: {p}")
print(f"\nparams 总数: {param_total}, desc 空: {param_empty} ({100*param_empty//max(param_total,1)}%)")
