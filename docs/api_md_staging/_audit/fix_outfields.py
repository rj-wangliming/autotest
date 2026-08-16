#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix: append flat fields present in 出参详情 table but missing from front-matter
response.body. Nested (a.b) and itemArr[]-style fields are skipped."""
import os, glob, re
import yaml

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
DOC_FILES = sorted(f for f in glob.glob(os.path.join(DOCS_DIR, "*.md"))
                   if os.path.basename(f) not in (
                       "README.md", "SETUP_PARAM_SPEC.md", "business_rules.md",
                       "code_map_all.md", "error_code_map_tci_strategy.md",
                       "修订记录.md", "外部接口清单.md", "用例参数_VDI教师机镜像变更策略.md"))

def get_fm_end(lines):
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return i
    return None

def table_rows(text, sec_title):
    m = re.search(r'##\s*' + re.escape(sec_title) + r'\s*\n(.*?)(?=\n##\s|\Z)', text, re.S)
    if not m:
        return []
    sect = m.group(1)
    rows = []
    for row in re.finditer(r'^\|\s*([^|\n]+?)\s*\|\s*([^|\n]+?)\s*\|(.*)$', sect, re.M):
        name = row.group(1).strip()
        typ = row.group(2).strip()
        desc = row.group(3).strip().strip("|").strip()
        if name in ("字段", "参数名", "返回类型", "项目") or name.startswith("---"):
            continue
        if "." in name or "[" in name or "/" in name:
            continue
        # skip wrapper fields (defined in response.wrapper) and descriptive rows
        if name in ("status", "message", "msgKey", "msgArgArr", "content", "itemArr", "total"):
            continue
        if "说明" in name:
            continue
        rows.append((name, typ, desc))
    return rows

fixed = []
for f in DOC_FILES:
    name = os.path.basename(f)
    text = open(f, encoding="utf-8").read()
    lines = text.split("\n")
    end = get_fm_end(lines)
    if end is None:
        continue
    block = "\n".join(lines[1:end])
    data = yaml.safe_load(block)
    resp = data.get("response") or {}
    body = resp.get("body") if isinstance(resp, dict) else None
    if not isinstance(body, dict):
        continue
    fm_fields = set(body.keys())
    body_text = "\n".join(lines[end+1:])
    rows = table_rows(body_text, "出参详情")
    missing = [(n, t, d) for (n, t, d) in rows if n not in fm_fields]
    if not missing:
        continue
    # build YAML snippet for missing flat fields (indent 4)
    snippet = ""
    for n, t, d in missing:
        snippet += f"    {n}:\n      type: {t}\n      description: {d}\n"
    # find response.body block end (last line before a top-level key at indent 0 within response)
    # simplest: find 'body:' line and the last nested field line before a dedent to 'response' siblings
    # We append right after the last field of body (before the next top-level key like polling:/upstream:)
    # locate 'body:' line index within front-matter (1-based absolute)
    body_line_abs = None
    for i in range(1, end):
        if lines[i].strip().startswith("body:"):
            body_line_abs = i
            break
    if body_line_abs is None:
        continue
    # find last line of body block: next line with indent 0 (top-level key) after body_line_abs
    last = body_line_abs
    for i in range(body_line_abs + 1, end):
        ln = lines[i]
        if re.match(r'^\S', ln):  # top-level key
            break
        last = i
    # insert snippet after 'last'
    new_lines = lines[:last+1] + [snippet.rstrip("\n")] + lines[last+1:]
    open(f, "w", encoding="utf-8").write("\n".join(new_lines))
    fixed.append((name, [n for n, t, d in missing]))

print("补全出参字段的文件数:", len(fixed))
for name, miss in fixed:
    print(f"  {name}: 补 {len(miss)} 字段 {miss[:20]}")
