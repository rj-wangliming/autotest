#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix: add missing ${param.xxx} declarations into the params.required list."""
import os, glob, re
import yaml

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
DOC_FILES = sorted(f for f in glob.glob(os.path.join(DOCS_DIR, "*.md"))
                   if os.path.basename(f) not in (
                       "README.md", "SETUP_PARAM_SPEC.md", "business_rules.md",
                       "code_map_all.md", "error_code_map_tci_strategy.md",
                       "修订记录.md", "外部接口清单.md", "用例参数_VDI教师机镜像变更策略.md"))

PAT = re.compile(r'\$\{param\.([A-Za-z0-9_]+)\}')

def fm_end(lines):
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return i
    return None

report = []
for f in DOC_FILES:
    name = os.path.basename(f)
    text = open(f, encoding="utf-8").read()
    lines = text.split("\n")
    end = fm_end(lines)
    if end is None:
        continue
    block = "\n".join(lines[1:end])
    refs = set(PAT.findall(block))
    data = yaml.safe_load(block)
    params = data.get("params") or {}
    declared = set()
    if isinstance(params, dict):
        for key in ("required", "optional"):
            items = params.get(key)
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict) and it.get("name"):
                        declared.add(it["name"])
                    elif isinstance(it, str):
                        declared.add(it)
    missing = sorted(refs - declared)
    if not missing:
        continue
    # insert entries at end of params.required: locate the params section and its last list item
    # find params: line (top-level, indent 0)
    pidx = None
    for j in range(1, end):
        if lines[j].startswith("params:"):
            pidx = j
            break
    if pidx is None:
        # no params section: add right before '---'
        block_new = "params:\n  required:\n" + "".join(f"  - name: {m}\n" for m in missing)
        lines = lines[:end] + [block_new.rstrip("\n")] + lines[end:]
        open(f, "w", encoding="utf-8").write("\n".join(lines))
        report.append((name, missing, "新增params节"))
        continue
    # find the last '  - name:' line within params section (indent exactly 2, before next top-level key or '---')
    last_name_line = None
    for j in range(pidx + 1, end):
        ln = lines[j]
        if re.match(r'^\S', ln):  # top-level key -> params section ends
            break
        if re.match(r'^  - name:', ln):
            last_name_line = j
    # ensure required: exists; if params section empty of 'required:', we still append '  - name:' lines
    # append after last_name_line (or after pidx if none)
    insert_after = last_name_line if last_name_line is not None else pidx
    new_entries = [f"  - name: {m}" for m in missing]
    lines = lines[:insert_after + 1] + new_entries + lines[insert_after + 1:]
    open(f, "w", encoding="utf-8").write("\n".join(lines))
    report.append((name, missing, "追加到params"))

print("修复文件数:", len(report))
for name, missing, mode in report:
    print(f"  {name} [{mode}] 补 {missing}")
