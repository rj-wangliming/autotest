#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fill downstream field_map 'to' by same-name match for specific-URL entries
(only concrete resource IDs, not generic 'id')."""
import os, glob, re, json
import yaml

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
DOWN = json.load(open(os.path.join(DOCS_DIR, "field_map_downstream.json"), encoding="utf-8"))

def get_fm(lines):
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return None

url_to_doc = {}
doc_body = {}
for f in glob.glob(os.path.join(DOCS_DIR, "*.md")):
    name = os.path.basename(f).replace(".md", "")
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    url = (data.get("api") or {}).get("url", "")
    if url:
        url_to_doc[url] = name
    req = data.get("request") or {}
    body = req.get("body") if isinstance(req, dict) else None
    doc_body[name] = set(body.keys()) if isinstance(body, dict) else set()

GENERIC = {"id", "idArr"}  # generic id is ambiguous, skip

filled = 0
for doc, entries in DOWN.items():
    for e in entries:
        if e.get("to"):
            continue
        api = e.get("api", "")
        froms = e.get("from", [])
        if not froms:
            continue
        m = re.search(r'(?:POST|GET)\s+(/[a-zA-Z0-9/]+)', api)
        if not m:
            continue
        durl = m.group(1)
        ddoc = url_to_doc.get(durl)
        if not ddoc:
            continue
        dbody = doc_body.get(ddoc, set())
        for fr in froms:
            if fr in GENERIC:
                continue
            if fr in dbody:
                e["to"] = fr
                e["matched_by"] = "same_name_downstream"
                filled += 1
                break

json.dump(DOWN, open(os.path.join(DOCS_DIR, "field_map_downstream.json"), "w",
                     encoding="utf-8"), ensure_ascii=False, indent=1)
n = sum(len(v) for v in DOWN.values())
to = sum(1 for v in DOWN.values() for e in v if e.get("to"))
print(f"下游同名匹配补全: {filled} 条")
print(f"downstream 条目: {n}, 含 to: {to}")
