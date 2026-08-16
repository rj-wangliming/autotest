#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check enum values in front-matter request.body description vs body 入参详情 table
description consistency (e.g. teacherMode PC missing in table)."""
import os, glob, re
import yaml

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
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

def enum_from(s):
    """Extract enum list from （A/B/C） or (A/B/C) pattern."""
    if not s:
        return None
    m = re.findall(r'[（(]([A-Za-z0-9_/，,、]+)[）)]', s)
    if not m:
        return None
    # 取最长的一组（最可能是枚举）
    longest = max(m, key=len)
    parts = re.split(r'[/，,、]', longest)
    parts = [p.strip() for p in parts if p.strip() and not p.startswith(('默认', '如', '含', '继承'))]
    return set(parts) if len(parts) > 1 else None

def table_desc(text, field):
    """Extract description from 入参详情 table for a given field."""
    m = re.search(r'##\s*入参详情\s*\n(.*?)(?=\n##\s|\Z)', text, re.S)
    if not m:
        return None
    sect = m.group(1)
    for row in re.finditer(r'^\|\s*([^|\n]+?)\s*\|\s*[^|\n]*\s*\|\s*[^|\n]*\s*\|\s*[^|\n]*\s*\|\s*(.*?)\s*\|', sect, re.M):
        if row.group(1).strip() == field:
            return row.group(2).strip()
    return None

problems = {}
checked = 0
for f in DOC_FILES:
    name = os.path.basename(f)
    lines = open(f, encoding="utf-8").read().split("\n")
    block = get_fm(lines)
    if block is None:
        continue
    data = yaml.safe_load(block)
    req = data.get("request") or {}
    body = req.get("body") if isinstance(req, dict) else None
    if not isinstance(body, dict):
        continue
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i; break
    body_text = "\n".join(lines[end+1:])
    for fld, spec in body.items():
        if not isinstance(spec, dict):
            continue
        fm_desc = spec.get("description", "")
        fm_enum = enum_from(fm_desc)
        if fm_enum is None:
            continue
        tb_desc = table_desc(body_text, fld)
        if tb_desc is None:
            continue
        tb_enum = enum_from(tb_desc)
        if tb_enum is None:
            continue
        checked += 1
        # 表格枚举应包含 front-matter 枚举（或反之），找不一致
        if fm_enum != tb_enum and not fm_enum.issubset(tb_enum) and not tb_enum.issubset(fm_enum):
            problems.setdefault(name, []).append(
                f"{fld}: front-matter={sorted(fm_enum)} vs 表格={sorted(tb_enum)}")

print(f"对比枚举字段数: {checked}")
print(f"枚举不一致的文件: {len(problems)}")
for name, ps in sorted(problems.items()):
    for p in ps:
        print(f"  {name}: {p}")
