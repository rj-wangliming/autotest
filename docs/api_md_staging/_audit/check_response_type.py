#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check response.body field types (enum/DTO class names) exist as real Java classes."""
import os, glob, re, json
import yaml

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
ROOT = "/Users/swlim/Desktop/ruijie/SpaceRCDC/rcdc-rcc-module-development-RCC-Space_V1.1_R1"

# java class/enum names
java_types = set()
for dp, _, fs in os.walk(ROOT):
    for fn in fs:
        if not fn.endswith(".java"):
            continue
        # class/enum/interface name = file name
        java_types.add(fn[:-5])
# swagger definitions
d = json.load(open("/Users/swlim/Desktop/ruijie/api_json/api.json", encoding="utf-8"))
swagger_types = set()
for name in d.get("definitions", {}):
    base = re.sub(r'«.*»', '', name)
    swagger_types.add(base)

# 基础类型
PRIMITIVES = {"String", "Integer", "Long", "Boolean", "Double", "Float", "Short", "Byte",
              "Object", "UUID", "Date", "list", "dict", "mixed", "enum", "long", "int",
              "Map", "List", "Set", "Object[]", "String[]", "Integer[]", "UUID[]",
              "File", "BigDecimal", "VgpuType", "VgpuExtraInfo", "String(JSON)", "null"}

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

problems = {}
for f in DOC_FILES:
    name = os.path.basename(f)
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    resp = data.get("response") or {}
    body = resp.get("body") if isinstance(resp, dict) else None
    if not isinstance(body, dict):
        continue
    for fld, spec in body.items():
        if not isinstance(spec, dict):
            continue
        t = spec.get("type", "")
        if not isinstance(t, str) or not t:
            continue
        # 去掉泛型/数组
        base = re.sub(r'[<\[\]].*$', '', t).strip()
        if base in PRIMITIVES or base in java_types or base in swagger_types:
            continue
        if base == "" or "/" in base:
            continue
        problems.setdefault(name, []).append(f"{fld}: type={t}（类 {base} 不在 Java/swagger）")

print(f"出参类型不在 Java/swagger 的文件: {len(problems)}")
for name, ps in sorted(problems.items()):
    for p in ps[:8]:
        print(f"  {name}: {p}")
