#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan field_map coverage, setup extract jsonpath, cleanup, and producer-consumer closure."""
import os, glob, re
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

stats = {
    "has_upstream": 0, "upstream_with_field_map": 0, "upstream_total": 0,
    "has_downstream": 0, "downstream_with_field_map": 0, "downstream_total": 0,
    "async_no_polling": 0, "op_no_cleanup": 0, "setup_extract_has_jsonpath": 0,
    "setup_extract_total": 0,
}
details = {}

for f in DOC_FILES:
    name = os.path.basename(f)
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    api = data.get("api") or {}
    url = api.get("url", "")
    # field_map
    for key in ("upstream", "downstream"):
        items = data.get(key)
        if not isinstance(items, list):
            continue
        for it in items:
            if not isinstance(it, dict):
                continue
            if key == "upstream":
                stats["upstream_total"] += 1
                if it.get("field_map"):
                    stats["upstream_with_field_map"] += 1
                elif it.get("produces") or it.get("purpose"):
                    pass
            else:
                stats["downstream_total"] += 1
                if it.get("field_map"):
                    stats["downstream_with_field_map"] += 1
    # setup extract jsonpath
    setup = data.get("setup")
    if isinstance(setup, list):
        for s in setup:
            if not isinstance(s, dict):
                continue
            ext = s.get("extract")
            if isinstance(ext, dict):
                for var, jp in ext.items():
                    stats["setup_extract_total"] += 1
                    if isinstance(jp, str) and jp.startswith("$"):
                        stats["setup_extract_has_jsonpath"] += 1
            elif isinstance(ext, list):
                for e in ext:
                    if isinstance(e, dict) and e.get("jsonpath"):
                        stats["setup_extract_total"] += 1
                        if str(e["jsonpath"]).startswith("$"):
                            stats["setup_extract_has_jsonpath"] += 1
    # cleanup for operational (create/delete/edit etc.)
    cleanup = data.get("cleanup")
    is_op = any(k in url for k in ("/create", "/delete", "/edit", "/add", "/assign", "/update", "/batchCreate", "/batchConfig"))
    if is_op and not cleanup:
        stats["op_no_cleanup"] += 1
        details.setdefault("op_no_cleanup", []).append(name)

print("=== field_map 覆盖 ===")
print(f"upstream 条目总数: {stats['upstream_total']}, 含 field_map: {stats['upstream_with_field_map']}")
print(f"downstream 条目总数: {stats['downstream_total']}, 含 field_map: {stats['downstream_with_field_map']}")
print(f"=== setup extract jsonpath ===")
print(f"extract 总数: {stats['setup_extract_total']}, 含 jsonpath($开头): {stats['setup_extract_has_jsonpath']}")
print(f"=== 操作类接口缺 cleanup ===")
print(f"数量: {stats['op_no_cleanup']}")
for n in details.get("op_no_cleanup", []):
    print(f"  - {n}")
