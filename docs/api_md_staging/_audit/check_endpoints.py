#!/usr/bin/env python3
"""Verify referenced endpoint URLs exist in source @RequestMapping combinations."""
import os, re, subprocess, sys

ROOT = "/Users/swlim/Desktop/ruijie/SpaceRCDC/rcdc-rcc-module-development-RCC-Space_V1.1_R1"

# Collect all controllers and their class-level + method-level mappings
ctrls = subprocess.run(
    ["find", ROOT, "-name", "*Controller.java"], capture_output=True, text=True
).stdout.split()

endpoints = set()
for path in ctrls:
    src = open(path, encoding="utf-8", errors="ignore").read()
    # class-level mapping: @RequestMapping in the annotation block right before 'public class'
    cls_m = None
    cm = re.search(r'public class', src)
    if cm:
        head = src[:cm.start()]
        # last @RequestMapping occurrence before class declaration
        for cls_m2 in re.finditer(r'@RequestMapping\(\s*(?:value\s*=\s*)?"([^"]+)"', head):
            cls_m = cls_m2
    base = cls_m.group(1) if cls_m else ""
    # method-level mappings: after class declaration
    body = src[cm.start():] if cm else src
    for m in re.finditer(r'@(?:Request|Post|Get)Mapping\(([^)]*)\)', body):
        q = re.search(r'"([^"]*)"', m.group(1))
        seg = q.group(1) if q else ""
        full = (base.rstrip("/") + "/" + seg.lstrip("/")) if seg else base
        if not full.startswith("/"):
            full = "/" + full
        endpoints.add(full)

# Read doc-referenced endpoints
docs = sys.argv[1:]
refs = set()
pat = re.compile(r"(?:POST|GET) (/[a-zA-Z0-9/]+)")
for d in docs:
    text = open(d, encoding="utf-8").read()
    refs.update(pat.findall(text))

print(f"source endpoints: {len(endpoints)}, doc refs: {len(refs)}")
print()
missing = []
for r in sorted(refs):
    if r in endpoints:
        pass
    else:
        # try prefix match (some mappings use path variables or sub-paths)
        close = [e for e in endpoints if e.startswith(r) or r.startswith(e)]
        missing.append((r, close[:3]))

if not missing:
    print("ALL doc-referenced endpoints exist in source ✅")
else:
    print(f"{len(missing)} referenced endpoints NOT found exactly:")
    for r, close in missing:
        print(f"  ❌ {r}" + (f"  (nearby: {close})" if close else "  (no nearby mapping)"))
