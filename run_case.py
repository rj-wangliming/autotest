#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""autotest - CI/CD 一条龙 CLI

用法:
  python3 run_case.py <用例文件> [--params 全局参数.yaml] [--base-url URL]
      [--llm-config model_config.json] [--plan-cache .cache/plans]
      [--junit report.xml] [--no-cache] [--timeout 120]

流程: 读用例 → build_plan_ai(命中缓存则0 LLM) → run_plan 执行 → JUnit → exit 0/1
plan 缓存按用例文本 hash: 首次本地调 LLM 生成并缓存; CI 命中缓存直接执行(0 LLM, 确定性)
"""
import argparse
import hashlib
import json
import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from app.core import get_index, Orchestrator


def load_yaml_or_json(path):
    """读 yaml/json 文件为 dict"""
    if not path or not os.path.exists(path):
        return {}
    import yaml
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_llm_config(path):
    """读 LLM 配置; CI 凭据注入: 环境变量 LLM_API_KEY/LLM_BASE_URL/LLM_MODEL 覆盖文件值"""
    cfg = load_yaml_or_json(path)
    if not cfg:
        default = os.path.join(PROJECT_ROOT, "app", "data", "model_config.json")
        if os.path.exists(default):
            cfg = load_yaml_or_json(default)
    if not cfg:
        return None
    if os.environ.get("LLM_API_KEY"):
        cfg["api_key"] = os.environ["LLM_API_KEY"]
    if os.environ.get("LLM_BASE_URL"):
        cfg["base_url"] = os.environ["LLM_BASE_URL"]
    if os.environ.get("LLM_MODEL"):
        cfg["model"] = os.environ["LLM_MODEL"]
    if cfg.get("base_url") and cfg.get("api_key") and cfg.get("model"):
        return cfg
    return None


def load_use_case(path):
    """读用例文件 → {name, use_case, params}
    YAML: {name, use_case, params}; 纯文本: 整文件为用例文本"""
    text = open(path, encoding="utf-8").read()
    if path.endswith((".yaml", ".yml")):
        import yaml
        d = yaml.safe_load(text) or {}
        return {"name": d.get("name") or os.path.splitext(os.path.basename(path))[0],
                "use_case": (d.get("use_case") or "").strip(),
                "params": d.get("params") or {}}
    return {"name": os.path.splitext(os.path.basename(path))[0],
            "use_case": text.strip(), "params": {}}


def plan_cache_key(use_case_text):
    return hashlib.sha1(use_case_text.encode("utf-8")).hexdigest()[:16]


def build_or_load_plan(use_case_text, params, llm_config, cache_dir):
    """plan 缓存: 命中则 0 LLM; 未命中则 build_plan_ai 生成并缓存"""
    idx = get_index(); idx.load()
    orch = Orchestrator(idx)
    key = plan_cache_key(use_case_text)
    cache_path = os.path.join(cache_dir, key + ".json") if cache_dir else None
    if cache_path and os.path.exists(cache_path):
        print("[ci] plan 命中缓存 %s（0 LLM 调用）" % key)
        return json.load(open(cache_path, encoding="utf-8")), "cache"
    if llm_config:
        try:
            plan = orch.build_plan_ai(use_case_text, params, llm_config)
            plan["_channel"] = "B"
        except Exception as e:
            print("[ci] AI 编排失败，降级规则: %s" % e)
            plan = orch.build_plan(use_case_text, params)
            plan["_channel"] = "A(降级)"
    else:
        plan = orch.build_plan(use_case_text, params)
        plan["_channel"] = "A(无LLM)"
    if cache_path:
        os.makedirs(cache_dir, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=1)
        print("[ci] plan 已缓存 %s（channel=%s, %d 步）" % (key, plan["_channel"], len(plan.get("steps", []))))
    return plan, plan.get("_channel")


def _xml_escape(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def to_junit_xml(results):
    """results: [{name, status, duration_ms, error, channel}] → JUnit XML"""
    total = len(results)
    failures = sum(1 for r in results if r["status"] != "PASS")
    total_time = sum(r.get("duration_ms", 0) for r in results) / 1000.0
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<testsuites>',
             '<testsuite name="RCC-AutoTest" tests="%d" failures="%d" errors="0" time="%.3f">' % (
                 total, failures, total_time)]
    for r in results:
        t = r.get("duration_ms", 0) / 1000.0
        lines.append('<testcase name="%s" classname="%s" time="%.3f">' % (
            _xml_escape(r["name"]), _xml_escape(r.get("channel", "")), t))
        if r["status"] != "PASS":
            lines.append('<failure message="%s"><![CDATA[%s]]></failure>' % (
                _xml_escape(r["status"]), r.get("error", "")[:500]))
        lines.append('</testcase>')
    lines.append('</testsuite></testsuites>')
    return "\n".join(lines)


def run_one(case_path, args):
    """跑单个用例 → result dict（name/status/duration_ms/error/channel）"""
    from app.core.logger import setup_app_logging, new_case_log, CaseFileLogger
    setup_app_logging()  # 项目运行日志（CI 也落盘）
    uc = load_use_case(case_path)
    params = dict(args.params) if isinstance(args.params, dict) else {}
    params.update(uc["params"])
    base_url = (args.base_url or os.environ.get("BASE_URL")
                or params.get("base_url") or "http://127.0.0.1:8080")
    plan, channel = build_or_load_plan(uc["use_case"], params, args.llm_config, args.plan_cache)
    from app.core.executor import run_plan
    log_path = new_case_log("ci_" + uc["name"])

    def log(level, msg):
        print("[%s] %s" % (level, msg))
        flog.write(level, msg)

    flog = CaseFileLogger(log_path)
    start = time.time()
    try:
        result = run_plan(plan, params, base_url, log_cb=log)
        status = result.get("status", "FAIL")
        error = result.get("error", "") or ""
    except Exception as e:
        status = "ERROR"
        error = str(e)
        log("error", "执行异常: %s" % e)
    finally:
        flog.close()
    dur = int((time.time() - start) * 1000)
    print("[ci] %s → %s (%.2fs, %s) 日志→%s" % (uc["name"], status, dur / 1000.0, channel, log_path))
    return {"name": uc["name"], "status": status, "duration_ms": dur,
            "error": error, "channel": channel}


def main():
    ap = argparse.ArgumentParser(description="autotest CI 一条龙")
    ap.add_argument("case", help="用例文件 (.yaml/.yml/.txt/.md)")
    ap.add_argument("--params", default="app/data/global_params.yaml", help="全局参数文件")
    ap.add_argument("--base-url", default=None, help="目标环境（优先级：--base-url > BASE_URL 环境变量 > yaml base_url > 默认）")
    ap.add_argument("--llm-config", default="app/data/model_config.json", help="LLM 配置文件")
    ap.add_argument("--plan-cache", default=".cache/plans", help="plan 缓存目录")
    ap.add_argument("--junit", help="JUnit XML 输出路径")
    ap.add_argument("--no-cache", action="store_true", help="禁用 plan 缓存（每次调 LLM）")
    args = ap.parse_args()
    args.params = load_yaml_or_json(args.params)
    args.llm_config = load_llm_config(args.llm_config)
    args.plan_cache = None if args.no_cache else args.plan_cache
    r = run_one(args.case, args)
    if args.junit:
        d = os.path.dirname(args.junit)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(args.junit, "w", encoding="utf-8") as f:
            f.write(to_junit_xml([r]))
        print("[ci] JUnit 报告: %s" % args.junit)
    sys.exit(0 if r["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
