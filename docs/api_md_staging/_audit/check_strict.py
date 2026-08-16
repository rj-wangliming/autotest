#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skill #30 strict checks: request.body merged fields, '---#' delimiter glue,
runs of 4+ hyphens, front-matter starts with lone '---'."""
import os, glob, re

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
DOC_FILES = sorted(f for f in glob.glob(os.path.join(DOCS_DIR, "*.md"))
                   if os.path.basename(f) not in (
                       "README.md", "SETUP_PARAM_SPEC.md", "business_rules.md",
                       "code_map_all.md", "error_code_map_tci_strategy.md",
                       "修订记录.md", "外部接口清单.md", "用例参数_VDI教师机镜像变更策略.md"))

problems = {}
for f in DOC_FILES:
    name = os.path.basename(f)
    text = open(f, encoding="utf-8").read()
    # (a) file starts with lone ---
    if not text.startswith("---\n"):
        problems.setdefault(name, []).append("文件不以独立 --- 开头")
    # (b) no '---#' glue
    for m in re.finditer(r'---#', text):
        problems.setdefault(name, []).append(f"发现 '---#' 粘连（行 {text[:m.start()].count(chr(10))+1}）")
    # (c) no runs of 4+ hyphens
    for m in re.finditer(r'^\-{4,}\s*$', text, re.M):
        problems.setdefault(name, []).append(f"发现 4+ 连字符行（行 {text[:m.start()].count(chr(10))+1}）")
    # (d) request.body field name containing '/'
    for m in re.finditer(r'^\s{4}([A-Za-z0-9_]+/[A-Za-z0-9_/]+):\s*$', text, re.M):
        problems.setdefault(name, []).append(f"request.body 字段名含'/': {m.group(1)}")
    # (e) placeholder rows
    for m in re.finditer(r'^\s{4}（[^）]+）:\s*$', text, re.M):
        problems.setdefault(name, []).append(f"占位符字段行: {m.group(0).strip()}")

print(f"检查文件: {len(DOC_FILES)}")
print(f"有问题的文件: {len(problems)}")
for name, ps in sorted(problems.items()):
    print(f"\n{name}:")
    for p in ps:
        print(f"  - {p}")
if not problems:
    print("✅ 全部通过")
