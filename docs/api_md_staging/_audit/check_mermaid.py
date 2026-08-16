#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check Mermaid 依赖关系全景图 completeness: B (central), A (upstream), C (flow), D (downstream)."""
import os, glob, re

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
DOC_FILES = sorted(f for f in glob.glob(os.path.join(DOCS_DIR, "*.md"))
                   if os.path.basename(f) not in (
                       "README.md", "SETUP_PARAM_SPEC.md", "business_rules.md",
                       "code_map_all.md", "error_code_map_tci_strategy.md",
                       "修订记录.md", "外部接口清单.md", "用例参数_VDI教师机镜像变更策略.md"))

problems = {}
total = 0
for f in DOC_FILES:
    name = os.path.basename(f)
    text = open(f, encoding="utf-8").read()
    # find mermaid block
    m = re.search(r'```mermaid\n(.*?)```', text, re.S)
    if not m:
        problems.setdefault(name, []).append("无 mermaid 依赖关系全景图")
        continue
    total += 1
    mm = m.group(1)
    has_b = bool(re.search(r'\bB\[', mm))
    has_a = bool(re.search(r'\bA\d?\[', mm))
    has_c = bool(re.search(r'\bC\d?\[', mm))
    has_d = bool(re.search(r'\bD\d?\[', mm))
    if not has_b:
        problems.setdefault(name, []).append("mermaid 缺中心节点 B")
    if not has_a and "上游" in mm:
        problems.setdefault(name, []).append("mermaid 上游节缺 A 节点")
    if not has_c:
        problems.setdefault(name, []).append("mermaid 缺内部流程 C 节点")
    if not has_d and "下游" in mm:
        problems.setdefault(name, []).append("mermaid 下游节缺 D 节点")

print(f"有 mermaid 图的接口: {total}")
print(f"图不完整的文件: {len(problems)}")
for name, ps in sorted(problems.items()):
    for p in ps:
        print(f"  {name}: {p}")
