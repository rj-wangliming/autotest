#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append '（取第一条，无名称过滤）' to purpose of env-resource [0]-extract steps."""
import os, glob

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
DOC_FILES = sorted(f for f in glob.glob(os.path.join(DOCS_DIR, "*.md"))
                   if os.path.basename(f) not in (
                       "README.md", "SETUP_PARAM_SPEC.md", "business_rules.md",
                       "code_map_all.md", "error_code_map_tci_strategy.md",
                       "修订记录.md", "外部接口清单.md", "用例参数_VDI教师机镜像变更策略.md"))

MARK = "（取第一条，无名称过滤）"
# exact purpose strings to annotate
TARGETS = [
    "获取计算集群ID与云平台ID",
    "获取存储池ID（镜像分配用）",
    "获取网络ID（镜像分配用）",
]

fixed = []
for f in DOC_FILES:
    name = os.path.basename(f)
    text = open(f, encoding="utf-8").read()
    changed = False
    for t in TARGETS:
        if t in text and (t + MARK) not in text:
            text = text.replace(t, t + MARK)
            changed = True
    if changed:
        open(f, "w", encoding="utf-8").write(text)
        fixed.append(name)

print("标注补充的文件数:", len(fixed))
for n in fixed:
    print("  -", n)
