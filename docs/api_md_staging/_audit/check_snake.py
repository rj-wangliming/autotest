#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skill #16: check doc request/response.body field names for snake_case
(should be camelCase matching Java DTO)."""
import glob, os, re, yaml

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"

def get_fm(lines):
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return None

snake = {}
for f in glob.glob(os.path.join(DOCS_DIR, "*.md")):
    name = os.path.basename(f)
    if name in ("README.md", "SETUP_PARAM_SPEC.md", "business_rules.md",
                "code_map_all.md", "error_code_map_tci_strategy.md",
                "修订记录.md", "外部接口清单.md", "用例参数_VDI教师机镜像变更策略.md"):
        continue
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    for sec in ("request", "response"):
        s = data.get(sec) or {}
        body = s.get("body") if isinstance(s, dict) else None
        if not isinstance(body, dict):
            continue
        for k in body:
            if "_" in k and not k.startswith("itemArr[]_") and "[]" not in k and "$" not in k:
                snake.setdefault(name, []).append(k)

print("含下划线字段名的文档数:", len(snake))
for name, ks in sorted(snake.items()):
    print(f"  {name}: {ks[:10]}")
if not snake:
    print("✅ 无 snake_case 字段名（均为 camelCase）")
