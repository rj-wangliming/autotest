#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate downstream field_map (from-side): for each interface, its downstream
consumer APIs + the produced ID fields (from response.body)."""
import os, glob, re, json
import yaml

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
DOC_FILES = sorted(f for f in glob.glob(os.path.join(DOCS_DIR, "*.md"))
                   if os.path.basename(f) not in (
                       "README.md", "SETUP_PARAM_SPEC.md", "business_rules.md",
                       "code_map_all.md", "error_code_map_tci_strategy.md",
                       "修订记录.md", "外部接口清单.md", "用例参数_VDI教师机镜像变更策略.md"))

ID_FIELDS = re.compile(r'(id|taskId|classroomId|strategyId|imageId|desktopId|seatId|terminalId|spaceId|poolId|groupId|userId|lessonId|lessonTaskId|clusterId|storagePoolId|networkId)$', re.I)

def get_fm(lines):
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return None

downstream_fm = {}
for f in DOC_FILES:
    name = os.path.basename(f).replace(".md", "")
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    down = data.get("downstream")
    if not isinstance(down, list):
        continue
    # produced ID fields from response.body (top-level + itemArr[]_ element IDs)
    resp = data.get("response") or {}
    body = resp.get("body") if isinstance(resp, dict) else None
    produced = []
    if isinstance(body, dict):
        for k in body:
            if ID_FIELDS.search(k) and "itemArr[]_" not in k:
                produced.append(k)
    produced = sorted(set(produced))[:6]
    entries = []
    for d in down:
        if not isinstance(d, dict):
            continue
        api = d.get("api", "")
        entries.append({"api": api, "from": produced, "note": d.get("purpose", "")[:60]})
    if entries:
        downstream_fm[name] = entries

out = os.path.join(DOCS_DIR, "field_map_downstream.json")
json.dump(downstream_fm, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
n_docs = len(downstream_fm)
n_entries = sum(len(v) for v in downstream_fm.values())
n_with_from = sum(1 for v in downstream_fm.values() for e in v if e.get("from"))
print(f"下游 field_map 文档数: {n_docs}, 条目: {n_entries}, 含产出字段: {n_with_from}")
print(f"输出: {out}")
