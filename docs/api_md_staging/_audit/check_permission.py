#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check doc api.permission matches Java method's actual @EnableAuthority annotation."""
import os, glob, re
import yaml

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
ROOT = "/Users/swlim/Desktop/ruijie/SpaceRCDC/rcdc-rcc-module-development-RCC-Space_V1.1_R1"

# build url -> method-level permission annotation (scan the annotation block above each method)
java_perm = {}  # url -> set of permission-ish annotations
for dp, _, fs in os.walk(ROOT):
    for fn in fs:
        if not fn.endswith("Controller.java"):
            continue
        src = open(os.path.join(dp, fn), encoding="utf-8", errors="ignore").read()
        cm = re.search(r'public\s+(?:abstract\s+)?class\s+\w+', src)
        base = ""
        class_anns = set()
        if cm:
            m = re.search(r'@RequestMapping\(\s*(?:value\s*=\s*)?["\']([^"\']*)["\']', src[:cm.start()])
            if m:
                base = m.group(1).strip()
                if not base.startswith("/"):
                    base = "/" + base
            class_anns = set(re.findall(r'@(EnableAuthority|OneTimeTokenRequired)\b', src[:cm.start()]))
        body = src[cm.start():] if cm else src
        body_lines = body.split("\n")
        # line numbers (1-based within body) of method signatures and annotations
        sig_lines = []  # list of line numbers (1-based in body)
        for i, ln in enumerate(body_lines, 1):
            if re.search(r'public\s+[\w<>\[\],\s\.\?]+?\s+\w+\s*\(', ln):
                sig_lines.append(i)
        if not sig_lines:
            continue
        # annotate each mapping/authority annotation with its owning method = first sig line after it
        def owner_of(line_no):
            for s in sig_lines:
                if s > line_no:
                    return s
            return sig_lines[-1]
        # collect per-method (owning sig line) annotations
        method_anns = {}
        for i, ln in enumerate(body_lines, 1):
            m_ann = re.search(r'@(EnableAuthority|OneTimeTokenRequired)\b', ln)
            if m_ann:
                ow = owner_of(i)
                method_anns.setdefault(ow, set()).add(m_ann.group(1))
            m_map = re.search(r'@(?:RequestMapping|PostMapping|GetMapping|PutMapping|DeleteMapping)\(\s*([^)]*)\)', ln)
            if m_map:
                ow = owner_of(i)
                method_anns.setdefault(ow, set()).add("__MAP__" + m_map.group(1))
        # now build url -> permissions
        for ow, anns in method_anns.items():
            perms = {a for a in anns if not a.startswith("__MAP__")}
            for a in anns:
                if a.startswith("__MAP__"):
                    attr = a[len("__MAP__"):]
                    segs = re.findall(r'["\']([^"\']*)["\']', attr)
                    for seg in segs:
                        url = (base.rstrip("/") + "/" + seg.lstrip("/")) if seg else base
                        if not url.startswith("/"):
                            url = "/" + url
                        java_perm.setdefault(url, set()).update(perms | class_anns)

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

problems = {}
for f in DOC_FILES:
    name = os.path.basename(f)
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    url = (data.get("api") or {}).get("url", "")
    doc_perm = (data.get("api") or {}).get("permission", "")
    if url not in java_perm:
        continue
    jann = java_perm[url]
    java_has_auth = "EnableAuthority" in jann
    java_has_ott = "OneTimeTokenRequired" in jann
    # doc permission semantics
    doc_says_auth = "@EnableAuthority" in str(doc_perm) or "EnableAuthority" in str(doc_perm)
    doc_says_none = doc_perm in ("无", "", None) or "无" in str(doc_perm) or "不需要" in str(doc_perm) or "无需" in str(doc_perm)
    doc_says_session = "user_session" in str(doc_perm) or "SessionContext" in str(doc_perm) or "需登录" in str(doc_perm)
    # mismatch detection
    if java_has_auth and doc_says_none:
        problems.setdefault(name, []).append(f"Java 有 @EnableAuthority 但文档标注无权限: {doc_perm}")
    elif not java_has_auth and doc_says_auth:
        problems.setdefault(name, []).append(f"Java 无 @EnableAuthority 但文档标注 @EnableAuthority")
    if java_has_ott and "OneTimeToken" not in str(doc_perm):
        problems.setdefault(name, []).append(f"Java 有 @OneTimeTokenRequired 但文档未标注")

print(f"Java 端点: {len(java_perm)}")
print(f"权限注解不一致的文件: {len(problems)}")
for name, ps in sorted(problems.items()):
    print(f"\n{name}:")
    for p in ps:
        print(f"  - {p}")
if not problems:
    print("✅ 权限注解全部一致")
