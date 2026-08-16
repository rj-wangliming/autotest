#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Move PARTIAL_SUCCESS from failure to success in polling.terminal_states."""
import glob, os

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"

fixed = []
for f in glob.glob(os.path.join(DOCS_DIR, "*.md")):
    name = os.path.basename(f)
    if name in ("README.md", "SETUP_PARAM_SPEC.md", "business_rules.md",
                "code_map_all.md", "error_code_map_tci_strategy.md",
                "修订记录.md", "外部接口清单.md", "用例参数_VDI教师机镜像变更策略.md"):
        continue
    t = open(f, encoding="utf-8").read()
    orig = t
    # 1. 标准结构：failure 删 PARTIAL_SUCCESS
    t = t.replace("    failure:\n    - FAILURE\n    - PARTIAL_SUCCESS\n",
                  "    failure:\n    - FAILURE\n")
    # 2. fail 结构：fail 改 failure，删 PARTIAL_SUCCESS
    t = t.replace("    fail:\n    - FAILURE\n    - PARTIAL_SUCCESS\n",
                  "    failure:\n    - FAILURE\n")
    # 3. success 加 PARTIAL_SUCCESS（若还没有）
    if "    - PARTIAL_SUCCESS\n" in t and "    success:\n    - SUCCESS\n    - PARTIAL_SUCCESS\n" not in t:
        t = t.replace("    success:\n    - SUCCESS\n",
                      "    success:\n    - SUCCESS\n    - PARTIAL_SUCCESS\n")
    if t != orig:
        open(f, "w", encoding="utf-8").write(t)
        fixed.append(name)

print("修复文件数:", len(fixed))
for n in fixed:
    print("  -", n)
