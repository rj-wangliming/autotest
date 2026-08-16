#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skill #28: front-matter data layer vs body markdown tables consistency.
入参详情表格字段 vs request.body 字段；出参详情表格字段 vs response.body 字段."""
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

def extract_section_table(text, sec_title):
    """Extract field names from a markdown table under a given ## section."""
    m = re.search(r'##\s*' + re.escape(sec_title) + r'\s*\n(.*?)(?=\n##\s|\Z)', text, re.S)
    if not m:
        return set()
    sect = m.group(1)
    fields = set()
    for row in re.finditer(r'^\|\s*([^|\n]+?)\s*\|', sect, re.M):
        cell = row.group(1).strip()
        if cell in ("字段", "参数名", "参数", "字段名", "返回类型", "项目",
                    "status", "message", "msgKey", "msgArgArr", "content",
                    "itemArr", "total") or cell.startswith("---"):
            continue
        if "说明" in cell or "." in cell or "[" in cell:
            continue
        fields.add(cell)
    return fields

problems = {}
for f in DOC_FILES:
    name = os.path.basename(f)
    text = open(f, encoding="utf-8").read()
    lines = text.split("\n")
    block = get_fm(lines)
    if block is None:
        continue
    data = yaml.safe_load(block)
    # body text (after front-matter)
    fm_end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm_end = i
            break
    body_text = "\n".join(lines[fm_end+1:])
    # 入参一致性
    req = data.get("request") or {}
    req_body = req.get("body") if isinstance(req, dict) else None
    if isinstance(req_body, dict):
        fm_fields = set(req_body.keys())
        tb_fields = extract_section_table(body_text, "入参详情")
        # body table may include nested/list refs (deskList[].xxx) - compare loosely
        fm_norm = {f for f in fm_fields}
        tb_norm = {t for t in tb_fields}
        only_fm = sorted(fm_norm - tb_norm)
        only_tb = sorted(tb_norm - fm_norm)
        # ignore table-only extra like wrapper rows
        if only_fm:
            problems.setdefault(name, []).append(f"入参: front-matter 有但表格无: {only_fm[:15]}")
        if only_tb and not any("[" in t for t in only_tb):
            problems.setdefault(name, []).append(f"入参: 表格有但 front-matter 无: {only_tb[:15]}")
    # 出参一致性
    resp = data.get("response") or {}
    resp_body = resp.get("body") if isinstance(resp, dict) else None
    if isinstance(resp_body, dict):
        fm_fields = set(resp_body.keys())
        tb_fields = extract_section_table(body_text, "出参详情")
        WRAPPER = {"status", "message", "msgKey", "msgArgArr", "content"}
        # normalize: front-matter 'itemArr[]_xxx' element fields correspond to table's flat 'xxx';
        # top-level 'itemArr'/'total' are table-flattened too
        fm_norm = {f for f in fm_fields
                   if f not in WRAPPER and f not in ("itemArr", "total", "itemArr[]")
                   and not f.startswith("itemArr[]_")}
        tb_norm = tb_fields
        only_fm = sorted(fm_norm - tb_norm)
        only_tb = sorted(tb_norm - fm_norm)
        if only_fm and "content" not in fm_fields:
            problems.setdefault(name, []).append(f"出参: front-matter 有但表格无: {only_fm[:15]}")
        if only_tb and not any("[" in t or "content" in t for t in only_tb):
            problems.setdefault(name, []).append(f"出参: 表格有但 front-matter 无: {only_tb[:15]}")

print(f"检查文件: {len(DOC_FILES)}")
print(f"两层不一致的文件: {len(problems)}")
for name, ps in sorted(problems.items()):
    print(f"\n{name}:")
    for p in ps:
        print(f"  - {p}")
if not problems:
    print("✅ front-matter 与 body 表格一致")
