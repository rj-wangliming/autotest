#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fill field_map 'to' by same-name match (from terminal field == body field),
mark non-HTTP endpoints as external. Update field_map.json."""
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
    if isinstance(fr, list):
        # list of field names -> first is primary
        return fr[0] if fr else None
    return None

filled = 0
external = 0
for doc, entries in FM.items():
    body = doc_body.get(doc, set())
    for e in entries:
        if e.get("to"):
            continue
        api = e.get("api", "") or ""
        fr = e.get("from_jsonpath", "")
        # non-HTTP -> mark external
        if api.startswith(("file://", "https://", "http://")) or "{" in api:
            e["external"] = True
            external += 1
            continue
        tf = term_field(fr)
        if tf and tf in body:
            e["to"] = tf
            e["matched_by"] = "same_name"
            filled += 1

json.dump(FM, open(os.path.join(DOCS_DIR, "field_map.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

n_entries = sum(len(v) for v in FM.values())
n_to = sum(1 for v in FM.values() for e in v if e.get("to"))
print(f"本轮同名映射补全: {filled} 条, 标记外部端点: {external} 条")
print(f"field_map 总数: {n_entries}, 含 to: {n_to} ({100*n_to//max(n_entries,1)}%)")
