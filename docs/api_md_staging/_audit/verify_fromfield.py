#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify field_map 'from_jsonpath' terminal field names exist in swagger definitions
or Java DTOs (real response fields)."""
import os, glob, re, json

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
FM = json.load(open(os.path.join(DOCS_DIR, "field_map.json"), encoding="utf-8"))
API = "/Users/swlim/Desktop/ruijie/api_json/api.json"
ROOT = "/Users/swlim/Desktop/ruijie/SpaceRCDC/rcdc-rcc-module-development-RCC-Space_V1.1_R1"

# known field names: swagger defs properties + java dto fields
known = set()
d = json.load(open(API, encoding="utf-8"))
for name, spec in d.get("definitions", {}).items():
    for p in spec.get("properties", {}).keys():
        known.add(p)
# java fields (all private/protected/public fields)
FIELD_RE = re.compile(r'(?:private|public|protected)\s+(?!class\b|static\b|final\b)[\w<>\[\],\s\.]+?\s+(\w+)\s*(?:=.*)?;', re.M)
for dp, _, fs in os.walk(ROOT):
    for fn in fs:
        if not fn.endswith(".java"):
            continue
        src = open(os.path.join(dp, fn), encoding="utf-8", errors="ignore").read()
        for m in FIELD_RE.finditer(src):
            known.add(m.group(1))

def term_field(fr):
    if isinstance(fr, str):
        m = re.search(r'([A-Za-z0-9_]+)$', fr)
        return m.group(1) if m else None
    if isinstance(fr, list):
        return fr
    return None

bad = []
total = 0
for doc, entries in FM.items():
    for e in entries:
        fr = e.get("from_jsonpath")
        tf = term_field(fr)
        if tf is None:
            continue
        fields = [tf] if isinstance(tf, str) else tf
        total += len(fields)
        for f in fields:
            if f not in known:
                bad.append((doc, e.get("api", "")[:40], f))

print(f"from_jsonpath 字段数: {total}")
print(f"不在 swagger/Java DTO 中的字段: {len(bad)}")
for doc, api, f in bad:
    print(f"  {doc} :: {api} | {f}")
if not bad:
    print("✅ 全部 from_jsonpath 字段均为真实响应字段")
