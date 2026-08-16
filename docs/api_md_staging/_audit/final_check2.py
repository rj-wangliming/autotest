#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final check #2: async->polling closure, required-field value source, upstream/downstream URL reality."""
import os, glob, re, json
import yaml

DOCS_DIR = "/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging"
JAVA_INDEX = json.load(open("/Users/swlim/Desktop/ruijie/autotest/_audit_tmp/java_index.json", encoding="utf-8")) if os.path.exists("/Users/swlim/Desktop/ruijie/autotest/_audit_tmp/java_index.json") else None
SWAGGER = None
for p in ("/Users/swlim/Desktop/ruijie/autotest/_audit_tmp/swagger_paths.json",):
    if os.path.exists(p):
        SWAGGER = json.load(open(p, encoding="utf-8"))
        break

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
            return lines[1:i]
    return None

# collect known endpoint URLs from source (fallback: re-extract quickly)
java_urls = set()
if JAVA_INDEX:
    for rel, info in JAVA_INDEX.items():
        for e in info["entries"]:
            java_urls.add(e["url"])
swagger_urls = set(SWAGGER.keys()) if SWAGGER else set()

# if java_index.json missing, extract on the fly
if not java_urls:
    ROOT = "/Users/swlim/Desktop/ruijie/SpaceRCDC/rcdc-rcc-module-development-RCC-Space_V1.1_R1"
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
            for m in re.finditer(r'@(?:RequestMapping|PostMapping|GetMapping)\(\s*([^)]*)\)', body):
                attr = m.group(1)
                segs = re.findall(r'["\']([^"\']*)["\']', attr)
                for seg in segs:
                    url = (base.rstrip("/") + "/" + seg.lstrip("/")) if seg else base
                    if not url.startswith("/"):
                        url = "/" + url
                    java_urls.add(url)

problems = {}
for f in DOC_FILES:
    name = os.path.basename(f)
    lines = open(f, encoding="utf-8").read().split("\n")
    fm = get_fm(lines)
    if fm is None:
        continue
    data = yaml.safe_load("\n".join(fm))
    api = data.get("api") or {}
    async_flag = api.get("async")
    # 1. async -> polling
    if async_flag and not data.get("polling"):
        problems.setdefault(name, []).append(f"async=true 但无 polling 配置")
    # 2. required field value source
    req = data.get("request") or {}
    body = req.get("body") if isinstance(req, dict) else None
    if isinstance(body, dict):
        for fname, spec in body.items():
            if not isinstance(spec, dict):
                continue
            if spec.get("required") is True:
                has_src = any(k in spec for k in ("value", "generated_by", "example")) or \
                          "${" in json.dumps(spec, ensure_ascii=False)
                # framework fields allowed without value
                if fname in ("page", "limit", "matchArr", "sortArr", "exactMatchArr", "searchKeyword"):
                    continue
                if not has_src:
                    problems.setdefault(name, []).append(f"required 字段 {fname} 无 value/generated_by 来源")
    # 3. upstream/downstream URL reality
    for key in ("upstream", "downstream", "cleanup"):
        items = data.get(key)
        if not isinstance(items, list):
            continue
        for it in items:
            if not isinstance(it, dict):
                continue
            u = it.get("api") or ""
            if not isinstance(u, str) or not u:
                continue
            m = re.match(r'(?:POST|GET)\s+(/[a-zA-Z0-9/_{}\.\-]+)', u)
            if not m:
                continue
            # skip wildcard/descriptive references (含中文说明 or */|/{)
            if re.search(r'[\u4e00-\u9fff]', u) or "*" in u or "|" in u or "{" in u:
                continue
            url = m.group(1)
            if url.startswith("/rco/admin/"):
                continue
            if url in java_urls or url in swagger_urls:
                continue
            problems.setdefault(name, []).append(f"{key} 引用不存在的端点: {u}")

print(f"接口文档数: {len(DOC_FILES)}")
print(f"已知 java 端点: {len(java_urls)}, swagger 端点: {len(swagger_urls)}")
print(f"有问题的文件: {len(problems)}")
for name, ps in sorted(problems.items()):
    print(f"\n{name}:")
    for p in ps:
        print(f"  - {p}")
if not problems:
    print("✅ 全部通过")
