#!/usr/bin/env python3
"""Check required-flag consistency between front-matter and body input table."""
import sys, re, yaml

for path in sys.argv[1:]:
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        continue
    try:
        fm = yaml.safe_load(m.group(1))
    except Exception as e:
        print(f"{path}: YAML ERROR {e}")
        continue
    body = text[m.end():]
    # front-matter request fields
    fm_req = {}
    req = (fm.get("request") or {})
    for fname, spec in (req.get("body") or {}).items():
        if isinstance(spec, dict):
            fm_req[fname] = spec.get("required")
    # body input table: | 参数名 | 类型 | 必填 | ...
    body_req = {}
    in_input = False
    for line in body.splitlines():
        if line.startswith("## 入参详情"):
            in_input = True
            continue
        if in_input and line.startswith("## ") and "入参" not in line:
            in_input = False
        if in_input and line.startswith("|") and "参数名" not in line and "---" not in line:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 3:
                # field name may be compound a/b/c
                for fn in cells[0].split("/"):
                    fn = fn.strip()
                    if fn:
                        body_req[fn] = cells[2]
    issues = []
    for fname, req_flag in fm_req.items():
        for bname, bval in body_req.items():
            if bname == fname or fname.startswith(bname + "/") or bname in fname.split("/"):
                pass
        # simple exact match only
        if fname in body_req:
            bv = body_req[fname]
            expect = "是" if req_flag else "否"
            if bv not in (expect, "条件"):
                issues.append(f"field '{fname}': front-matter required={req_flag} but body table says '{bv}'")
    if issues:
        print(f"{path}:")
        for i in issues:
            print(f"  ⚠️ {i}")
    else:
        # also report fields where front-matter has no required but body says 是
        extra = [f"{k}={v}" for k, v in body_req.items() if v == "是" and k not in fm_req and fm_req]
        print(f"{path}: OK" + (f"  (body-only required fields not in front-matter: {', '.join(extra)})" if extra else ""))
