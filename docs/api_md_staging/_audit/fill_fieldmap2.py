#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fill remaining field_map 'to' via deterministic rules:
- upstream api -> resource type -> ID field (cluster/storagePool/network/platform/seat)
- abbreviation (classroomId -> crId)
- teacher/student prefix (classroomStrategyId -> student/teacherClassroomStrategyId)
- nested list (desktopId -> deskList[].deskId)
- matchArr filter -> resolve_via note
"""
import os, glob, re, json
import yaml

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
FM = json.load(open(os.path.join(DOCS_DIR, "field_map.json"), encoding="utf-8"))

def get_fm(lines):
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return None

doc_body = {}
for f in glob.glob(os.path.join(DOCS_DIR, "*.md")):
    name = os.path.basename(f).replace(".md", "")
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    req = data.get("request") or {}
    body = req.get("body") if isinstance(req, dict) else None
    doc_body[name] = set(body.keys()) if isinstance(body, dict) else set()

def term_field(fr):
    if isinstance(fr, str):
        m = re.search(r'([A-Za-z0-9_]+)$', fr)
        return m.group(1) if m else None
    return None

# deterministic rules: (api substring, from field, to field)
API_RULES = [
    ("obtainComputeClusterList", "id", "clusterId"),
    ("storagePool/list", "id", "storagePoolId"),
    ("deskNetwork/list", "id", "networkId"),
    ("platform/list", "id", "platformId"),
    ("/seat/list", "id", "seatId"),
    ("desktop/list", "desktopId", "deskId"),
    ("desktop/tci/list", "desktopId", "deskList[].deskId"),
    ("terminal/list", "teacherTerminalId", "terminalId"),
    ("adGroup/listWithAssignment", "adGroupId", "selectedAdGroupIdList"),
]

filled = 0
resolve_via = 0
for doc, entries in FM.items():
    body = doc_body.get(doc, set())
    for e in entries:
        if e.get("to") or e.get("external"):
            continue
        api = e.get("api", "") or ""
        fr = e.get("from_jsonpath", "")
        tf = term_field(fr)
        # 1. deterministic api->resource rules
        for akey, ff, tt in API_RULES:
            if akey in api and tf == ff and tt in body:
                e["to"] = tt
                e["matched_by"] = "api_rule"
                filled += 1
                break
        if e.get("to"):
            continue
        # 2. abbreviation classroomId -> crId
        if tf == "classroomId" and "crId" in body and "classroomId" not in body:
            e["to"] = "crId"
            e["matched_by"] = "abbrev_crId"
            filled += 1
            continue
        # 3. classroomStrategyId -> student/teacher prefix by doc name
        if tf == "classroomStrategyId":
            if "studentClassroomStrategyId" in body and "teacherClassroomStrategyId" not in body:
                e["to"] = "studentClassroomStrategyId"
                e["matched_by"] = "student_prefix"
                filled += 1
                continue
            if "teacherClassroomStrategyId" in body and "studentClassroomStrategyId" not in body:
                e["to"] = "teacherClassroomStrategyId"
                e["matched_by"] = "teacher_prefix"
                filled += 1
                continue
        # 4. matchArr filter -> resolve_via
        if tf == "id" and any("matchArr" in k for k in body):
            e["resolve_via"] = "matchArr 过滤字段（见该接口 request.body.matchArr[].fieldName）"
            resolve_via += 1

json.dump(FM, open(os.path.join(DOCS_DIR, "field_map.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

n_entries = sum(len(v) for v in FM.values())
n_to = sum(1 for v in FM.values() for e in v if e.get("to"))
print(f"本轮补全: {filled} 条, 标注 resolve_via: {resolve_via} 条")
print(f"field_map 总数: {n_entries}, 含 to: {n_to} ({100*n_to//max(n_entries,1)}%)")
