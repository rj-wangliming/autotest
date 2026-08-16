#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check doc constraint @Size/@Range min/max values match Java DTO annotations."""
import os, glob, re
import yaml

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
ROOT = "/Users/swlim/Desktop/ruijie/SpaceRCDC/rcdc-rcc-module-development-RCC-Space_V1.1_R1"

# ---- extract DTO field annotations (name -> {field: {ann: detail}}) ----
FIELD_RE = re.compile(
    r'((?:(?:@\w+(?:\([^)]*\))?)\s*)*)(?:private|public|protected)\s+'
    r'(?!class\b|static\b|final\b|interface\b|enum\b)'
    r'([\w<>\[\],\s\.]+?)\s+(\w+)\s*(?:=\s*[^;]+)?;', re.M)
PKG_RE = re.compile(
    r'((?:(?:@\w+(?:\([^)]*\))?)\s*)+)'
    r'(?!class\b|static\b|final\b|interface\b|enum\b|private\b|public\b|protected\b)'
    r'([\w<>\[\],\s\.]+?)\s+(\w+)\s*(?:=\s*[^;]+)?;', re.M)

dto = {}
for dp, _, fs in os.walk(ROOT):
    for fn in fs:
        if not fn.endswith(".java"):
            continue
        src = open(os.path.join(dp, fn), encoding="utf-8", errors="ignore").read()
        for cm in re.finditer(r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)(?:<[^>]*>)?\s*'
                              r'(?:extends\s+([\w\.]+))?\s*(?:implements\s+[\w\.,\s<>]+)?\s*\{', src):
            cname = cm.group(1)
            body = src[cm.end():]
            nxt = re.search(r'\n\s*(?:public\s+|protected\s+|private\s+)?(?:abstract\s+|static\s+|final\s+)*(?:class|interface|enum)\s+\w+', body)
            body = body[:nxt.start()] if nxt else body
            fields = {}
            for fre in (FIELD_RE, PKG_RE):
                for m in fre.finditer(body):
                    ann = m.group(1)
                    details = dict(re.findall(r'@(\w+)(?:\(([^)]*)\))?', ann))
                    fields[m.group(3)] = details
            dto.setdefault(cname, {}).update(fields)

def resolve(cname, depth=0):
    if depth > 8 or cname not in dto:
        return {}
    # parent lookup needs parent info; skip (fields usually in same class or known parent)
    return dto[cname]

def parse_doc_constraint(s):
    out = {}
    for kind, pat in (("Size", r'@Size\(([^)]*)\)'), ("Range", r'@Range\(([^)]*)\)'),
                      ("NotBlank", r'@NotBlank'), ("NotNull", r'@NotNull'), ("NotEmpty", r'@NotEmpty')):
        m = re.search(pat, s or "")
        if m:
            out[kind] = m.group(1) if m.lastindex else ""
    return out

def num(v):
    v = (v or "").strip().strip('"\'')
    return v

def parse_range(s):
    """Parse @Range(...) args -> (min, max) supporting three forms:
    min=X,max=Y | a-b | a,b (positional)."""
    if not s:
        return None, None
    s = s.strip()
    mn = re.search(r'min\s*=\s*"?([^,"\s\)]+)', s)
    mx = re.search(r'max\s*=\s*"?([^,"\s\)]+)', s)
    if mn or mx:
        return num(mn.group(1)) if mn else None, num(mx.group(1)) if mx else None
    # strip leading '@Range(' already removed by caller; handle a-b or a,b
    inner = s.strip("()")
    if "-" in inner and "," not in inner:
        parts = inner.split("-")
        return num(parts[0]), num(parts[-1])
    if "," in inner:
        parts = inner.split(",")
        return num(parts[0]), num(parts[1])
    return None, None

DOC_FILES = sorted(f for f in glob.glob(os.path.join(DOCS_DIR, "*.md"))
                   if os.path.basename(f) not in (
                       "README.md", "SETUP_PARAM_SPEC.md", "business_rules.md",
                       "code_map_all.md", "error_code_map_tci_strategy.md",
                       "修订记录.md", "外部接口清单.md", "用例参数_VDI教师机镜像变更策略.md"))

problems = {}
checked = 0
for f in DOC_FILES:
    name = os.path.basename(f)
    lines = open(f, encoding="utf-8").read().split("\n")
    if lines[0].strip() != "---":
        continue
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            block = "\n".join(lines[1:i]); break
    data = yaml.safe_load(block)
    req = data.get("request") or {}
    dto_name = (req.get("dto") or "").split("（")[0].split("(")[0].strip()
    body = req.get("body") if isinstance(req, dict) else None
    if not isinstance(body, dict) or dto_name not in dto:
        continue
    jf = resolve(dto_name)
    for fname, spec in body.items():
        if not isinstance(spec, dict):
            continue
        constraint = spec.get("constraint") or ""
        dc = parse_doc_constraint(constraint)
        jann = jf.get(fname, {})
        for kind in ("Size", "Range"):
            if kind not in dc or kind not in jann:
                continue
            checked += 1
            dm, dx = parse_range(dc[kind])
            jm, jx = parse_range(jann[kind])
            if dm != jm or dx != jx:
                problems.setdefault(name, []).append(
                    f"{fname} @{kind}: 文档(min={dm},max={dx}) ≠ Java(min={jm},max={jx})")
print(f"检查的 @Size/@Range 字段数: {checked}")
print(f"constraint 不一致的文件: {len(problems)}")
for name, ps in sorted(problems.items()):
    print(f"\n{name}:")
    for p in ps:
        print(f"  - {p}")
if not problems:
    print("✅ constraint 值全部一致")
