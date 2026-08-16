#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check matchArr/exactMatchArr/sortArr element structure matches real samples
(matchArr: {type,fieldName,valueArr,matchRule}; exactMatchArr: {name,valueArr}; sortArr: {fieldName,direction})."""
import os, glob, re, json
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

# 期望的元素字段
EXPECT = {
    "matchArr": {"type", "fieldName", "fieldNameArr", "value", "valueArr", "matchRule"},
    "exactMatchArr": {"name", "valueArr"},
    "sortArr": {"fieldName", "direction", "sortField"},
}

problems = {}
checked = 0
for f in DOC_FILES:
    name = os.path.basename(f)
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    # 检查 request.body 和 setup 里的 matchArr/exactMatchArr/sortArr 元素
    def check_items(obj, ctx):
        global checked
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ("matchArr", "exactMatchArr", "sortArr") and isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            checked += 1
                            keys = set(item.keys())
                            exp = EXPECT[k]
                            # 允许字段缺失（部分场景），但字段名必须是期望集合里的
                            unknown = keys - exp
                            if unknown:
                                problems.setdefault(name, []).append(
                                    f"{ctx}.{k} 元素含非标准字段 {sorted(unknown)}（期望 {sorted(exp)}）")
                elif isinstance(v, (dict, list)):
                    check_items(v, f"{ctx}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_items(item, f"{ctx}[{i}]")
    req = data.get("request") or {}
    check_items(req, "request")
    setup = data.get("setup")
    check_items(setup, "setup")

print(f"matchArr/exactMatchArr/sortArr 元素检查数: {checked}")
print(f"元素字段非标准的文件: {len(problems)}")
for name, ps in sorted(problems.items()):
    for p in ps[:10]:
        print(f"  {name}: {p}")
