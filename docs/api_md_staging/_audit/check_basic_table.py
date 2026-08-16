#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check 接口基本信息 body table (URL/Controller/方法名/权限注解) vs front-matter api."""
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

def basic_table(text):
    """Extract {项目: 内容} from 接口基本信息 table."""
    m = re.search(r'##\s*接口基本信息\s*\n(.*?)(?=\n##\s|\Z)', text, re.S)
    if not m:
        return {}
    sect = m.group(1)
    out = {}
    for row in re.finditer(r'^\|\s*([^|\n]+?)\s*\|\s*([^|\n]*?)\s*\|', sect, re.M):
        k = row.group(1).strip()
        v = row.group(2).strip()
        out[k] = v
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
    api = data.get("api") or {}
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i; break
    body_text = "\n".join(lines[end+1:])
    tb = basic_table(body_text)
    if not tb:
        continue
    # URL
    if "URL" in tb:
        checked += 1
        tb_url = re.sub(r'[（(](GET|POST|PUT|DELETE)[）)]', '', tb["URL"]).strip().rstrip("/")
        fm_url = (api.get("url", "") or "").rstrip("/")
        if tb_url != fm_url:
            problems.setdefault(name, []).append(f"URL 表格={tb['URL']} vs front-matter={api.get('url')}")
    # Controller
    if "Controller" in tb and api.get("controller"):
        checked += 1
        tb_ctrl = tb["Controller"].strip().replace(".java", "")
        if tb_ctrl != api["controller"].replace(".java", ""):
            problems.setdefault(name, []).append(f"Controller 表格={tb['Controller']} vs front-matter={api.get('controller')}")
    # 方法名
    if "方法名" in tb and api.get("method_ref"):
        checked += 1
        if tb["方法名"].strip() != api["method_ref"]:
            problems.setdefault(name, []).append(f"方法名 表格={tb['方法名']} vs front-matter={api.get('method_ref')}")

print(f"对比项: {checked}")
print(f"不一致的文件: {len(problems)}")
for name, ps in sorted(problems.items()):
    for p in ps:
        print(f"  {name}: {p}")
if not problems:
    print("✅ 接口基本信息表格与 front-matter 一致")
