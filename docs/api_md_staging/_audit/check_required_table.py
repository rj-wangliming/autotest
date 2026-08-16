#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skill #7: cross-check body 入参详情 table '必填' column vs front-matter required."""
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

def table_required(text):
    """Extract {field: required_bool} from 入参详情 table."""
    m = re.search(r'##\s*入参详情\s*\n(.*?)(?=\n##\s|\Z)', text, re.S)
    if not m:
        return {}
    sect = m.group(1)
    out = {}
    for row in re.finditer(r'^\|\s*([^|\n]+?)\s*\|\s*([^|\n]+?)\s*\|\s*([^|\n]+?)\s*\|', sect, re.M):
        name = row.group(1).strip()
        req = row.group(3).strip()
        if name in ("参数名", "参数", "字段") or name.startswith("---"):
            continue
        if "." in name or "[" in name or "/" in name:
            continue
        out[name] = (req == "是")
    return out

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
    fm_end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm_end = i
            break
    body_text = "\n".join(lines[fm_end+1:])
    tb_req = table_required(body_text)
    for fld, spec in body.items():
        if not isinstance(spec, dict):
            continue
        fm_req = bool(spec.get("required"))
        if fld not in tb_req:
            continue
        tb_r = tb_req[fld]
        checked += 1
        if fm_req != tb_r:
            problems.setdefault(name, []).append(
                f"{fld}: front-matter required={fm_req} 但表格必填列={'是' if tb_r else '否'}")

print(f"对比字段数: {checked}")
print(f"必填不一致的文件: {len(problems)}")
for name, ps in sorted(problems.items()):
    print(f"\n{name}:")
    for p in ps:
        print(f"  - {p}")
if not problems:
    print("✅ 必填列全部一致")
