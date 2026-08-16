#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check msgKey values referenced in assertions exist in code_map_all.md."""
import os, glob, re

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
code_map = open(os.path.join(DOCS_DIR, "code_map_all.md"), encoding="utf-8").read()
known = set()
for row in re.finditer(r'^\|\s*([A-Za-z0-9_]+)\s*\|\s*([A-Za-z0-9_\.\-]+)\s*\|', code_map, re.M):
    known.add(row.group(1))
    known.add(row.group(2))
for row in re.finditer(r'^\|\s*(\d+)\s*\|\s*([A-Za-z0-9_]+)\s*\|', code_map, re.M):
    known.add(row.group(1))
    known.add(row.group(2))

DOC_FILES = sorted(f for f in glob.glob(os.path.join(DOCS_DIR, "*.md"))
                   if os.path.basename(f) not in (
                       "README.md", "SETUP_PARAM_SPEC.md", "business_rules.md",
                       "code_map_all.md", "error_code_map_tci_strategy.md",
                       "修订记录.md", "外部接口清单.md", "用例参数_VDI教师机镜像变更策略.md"))

TYPE_WORDS = {"String", "Object", "type", "i18n", "Integer", "Boolean", "Long"}

problems = {}
for f in DOC_FILES:
    name = os.path.basename(f)
    text = open(f, encoding="utf-8").read()
    refs = set()
    # msgKey==XXX  (assertion equality)
    refs |= set(re.findall(r'msgKey\s*==\s*([A-Za-z0-9_\.\-]+)', text))
    # msgKey 为 XXX / msgKey=XXX (body text, but not front-matter "msgKey: String")
    for m in re.finditer(r'msgKey\s*(?:为|是|：|=)\s*([A-Za-z0-9_\.\-]+)', text):
        v = m.group(1)
        if v not in TYPE_WORDS:
            refs.add(v)
    for r in sorted(refs):
        if r in known or r.isdigit():
            continue
        problems.setdefault(name, set()).add(r)

print(f"code_map 已知: {len(known)}")
print(f"文档断言引用但 code_map 无的 msgKey（文件数）: {len(problems)}")
for name, refs in sorted(problems.items()):
    print(f"\n{name}:")
    for r in sorted(refs):
        print(f"  - {r}")
if not problems:
    print("✅ 全部 msgKey 均可找到")
