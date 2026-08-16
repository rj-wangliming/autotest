#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify field_map 'to' fields exist in each doc's request.body (mapping validity)."""
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

# build doc -> request.body field set
doc_fields = {}
for f in glob.glob(os.path.join(DOCS_DIR, "*.md")):
    name = os.path.basename(f).replace(".md", "")
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    req = data.get("request") or {}
    body = req.get("body") if isinstance(req, dict) else None
    if isinstance(body, dict):
        doc_fields[name] = set(body.keys())
    else:
        doc_fields[name] = set()

bad = []
total_to = 0
for doc, entries in FM.items():
    body = doc_fields.get(doc, set())
    for e in entries:
        to = e.get("to")
        if not to:
            continue
        total_to += 1
        # nested path (a.b.c) -> check top-level field; array element (x[].y) is a full field name
        top = to if "[]" in to else to.split(".")[0]
        if top not in body:
            bad.append((doc, e.get("api", ""), e.get("from_jsonpath", ""), to))

print(f"field_map 含 to 映射: {total_to} 条")
print(f"to 字段不在 request.body 的: {len(bad)} 条")
for doc, api, fr, to in bad:
    print(f"  {doc} :: {api[:40]} | from={fr[:35]} | to={to} (request.body 无此字段)")
if not bad:
    print("✅ 全部 to 字段均为真实入参")
