#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remaining checks: response.wrapper standard 5 fields, cleanup API reality,
assertions success+failure presence."""
import os, glob, re, json
import yaml

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
ROOT = "/Users/swlim/Desktop/ruijie/SpaceRCDC/rcdc-rcc-module-development-RCC-Space_V1.1_R1"

# java url set
java_urls = set()
for dp, _, fs in os.walk(ROOT):
    for fn in fs:
        if not fn.endswith("Controller.java"):
            continue
        src = open(os.path.join(dp, fn), encoding="utf-8", errors="ignore").read()
        cm = re.search(r'public\s+(?:abstract\s+)?class\s+\w+', src)
        base = ""
        if cm:
            m = re.search(r'@RequestMapping\(\s*(?:value\s*=\s*)?["\']([^"\']*)["\']', src[:cm.start()])
            if m:
                base = m.group(1).strip()
                if not base.startswith("/"):
                    base = "/" + base
        body = src[cm.start():] if cm else src
        for m in re.finditer(r'@(?:RequestMapping|PostMapping|GetMapping|PutMapping|DeleteMapping)\(\s*([^)]*)\)', body):
            attr = m.group(1)
            segs = re.findall(r'["\']([^"\']*)["\']', attr)
            for seg in segs:
                url = (base.rstrip("/") + "/" + seg.lstrip("/")) if seg else base
                if not url.startswith("/"):
                    url = "/" + url
                java_urls.add(url)

STANDARD_WRAPPER = {"status", "message", "msgKey", "msgArgArr", "content"}

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
    # 1. response.wrapper non-standard fields
    # (halo_getReport 返回 void + 直接写 ResponseResultDTO(result/desc)，非 SK 五字段包装，豁免)
    resp = data.get("response") or {}
    wrapper = resp.get("wrapper") if isinstance(resp, dict) else None
    if isinstance(wrapper, dict) and name != "rcc_halo_getReport.md":
        extra = set(wrapper.keys()) - STANDARD_WRAPPER
        if extra:
            problems.setdefault(name, []).append(f"response.wrapper 非标准字段: {sorted(extra)}")
        missing = STANDARD_WRAPPER - set(wrapper.keys())
        if missing:
            problems.setdefault(name, []).append(f"response.wrapper 缺标准字段: {sorted(missing)}")
    # 2. cleanup API reality
    cleanup = data.get("cleanup")
    if isinstance(cleanup, list):
        for c in cleanup:
            if isinstance(c, dict) and c.get("api"):
                u = c["api"]
                m = re.match(r'(?:POST|GET)\s+(/[a-zA-Z0-9/_{}\.\-]+)', str(u))
                if m:
                    url = m.group(1)
                    if "*" not in url and "{" not in url and url not in java_urls and not url.startswith("/rco/admin"):
                        problems.setdefault(name, []).append(f"cleanup 引用不存在的端点: {u}")
    # 3. assertions success+failure presence (operational interfaces)
    assertions = data.get("assertions")
    if isinstance(assertions, dict):
        succ = assertions.get("success")
        fail = assertions.get("failure")
        api = data.get("api") or {}
        url = api.get("url", "")
        if not succ and url not in ("/rcc/dashboard/statistics/classroomInfo",):
            problems.setdefault(name, []).append("断言缺 success 场景")
        if not fail:
            problems.setdefault(name, []).append("断言缺 failure 场景")

print(f"检查文件: {len(DOC_FILES)}")
print(f"有问题的文件: {len(problems)}")
for name, ps in sorted(problems.items()):
    print(f"\n{name}:")
    for p in ps:
        print(f"  - {p}")
if not problems:
    print("✅ 全部通过")
