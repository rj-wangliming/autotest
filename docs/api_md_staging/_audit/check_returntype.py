#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check doc api.return_type / response wrapper vs Java method return type."""
import os, glob, re
import yaml

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
ROOT = "/Users/swlim/Desktop/ruijie/SpaceRCDC/rcdc-rcc-module-development-RCC-Space_V1.1_R1"

# java url -> return_type
java_rt = {}
for dp, _, fs in os.walk(ROOT):
    for fn in fs:
        if not fn.endswith("Controller.java"):
            continue
        src = open(os.path.join(dp, fn), encoding="utf-8", errors="ignore").read()
        cm = re.search(r'public\s+(?:abstract\s+)?class\s+\w+', src)
        base = ""
        if cm:
            m = re.search(r'@RequestMapping\(\s*(?:value\s*=\s*)?["\']([^"\']*)["\']', src[:cm.start()])
            if m:
                base = m.group(1).strip()
                if not base.startswith("/"):
                    base = "/" + base
        body = src[cm.start():] if cm else src
        for m in re.finditer(r'@(?:RequestMapping|PostMapping|GetMapping|PutMapping|DeleteMapping)\(\s*([^)]*)\)', body):
            attr = m.group(1)
            segs = re.findall(r'["\']([^"\']*)["\']', attr)
            tail = body[m.end():]
            sig = re.search(r'public\s+([\w<>\[\],\s\.\?]+?)\s+(\w+)\s*\(', tail)
            if not sig:
                continue
            rt = sig.group(1).strip()
            for seg in segs:
                url = (base.rstrip("/") + "/" + seg.lstrip("/")) if seg else base
                if not url.startswith("/"):
                    url = "/" + url
                java_rt.setdefault(url, set()).add(rt)

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

# normalize wrapper: map doc return_type / java return type to wrapper + content
def norm_rt(rt):
    rt = (rt or "").strip()
    # strip generic
    base = re.sub(r'<.*>', '', rt)
    return base

problems = {}
for f in DOC_FILES:
    name = os.path.basename(f)
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    url = (data.get("api") or {}).get("url", "")
    doc_rt = (data.get("api") or {}).get("return_type", "")
    resp_wrapper = ((data.get("response") or {}).get("wrapper") or {})
    if url not in java_rt:
        continue
    jrts = java_rt[url]
    # java wrapper = base return type
    jwrappers = {norm_rt(r) for r in jrts}
    # doc wrapper from response.wrapper keys (status/message/content => DefaultWebResponse-like)
    # or from return_type
    doc_w = norm_rt(doc_rt)
    # mismatch only if doc declares a return_type and it differs in wrapper name
    if doc_w and jwrappers and doc_w not in jwrappers and not any(doc_w in j or j in doc_w for j in jwrappers):
        problems.setdefault(name, []).append(f"文档 return_type={doc_rt} vs Java={sorted(jrts)}")

print(f"Java 端点: {len(java_rt)}")
print(f"return_type 不一致: {len(problems)}")
for name, ps in sorted(problems.items()):
    print(f"\n{name}:")
    for p in ps:
        print(f"  - {p}")
if not problems:
    print("✅ return_type 全部一致（或文档未声明 return_type）")
