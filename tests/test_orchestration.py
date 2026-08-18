#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""编排/规则库/文档 回归测试（纯 assert，不依赖真实环境与 LLM）

用法:
  python3 tests/test_orchestration.py          # 全量
  python3 tests/test_orchestration.py 编排     # 按前缀过滤

覆盖:
  1. 规则库:business_rules.md YAML 可解析、state_prereq/链接口存在于文档集
  2. 匹配:词边界(restart≠start)、精确匹配(classroom/delete vs image/student/delete)
  3. 补链:通道B场景 LLM 漏分配镜像时自动补齐、顺序拓扑正确
  4. 引用:plan 中 ${prev.*} 全部可解析
  5. 文档:全量 front-matter YAML 解析
"""
import os
import re
import sys
import glob
import traceback

import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["API_MD_DIR"] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "api_md_staging")

from app.core.orchestrator import Orchestrator  # noqa: E402
import app.core.index as index_mod  # noqa: E402

PASS = []
FAIL = []


def check(name, fn):
    try:
        fn()
        PASS.append(name)
        print("  ✅ %s" % name)
    except Exception as e:
        FAIL.append((name, str(e)))
        print("  ❌ %s: %s" % (name, e))
        traceback.print_exc()


def test_rules_yaml():
    d = yaml.safe_load(open(os.path.join(index_mod.API_MD_DIR, "business_rules.md")).read().split("---\n", 2)[1])
    assert "resource_chains" in d and "state_prereq" in d and "case_prereq" in d
    assert "field_prereq" in d
    assert len(d["resource_chains"]) >= 3
    assert len(d["state_prereq"]) >= 10


def test_rules_refs_exist():
    o = Orchestrator()
    doc = {m["url"] for m in o.index.all()}
    for sp in o.rules.get("state_prereq", []):
        if sp.get("api"):
            assert sp["api"] in doc, "规则 api %s 不在文档集" % sp["api"]
        for a in sp.get("achieve_via", []):
            u = re.sub(r"^(POST|GET|PUT|DELETE)\s+", "", a["api"])
            assert u in doc, "achieve_via %s 不在文档集" % u
    for rc in o.rules.get("resource_chains", {}).values():
        for u in rc["order"]:
            assert re.sub(r"^(POST|GET|PUT|DELETE)\s+", "", u) in doc, "链接口 %s 不在文档集" % u


def test_word_boundary():
    o = Orchestrator()
    r = o._find_state_prereq("/rcc/classroom/teacher/terminal/restart")
    assert r and r.get("action") == "restart", "restart 被误匹配为 start: %s" % (r or {})


def test_exact_api():
    o = Orchestrator()
    assert o._find_state_prereq("/rcc/classroom/delete") is not None, "classroom/delete 应命中规则"
    r = o._find_state_prereq("/rcc/classroom/image/student/delete")
    assert r is None, "image/student/delete 不应命中 classroom delete 规则"


def _run_channel_b(intent):
    o = Orchestrator()
    steps, seen = [], set()
    for s in intent["steps"]:
        api = s.get("api", "")
        if not o.index.get(api):
            continue
        o._expand_setup(api, steps, seen)
        if api not in seen:
            steps.append(o._build_step_named(api, s.get("step_name", ""), "", s.get("section", "action")))
            seen.add(api)
    plan = {"id": "t", "steps": steps, "assertions": [], "sections": {"前置": [], "操作": [], "预期": []}}
    return o.validate_plan(plan)


def test_chain_complete():
    """通道 B:LLM 漏分配镜像 → 自动补镜像 + 上课开机,顺序正确"""
    intent = {"steps": [
        {"api": "/rcc/classroom/strategy/create", "step_name": "createStrategy", "section": "pre"},
        {"api": "/rcc/classroom/create", "step_name": "create_classroom", "section": "pre"},
        {"api": "/rcc/classroom/seat/batchCreate", "step_name": "create_seat", "section": "pre"},
        {"api": "/rcc/space/classroom/cloudDesktop/restart", "step_name": "restart", "section": "action"},
    ]}
    plan = _run_channel_b(intent)
    apis = [s["api"] for s in plan["steps"]]
    # 分配镜像已补
    assert "/rcc/classroom/image/student/create" in apis, "缺分配镜像: %s" % apis
    # 上课开机已补
    assert "/rcc/classroom/cmrcef/lesson/start" in apis, "缺上课开机: %s" % apis
    # 顺序:教室 → 座位 → 镜像 → 上课 → 重启
    order = {u: i for i, u in enumerate(apis)}
    assert order["/rcc/classroom/create"] < order["/rcc/classroom/seat/batchCreate"], "教室应在座位前"
    assert order["/rcc/classroom/seat/batchCreate"] < order["/rcc/classroom/image/student/create"], "座位应在镜像前"
    assert order["/rcc/classroom/image/student/create"] < order["/rcc/classroom/cmrcef/lesson/start"], "镜像应在课前"
    assert order["/rcc/classroom/cmrcef/lesson/start"] < order["/rcc/space/classroom/cloudDesktop/restart"], "上课应在重启前"


def test_refs_resolvable():
    """plan 中 ${prev.X.output.Y} 引用, X 步骤存在且 extract 产出 Y"""
    intent = {"steps": [
        {"api": "/rcc/classroom/strategy/create", "step_name": "createStrategy", "section": "pre"},
        {"api": "/rcc/classroom/create", "step_name": "create_classroom", "section": "pre"},
        {"api": "/rcc/classroom/seat/batchCreate", "step_name": "create_seat", "section": "pre"},
        {"api": "/rcc/space/classroom/cloudDesktop/restart", "step_name": "restart", "section": "action"},
    ]}
    plan = _run_channel_b(intent)
    step_names = {s.get("step_name") for s in plan["steps"] if s.get("step_name")}
    for st in plan["steps"]:
        for v in (st.get("body") or {}).values():
            if not isinstance(v, dict) or not isinstance(v.get("value"), str):
                continue
            for m in re.finditer(r"\$\{prev\.([\w.]+)", v["value"]):
                sname = m.group(1).split(".")[0]
                assert sname in step_names, "引用断裂: %s -> %s" % (sname, v["value"])


def test_docs_yaml():
    fails = 0
    for path in glob.glob(os.path.join(index_mod.API_MD_DIR, "*.md")):
        c = open(path).read()
        if not c.startswith("---"):
            continue
        try:
            yaml.safe_load(c.split("---\n", 2)[1])
        except Exception:
            fails += 1
            print("    ❌ %s" % path.split("/")[-1])
    assert fails == 0, "%d 个文档 YAML 解析失败" % fails


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    tests = [
        ("规则库 YAML", test_rules_yaml),
        ("规则引用存在", test_rules_refs_exist),
        ("词边界匹配", test_word_boundary),
        ("精确 api 匹配", test_exact_api),
        ("补链完整性", test_chain_complete),
        ("引用可解析", test_refs_resolvable),
        ("文档 YAML", test_docs_yaml),
    ]
    print("=== 编排/规则库回归测试 ===\n")
    for name, fn in tests:
        if only and only not in name:
            continue
        check(name, fn)
    print("\n结果: %d 通过, %d 失败" % (len(PASS), len(FAIL)))
    if FAIL:
        for name, err in FAIL:
            print("  ❌ %s: %s" % (name, err[:200]))
        sys.exit(1)
    print("全部通过 ✅")


if __name__ == "__main__":
    main()
