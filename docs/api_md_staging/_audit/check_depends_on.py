#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check cleanup.depends_on referencing content.xxx fields that don't exist in
response.body (async create returns only taskId, business ID must come from query)."""
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

problems = {}
for f in DOC_FILES:
    name = os.path.basename(f)
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    resp = data.get("response") or {}
    body = resp.get("body") if isinstance(resp, dict) else None
    body_fields = set(body.keys()) if isinstance(body, dict) else set()
    # content.fields nested
    c = body.get("content") if isinstance(body, dict) else None
    if isinstance(c, dict):
        f2 = c.get("fields")
        if isinstance(f2, dict):
            body_fields |= set(f2.keys())
        elif isinstance(f2, list):
            body_fields |= {x for x in f2 if isinstance(x, str)}
    cleanup = data.get("cleanup")
    if not isinstance(cleanup, list):
        continue
    for it in cleanup:
        if not isinstance(it, dict):
            continue
        dep = it.get("depends_on", "")
        if not isinstance(dep, str):
            continue
        # 引用 content.xxx / 轮询终态后 等
        for m in re.finditer(r'content\.([A-Za-z0-9_]+)', dep):
            fld = m.group(1)
            if fld not in body_fields and fld not in ("taskId",):
                problems.setdefault(name, []).append(
                    f"cleanup.depends_on 引用响应不存在的字段 content.{fld}（响应 body 字段: {sorted(body_fields)[:10]}）")

print(f"depends_on 引用不存在的响应字段的文件: {len(problems)}")
for name, ps in sorted(problems.items()):
    for p in ps:
        print(f"  {name}: {p}")
