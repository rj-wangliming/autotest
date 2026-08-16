#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix 出参 front-matter completeness: append fields present in 出参详情 table
but missing from response.body. itemArr element fields get 'itemArr[]_' prefix."""
import os, glob, re
import yaml

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
DOC_FILES = sorted(f for f in glob.glob(os.path.join(DOCS_DIR, "*.md"))
                   if os.path.basename(f) not in (
                       "README.md", "SETUP_PARAM_SPEC.md", "business_rules.md",
                       "code_map_all.md", "error_code_map_tci_strategy.md",
                       "修订记录.md", "外部接口清单.md", "用例参数_VDI教师机镜像变更策略.md"))

SKIP_FIELDS = {"字段", "参数名", "返回类型", "项目", "status", "message", "msgKey",
               "msgArgArr", "content", "itemArr", "total"}

def parse_table(text, sec_title):
    m = re.search(r'##\s*' + re.escape(sec_title) + r'\s*\n(.*?)(?=\n##\s|\Z)', text, re.S)
    if not m:
        return []
    sect = m.group(1)
    rows = []       # (name, type, desc)
    elem_mode = False
    for row in re.finditer(r'^\|\s*([^|\n]+?)\s*\|\s*([^|\n]+?)\s*\|(.*)$', sect, re.M):
        name = row.group(1).strip()
        typ = row.group(2).strip()
        desc = row.group(3).strip().strip("|").strip()
        if name.startswith("---"):
            continue
        if name in SKIP_FIELDS:
            if name == "itemArr" and ("元素" in desc or "见下" in desc):
                elem_mode = True
            continue
        if "." in name or "[" in name or "/" in name or "说明" in name:
            continue
        rows.append((name, typ, desc, elem_mode))
    return rows

def get_fm_end(lines):
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return i
    return None

def fm_field_names(body):
    names = set(body.keys())
    c = body.get("content")
    if isinstance(c, dict):
        f = c.get("fields")
        if isinstance(f, dict):
            names |= set(f.keys())
        elif isinstance(f, list):
            names |= {x for x in f if isinstance(x, str)}
    return names

report = []
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
    fm = fm_field_names(body)
    body_text = "\n".join(lines[end+1:])
    rows = parse_table(body_text, "出参详情")
    missing = [(n, t, d, e) for (n, t, d, e) in rows
               if (("itemArr[]_" + n) if e else n) not in fm]
    if not missing:
        continue
    # build YAML snippet (indent 4)
    snippet = ""
    for n, t, d, e in missing:
        fname = ("itemArr[]_" + n) if e else n
        # quote names containing [] to avoid YAML flow-sequence ambiguity
        key = f'"{fname}"' if "[]" in fname else fname
        snippet += f"    {key}:\n      type: {t}\n      description: {d}\n"
    # locate response.body block (indent-2 'body:' under response:, NOT setup's request.body)
    body_line_abs = None
    resp_line = None
    for i in range(1, end):
        if lines[i].strip() == "response:" and not lines[i].startswith(" "):
            resp_line = i
            break
    if resp_line is not None:
        for i in range(resp_line + 1, end):
            if re.match(r'^\S', lines[i]):  # next top-level key ends response section
                break
            if re.match(r'^  body:', lines[i]):
                body_line_abs = i
                break
    if body_line_abs is None:
        # fallback: any indent-2 body under a top-level response
        for i in range(1, end):
            if re.match(r'^  body:', lines[i]):
                body_line_abs = i
                break
    if body_line_abs is None:
        continue
    last = body_line_abs
    for i in range(body_line_abs + 1, end):
        if re.match(r'^\S', lines[i]):
            break
        last = i
    new_lines = lines[:last+1] + [snippet.rstrip("\n")] + lines[last+1:]
    if os.environ.get("DRY_RUN"):
        report.append((name, len(missing), "DRY"))
        continue
    open(f, "w", encoding="utf-8").write("\n".join(new_lines))
    report.append((name, len(missing)))

print("补全文件数:", len(report))
for item in report:
    print(f"  {item}")
