#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate field_map (upstream) from the three-piece chain:
upstream.produces -> setup.extract (jsonpath->var) -> request.body ${prev.var}->field.
Output standalone field_map.json as machine-readable cross-interface contract."""
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

def jsonpath_field(jp):
    """Extract the terminal field name from a jsonpath like $.content.itemArr[0].classroomStrategyId."""
    if not jp or not isinstance(jp, str):
        return None
    m = re.search(r'(?:\.|\[0\]\.)([A-Za-z0-9_]+)$', jp)
    if m:
        return m.group(1)
    m = re.search(r'([A-Za-z0-9_]+)$', jp)
    return m.group(1) if m else None

field_map = {}  # doc -> list of upstream field_map entries

for f in DOC_FILES:
    name = os.path.basename(f).replace(".md", "")
    block = get_fm(open(f, encoding="utf-8").read().split("\n"))
    if block is None:
        continue
    data = yaml.safe_load(block)
    # build extract var -> (step, jsonpath) and jsonpath -> var
    var_to_jp = {}   # var -> jsonpath
    jp_to_var = {}   # terminal field of jsonpath -> var (first match)
    setup = data.get("setup")
    if isinstance(setup, list):
        for s in setup:
            if not isinstance(s, dict):
                continue
            ext = s.get("extract")
            if isinstance(ext, dict):
                for var, jp in ext.items():
                    var_to_jp[var] = jp
                    tf = jsonpath_field(jp)
                    if tf and tf not in jp_to_var:
                        jp_to_var[tf] = var
            elif isinstance(ext, list):
                for e in ext:
                    if isinstance(e, dict) and e.get("var"):
                        var_to_jp[e["var"]] = e.get("jsonpath", "")
                        tf = jsonpath_field(e.get("jsonpath", ""))
                        if tf and tf not in jp_to_var:
                            jp_to_var[tf] = e["var"]
    # request.body prev refs: ${prev.step.output.var} / ${prev.var} -> field
    req = data.get("request") or {}
    body = req.get("body") if isinstance(req, dict) else None
    body_str = json.dumps(body, ensure_ascii=False) if isinstance(body, dict) else ""
    # map var -> field (where ${prev.<var>} appears as value of field)
    var_to_field = {}
    if isinstance(body, dict):
        for fld, spec in body.items():
            if isinstance(spec, dict):
                val = spec.get("value")
                if isinstance(val, str):
                    m = re.search(r'\$\{prev\.(?:[A-Za-z0-9_]+\.)?(?:output\.)?([A-Za-z0-9_]+)\}', val)
                    if m:
                        var_to_field[m.group(1)] = fld
    # upstream field_map
    entries = []
    for it in (data.get("upstream") or []):
        if not isinstance(it, dict):
            continue
        api = it.get("api", "")
        produces = it.get("produces")
        if not produces:
            continue
        fm = {"api": api, "from_jsonpath": produces}
        tf = jsonpath_field(produces)
        # to field: via extract var -> request.body field
        if tf and tf in jp_to_var:
            var = jp_to_var[tf]
            if var in var_to_field:
                fm["to"] = var_to_field[var]
        entries.append(fm)
    if entries:
        field_map[name] = entries

out = os.path.join("/Users/swlim/Desktop/ruijie/autotest/docs/api_md_staging", "field_map.json")
json.dump(field_map, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

n_docs = len(field_map)
n_entries = sum(len(v) for v in field_map.values())
n_with_to = sum(1 for v in field_map.values() for e in v if e.get("to"))
print(f"生成 field_map 文档数: {n_docs}")
print(f"field_map 条目: {n_entries}, 其中含 to 映射: {n_with_to} ({100*n_with_to//max(n_entries,1)}%)")
print(f"输出: {out}")
