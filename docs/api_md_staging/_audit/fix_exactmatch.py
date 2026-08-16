#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix exactMatchArr elements: type/fieldName/matchRule -> name (ExactMatch = name+valueArr)."""
import re

DOCS = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
FILES = ["rcc_admin_dataPermission_edit.md", "rcc_dashboard_statistics_spaceHistory.md",
         "rcc_space_delete.md", "rcc_space_detail.md", "rcc_space_edit.md",
         "rcc_space_forceWakeUp.md"]

for f in FILES:
    path = f"{DOCS}/{f}"
    lines = open(path, encoding="utf-8").read().split("\n")
    out = []
    i = 0
    changed = False
    while i < len(lines):
        ln = lines[i]
        m = re.match(r'^(\s*)exactMatchArr:\s*$', ln)
        if not m:
            out.append(ln)
            i += 1
            continue
        indent = len(m.group(1))
        out.append(ln)
        i += 1
        # 处理块内行
        while i < len(lines):
            ln2 = lines[i]
            # 块结束：缩进严格小于 exactMatchArr 缩进（列表项缩进 == indent 属块内）
            if ln2.strip() and len(ln2) - len(ln2.lstrip()) < indent:
                break
            # 空行或注释保留
            if not ln2.strip():
                out.append(ln2)
                i += 1
                continue
            # 列表项 - type: EXACT -> 记 pending，下一行 fieldName 改为 - name
            m2 = re.match(r'^(\s*)- type:\s*EXACT\s*$', ln2)
            if m2:
                item_indent = m2.group(1)
                # 找下一行 fieldName
                if i + 1 < len(lines):
                    m3 = re.match(r'^\s*fieldName:\s*(\S+)\s*$', lines[i + 1])
                    if m3:
                        out.append(f"{item_indent}- name: {m3.group(1)}")
                        i += 2  # 跳过 type 和 fieldName 行
                        changed = True
                        continue
            # matchRule 行删除
            if re.match(r'^\s*matchRule:', ln2):
                i += 1
                changed = True
                continue
            out.append(ln2)
            i += 1
    open(path, "w", encoding="utf-8").write("\n".join(out))
    print(f"{f}: {'已修复' if changed else '无变化'}")
