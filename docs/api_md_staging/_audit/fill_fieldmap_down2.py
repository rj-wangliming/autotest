#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final downstream field_map 'to' attempt: cross-document ${prev} reference.
For each downstream entry (specific URL), find the downstream doc's setup step
whose api == this interface's URL, get its extract vars, then find the downstream
request.body field that references those vars via ${prev.*}."""
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

# url -> doc name
url_to_doc = {}
doc_data = {}
for f in glob.glob(os.path.join(DOCS_DIR, "*.md")):
    name = os.path.basename(f).replace(".md", "")
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    url = (data.get("api") or {}).get("url", "")
    if url:
        url_to_doc[url] = name
    doc_data[name] = data

filled = 0
for doc, entries in DOWN.items():
    if doc not in doc_data:
        continue
    src_url = (doc_data[doc].get("api") or {}).get("url", "")
    for e in entries:
        if e.get("to"):
            continue
        api = e.get("api", "")
        m = re.search(r'(?:POST|GET)\s+(/[a-zA-Z0-9/]+)', api)
        if not m:
            continue
        durl = m.group(1)
        ddoc = url_to_doc.get(durl)
        if not ddoc or ddoc not in doc_data:
            continue
        ddata = doc_data[ddoc]
        dbody = (ddata.get("request") or {}).get("body") or {}
        if not isinstance(dbody, dict):
            continue
        # downstream setup steps whose api == src_url -> extract vars
        setup = ddata.get("setup")
        extract_vars = set()
        if isinstance(setup, list):
            for s in setup:
                if not isinstance(s, dict):
                    continue
                if s.get("api") == src_url or ("POST " + src_url) in str(s.get("api", "")) or src_url in str(s.get("api", "")):
                    ext = s.get("extract")
                    if isinstance(ext, dict):
                        extract_vars.update(ext.keys())
                    elif isinstance(ext, list):
                        for x in ext:
                            if isinstance(x, dict) and x.get("var"):
                                extract_vars.add(x["var"])
        if not extract_vars:
            continue
        # downstream body field referencing any extract var via ${prev...var}
        body_str = json.dumps(dbody, ensure_ascii=False)
        for var in extract_vars:
            if re.search(r'\$\{prev\.[^}]*' + re.escape(var) + r'[^}]*\}', body_str):
                # find which field
                for fld, spec in dbody.items():
                    if isinstance(spec, dict) and isinstance(spec.get("value"), str) and var in spec["value"]:
                        e["to"] = fld
                        e["matched_by"] = "cross_doc_prev"
                        filled += 1
                        break
                break

json.dump(DOWN, open(os.path.join(DOCS_DIR, "field_map_downstream.json"), "w",
                     encoding="utf-8"), ensure_ascii=False, indent=1)
n = sum(len(v) for v in DOWN.values())
to = sum(1 for v in DOWN.values() for e in v if e.get("to"))
print("跨文档 prev 引用补全: %d 条" % filled)
print(f"downstream 条目: {n}, 含 to: {to}")
