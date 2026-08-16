#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skill #4: [0]-extract steps without name-filter must have purpose marked
'取第一条/无名称过滤'. Report those missing the mark."""
import os, glob, re, json
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

need_mark = []
for f in DOC_FILES:
    name = os.path.basename(f)
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    setup = data.get("setup")
    if not isinstance(setup, list):
        continue
    for s in setup:
        if not isinstance(s, dict):
            continue
        ext = s.get("extract")
        jps = []
        if isinstance(ext, dict):
            jps = list(ext.values())
        elif isinstance(ext, list):
            for e in ext:
                if isinstance(e, dict) and e.get("jsonpath"):
                    jps.append(e["jsonpath"])
        if not any(isinstance(j, str) and "[0]" in j for j in jps):
            continue
        req = s.get("request") or {}
        body = req.get("body") if isinstance(req, dict) else None
        body_str = json.dumps(body, ensure_ascii=False) if body is not None else ""
        if re.search(r'matchArr|exactMatchArr|searchKeyword', body_str):
            continue
        purpose = s.get("purpose", "") or ""
        if "取第一条" in purpose or "无名称过滤" in purpose or "第一条" in purpose:
            continue
        if "过滤" in purpose or "按名" in purpose or "按名称" in purpose:
            continue
        need_mark.append((name, s.get("name", "?"), s.get("api", "?"), purpose[:30]))

print(f"需补充'取第一条'标注的步骤: {len(need_mark)}")
for name, step, api, pur in need_mark:
    print(f"  - {name} :: {step} ({api})  purpose={pur}")
