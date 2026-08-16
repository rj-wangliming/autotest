#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fill remaining field_map 'to' by extract-variable-name == body-field-name rule."""
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

doc_info = {}
for f in glob.glob(os.path.join(DOCS_DIR, "*.md")):
    name = os.path.basename(f).replace(".md", "")
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    req = data.get("request") or {}
    body = req.get("body") if isinstance(req, dict) else None
    body_keys = set(body.keys()) if isinstance(body, dict) else set()
    # extract var -> jsonpath terminal field
    var_to_term = {}
    setup = data.get("setup")
    if isinstance(setup, list):
        for s in setup:
            if not isinstance(s, dict):
                continue
            ext = s.get("extract")
            if isinstance(ext, dict):
                for var, jp in ext.items():
                    m = re.search(r'([A-Za-z0-9_]+)$', str(jp))
                    var_to_term[var] = m.group(1) if m else ""
            elif isinstance(ext, list):
                for e in ext:
                    if isinstance(e, dict) and e.get("var"):
                        m = re.search(r'([A-Za-z0-9_]+)$', str(e.get("jsonpath", "")))
                        var_to_term[e["var"]] = m.group(1) if m else ""
    doc_info[name] = {"body": body_keys, "var_to_term": var_to_term}

def term_field(fr):
    if isinstance(fr, str):
        m = re.search(r'([A-Za-z0-9_]+)$', fr)
        return m.group(1) if m else None
    return None

filled = 0
for doc, entries in FM.items():
    info = doc_info.get(doc, {})
    body = info.get("body", set())
    var_to_term = info.get("var_to_term", {})
    for e in entries:
        if e.get("to") or e.get("external") or e.get("resolve_via"):
            continue
        tf = term_field(e.get("from_jsonpath", ""))
        if not tf:
            continue
        # find extract vars whose jsonpath terminal == tf, and var name in body
        for var, term in var_to_term.items():
            if term == tf and var in body:
                e["to"] = var
                e["matched_by"] = "extract_var_same_name"
                filled += 1
                break

json.dump(FM, open(os.path.join(DOCS_DIR, "field_map.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

n_entries = sum(len(v) for v in FM.values())
n_to = sum(1 for v in FM.values() for e in v if e.get("to"))
print(f"本轮补全: {filled} 条")
print(f"field_map 总数: {n_entries}, 含 to: {n_to} ({100*n_to//max(n_entries,1)}%)")
