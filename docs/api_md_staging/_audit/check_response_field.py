#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check response.body fields (incl itemArr[]_ element fields) exist in Java DTOs
or swagger definitions (no ghost/fabricated fields)."""
import os, glob, re, json
import yaml

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
API = "/Users/swlim/Desktop/ruijie/api_json/api.json"
ROOT = "/Users/swlim/Desktop/ruijie/SpaceRCDC/rcdc-rcc-module-development-RCC-Space_V1.1_R1"

# known field names (swagger defs + java DTO fields)
known = set()
d = json.load(open(API, encoding="utf-8"))
for name, spec in d.get("definitions", {}).items():
    for p in spec.get("properties", {}).keys():
        known.add(p)
FIELD_RE = re.compile(r'(?:private|public|protected)\s+(?!class\b|static\b|final\b)[\w<>\[\],\s\.]+?\s+(\w+)\s*(?:=.*)?;', re.M)
for dp, _, fs in os.walk(ROOT):
    for fn in fs:
        if not fn.endswith(".java"):
            continue
        src = open(os.path.join(dp, fn), encoding="utf-8", errors="ignore").read()
        for m in FIELD_RE.finditer(src):
            known.add(m.group(1))
# wrapper + common
known |= {"status", "message", "msgKey", "msgArgArr", "content", "itemArr", "total",
          "taskId", "taskName", "taskDesc", "id", "name", "result", "desc", "state"}

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
    if not isinstance(body, dict):
        continue
    for fld in body.keys():
        # 规范化：去掉 itemArr[]_ / content_ / DTO_ 前缀
        norm = fld
        for prefix in ("itemArr[]_", "content_", "resultArr[]_", "avgUseRateList[]_",
                       "maxUseRateList[]_", "lanTemplateList[]_"):
            if norm.startswith(prefix):
                norm = norm[len(prefix):]
                break
        # 去掉 DTO_ 前缀（clusterInfoDTO_clusterName -> clusterName）
        m = re.match(r'^[A-Za-z]+DTO_(.+)$', norm)
        if m:
            norm = m.group(1)
        if norm in known:
            continue
        if "[]" in norm:
            continue
        # 下划线分隔的（clusterInfoDTO_clusterName 已处理，其他 DTO 前缀）
        if "_" in norm and norm.split("_")[-1] in known:
            continue
        problems.setdefault(name, []).append(f"{fld} -> 规范化为 {norm}，不在 DTO/swagger 中")

print(f"response.body 字段不在 DTO 的文件: {len(problems)}")
for name, ps in sorted(problems.items()):
    for p in ps:
        print(f"  {name}: {p}")
