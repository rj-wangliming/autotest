#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix upstream/downstream/cleanup api fields missing 'POST ' prefix."""
import os, glob, re
import yaml

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
DOC_FILES = sorted(f for f in glob.glob(os.path.join(DOCS_DIR, "*.md"))
                   if os.path.basename(f) not in (
                       "README.md", "SETUP_PARAM_SPEC.md", "business_rules.md",
                       "code_map_all.md", "error_code_map_tci_strategy.md",
                       "修订记录.md", "外部接口清单.md", "用例参数_VDI教师机镜像变更策略.md"))

fixed = []
for f in DOC_FILES:
    name = os.path.basename(f)
    text = open(f, encoding="utf-8").read()
    lines = text.split("\n")
    changed = False
    for i, ln in enumerate(lines):
        # api: /xxx  (缺 POST) -> api: POST /xxx
        m = re.match(r'^(\s*api:\s*)(/[a-zA-Z][^"\']*)$', ln)
        if m and "POST" not in ln and "GET" not in ln and "internal" not in ln and "file:" not in ln and "https:" not in ln:
            lines[i] = m.group(1) + "POST " + m.group(2)
            changed = True
    if changed:
        open(f, "w", encoding="utf-8").write("\n".join(lines))
        fixed.append(name)

print("补 POST 前缀的文件数:", len(fixed))
for n in fixed:
    print("  -", n)
