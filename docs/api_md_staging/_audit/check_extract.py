#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check setup extract jsonpath: all should start with '$' and terminal field
should exist in swagger/Java DTOs."""
import os, glob, re, json
import yaml

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
API = "/Users/swlim/Desktop/ruijie/api_json/api.json"
ROOT = "/Users/swlim/Desktop/ruijie/SpaceRCDC/rcdc-rcc-module-development-RCC-Space_V1.1_R1"

# known fields
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
non_dollar = []
total = 0
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
        jps = []
        if isinstance(ext, dict):
            for var, jp in ext.items():
                jps.append((var, jp))
        elif isinstance(ext, list):
            for e in ext:
                if isinstance(e, dict) and e.get("jsonpath"):
                    jps.append((e.get("var", "?"), e["jsonpath"]))
        for var, jp in jps:
            if not isinstance(jp, str) or not jp:
                problems.setdefault(name, []).append(f"extract {var} jsonpath 为空/非字符串")
                continue
            total += 1
            if not jp.startswith("$"):
                non_dollar.append((name, var, jp[:50]))
                continue
            # terminal field check
            m = re.search(r'([A-Za-z0-9_]+)$', jp)
            tf = m.group(1) if m else ""
            if tf and tf not in known and tf not in ("itemArr", "total", "id", "name", "content"):
                problems.setdefault(name, []).append(f"extract {var} jsonpath 字段 {tf} 不在 DTO 中")

print(f"extract jsonpath 总数: {total}")
print(f"非 \$ 开头: {len(non_dollar)}")
for n, v, jp in non_dollar[:15]:
    print(f"  {n} :: {v} = {jp}")
print(f"字段名不在 DTO 的文件: {len(problems)}")
for name, ps in sorted(problems.items()):
    for p in ps:
        print(f"  {name}: {p}")
