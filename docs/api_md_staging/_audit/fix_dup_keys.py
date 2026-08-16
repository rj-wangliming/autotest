#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Delete duplicate mapping key lines in front-matter (keep first occurrence)."""
import os, glob
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
                rec.dups.append(key_node.start_mark.line + 1)
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping
    return construct_mapping

def get_fm_end(lines):
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return i
    return None

fixed = []
for f in DOC_FILES:
    name = os.path.basename(f)
    lines = open(f, encoding="utf-8").read().split("\n")
    end = get_fm_end(lines)
    if end is None:
        continue
    block = "\n".join(lines[1:end])
    rec = Rec()
    loader_cls = type("L", (yaml.SafeLoader,), {})
    loader_cls.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                              make_constructor(rec))
    try:
        yaml.load(block, Loader=loader_cls)
    except Exception as e:
        print(f"  [skip] {name}: {e}")
        continue
    if not rec.dups:
        continue
    del_indices = sorted({1 + (ln - 1) for ln in rec.dups})  # block line -> absolute index
    new_lines = [l for i, l in enumerate(lines) if i not in del_indices]
    open(f, "w", encoding="utf-8").write("\n".join(new_lines))
    fixed.append((name, len(rec.dups)))

print("删除重复 key 的文件数:", len(fixed))
for name, n in fixed:
    print(f"  {name}: 删 {n} 行")
