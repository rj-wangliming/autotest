#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final verification: front-matter validity, duplicate keys, merged fields
(in BOTH front-matter and body markdown tables), fabricated response fields."""
import os, glob, re
import yaml

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
DOC_FILES = sorted(f for f in glob.glob(os.path.join(DOCS_DIR, "*.md"))
                   if os.path.basename(f) not in (
                       "README.md", "SETUP_PARAM_SPEC.md", "business_rules.md",
                       "code_map_all.md", "error_code_map_tci_strategy.md",
                       "修订记录.md", "外部接口清单.md", "用例参数_VDI教师机镜像变更策略.md"))

class Rec:
    def __init__(self):
        self.dups = []

def make_constructor(rec):
    def construct_mapping(loader, node, deep=False):
        mapping = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError:
                key = str(key)
            if key in mapping:
                rec.dups.append((key_node.start_mark.line + 1, str(key)))
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping
    return construct_mapping

def get_fm_block(lines):
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i]
    return None

problems = {}
n_fm_ok = 0
for f in DOC_FILES:
    name = os.path.basename(f)
    text = open(f, encoding="utf-8").read()
    lines = text.split("\n")
    fm = get_fm_block(lines)
    if fm is None:
        problems.setdefault(name, []).append("front-matter 无 --- 分隔")
        continue
    block = "\n".join(fm)
    # 1. strict yaml
    try:
        data = yaml.safe_load(block)
    except Exception as e:
        problems.setdefault(name, []).append(f"front-matter YAML 错误: {e}")
        continue
    n_fm_ok += 1
    # 2. duplicate keys
    rec = Rec()
    loader_cls = type("L", (yaml.SafeLoader,), {})
    loader_cls.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                              make_constructor(rec))
    try:
        yaml.load(block, Loader=loader_cls)
    except Exception:
        pass
    if rec.dups:
        problems.setdefault(name, []).append(f"重复key: {[(l,k) for l,k in rec.dups]}")
    # 3. front-matter response.body merged fields
    resp = (data or {}).get("response") or {}
    body = resp.get("body") if isinstance(resp, dict) else None
    if isinstance(body, dict):
        merged = [k for k in body if "/" in k]
        if merged:
            problems.setdefault(name, []).append(f"front-matter response.body 字段名含'/': {merged}")
        for k in body:
            if k in ("code", "retCode", "resultCode", "errno", "errorCode"):
                problems.setdefault(name, []).append(f"front-matter 伪造字段: {k}")
    # 4. body markdown table merged fields (出参详情 / 入参详情)
    # find tables in body (after front-matter)
    body_text = "\n".join(lines[len(fm)+2:])
    # locate section titles
    for sec in ("出参详情", "入参详情"):
        m = re.search(r'##\s*' + sec + r'\s*\n(.*?)(?=\n##\s|\Z)', body_text, re.S)
        if not m:
            continue
        sect = m.group(1)
        # table rows: | field | type | ... |
        for row in re.finditer(r'^\|\s*([^|\n]+?)\s*\|', sect, re.M):
            first_cell = row.group(1).strip()
            if "/" in first_cell and not first_cell.startswith("-"):
                # skip separator rows and header
                if first_cell in ("字段", "参数名", "参数", "字段名"):
                    continue
                problems.setdefault(name, []).append(f"body {sec} 表格字段名含'/': {first_cell[:60]}")

print(f"接口文档数: {len(DOC_FILES)}")
print(f"front-matter 严格解析通过: {n_fm_ok} / {len(DOC_FILES)}")
print(f"有问题的文件: {len(problems)}")
for name, ps in sorted(problems.items()):
    print(f"\n{name}:")
    for p in ps:
        print(f"  - {p}")
if not problems:
    print("✅ 全部通过")
