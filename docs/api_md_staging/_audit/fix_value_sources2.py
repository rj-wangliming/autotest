#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add value/generated_by to remaining required fields."""
import os
DOCS = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"

FIXES = [
    ("rcc_classroom_cmrcef_lesson_start.md",
     "      description: 由@ClassroomCef拦截器校验（CMR 专用加密 TOKEN，需测试环境提供/注入）",
     "      description: 由@ClassroomCef拦截器校验（CMR 专用加密 TOKEN，需测试环境提供/注入）\n      generated_by: true"),
    ("rco_admin_loginAdmin.md",
     "      description: 请求时间戳（毫秒），每次登录必须生成新值",
     "      description: 请求时间戳（毫秒），每次登录必须生成新值\n      generated_by: true"),
    ("rcc_classroom_desktop_tci_list.md",
     "      description: 包含 classroomId 精确匹配条件",
     "      description: 包含 classroomId 精确匹配条件\n      value: ${prev.query_classroom.output.classroomId}"),
    ("space_strategy_tci_edit.md",
     "      description: 系统盘大小（关联镜像时只可扩大）",
     "      description: 系统盘大小（关联镜像时只可扩大）\n      value: ${param.system_size}"),
    ("space_strategy_tci_edit.md",
     "      description: 平台策略组（更新时回填）",
     "      description: 平台策略组（更新时回填）\n      generated_by: true"),
    ("space_strategygroup_vdi_edit.md",
     "      description: 系统盘大小",
     "      description: 系统盘大小\n      value: ${param.system_size}"),
    ("space_strategygroup_vdi_edit.md",
     "      description: CPU 核数",
     "      description: CPU 核数\n      value: ${param.cpu}"),
    ("space_strategygroup_vdi_edit.md",
     "      description: 平台策略组（更新时回填）",
     "      description: 平台策略组（更新时回填）\n      generated_by: true"),
]

for fname, old, new in FIXES:
    path = os.path.join(DOCS, fname)
    text = open(path, encoding="utf-8").read()
    cnt = text.count(old)
    if cnt != 1:
        print(f"FAIL count={cnt} {fname} :: {old[:40]}")
        continue
    text = text.replace(old, new)
    open(path, "w", encoding="utf-8").write(text)
    print(f"OK   {fname} :: {old[:40]}")
