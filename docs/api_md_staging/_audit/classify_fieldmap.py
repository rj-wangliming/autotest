#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Classify the 104 field_map entries lacking 'to': (a) validation interfaces (no ID input),
(b) non-HTTP endpoints, (c) produces-but-unreferenced (potential gaps)."""
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

# build doc -> request.body fields
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

cat = {"validation": [], "non_http": [], "unreferenced": []}
for doc, entries in FM.items():
    body = doc_body.get(doc, set())
    for e in entries:
        if e.get("to"):
            continue
        api = e.get("api", "") or ""
        fr = e.get("from_jsonpath", "") or ""
        fr_str = fr if isinstance(fr, str) else json.dumps(fr, ensure_ascii=False)
        # non-HTTP endpoints
        if api.startswith(("file://", "https://", "http://")) or "{" in api:
            cat["non_http"].append((doc, api, fr_str))
            continue
        # validation: produces field name NOT in body and body has no ID-like field
        tf = re.search(r'([A-Za-z0-9_]+)$', fr_str)
        field = tf.group(1) if tf else ""
        id_like = [k for k in body if re.search(r'(id|Id)$', k)]
        if not id_like:
            cat["validation"].append((doc, api, fr_str))
        else:
            cat["unreferenced"].append((doc, api, fr_str, sorted(id_like)[:6]))

print(f"缺 to 的 field_map 条目分类:")
print(f"  ① 校验类接口(无 ID 输入): {len(cat['validation'])}")
print(f"  ② 非 HTTP 端点: {len(cat['non_http'])}")
print(f"  ③ produces 有但未引用(潜在遗漏): {len(cat['unreferenced'])}")
print("\n--- ② 非 HTTP 端点 ---")
for doc, api, fr in cat["non_http"]:
    print(f"  {doc} :: {api[:50]} | {fr[:40]}")
print("\n--- ③ 潜在遗漏 ---")
for doc, api, fr, ids in cat["unreferenced"]:
    print(f"  {doc} :: {api[:45]} | from={fr[:35]} | body含ID字段={ids}")
