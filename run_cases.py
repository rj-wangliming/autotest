#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量跑用例目录 → 汇总 JUnit 报告

用法:
  python3 run_cases.py <用例目录> [--params global_params.yaml] [--base-url URL]
      [--llm-config model_config.json] [--plan-cache .cache/plans]
      [--junit report.xml] [--no-cache]

遍历目录下 *.yaml/*.yml/*.txt/*.md, 每个用例一个 testcase, 汇总一个 JUnit XML。
exit 0 仅当全部 PASS。
"""
import argparse
import glob
import os
import sys

from run_case import run_one, to_junit_xml, load_yaml_or_json, load_llm_config


def main():
    ap = argparse.ArgumentParser(description="无封装测试平台 CI 批量")
    ap.add_argument("case_dir", help="用例目录")
    ap.add_argument("--params", default="app/data/global_params.yaml", help="全局参数文件")
    ap.add_argument("--base-url", default=os.environ.get("BASE_URL", "http://127.0.0.1:8080"))
    ap.add_argument("--llm-config", default="app/data/model_config.json", help="LLM 配置文件")
    ap.add_argument("--plan-cache", default=".cache/plans", help="plan 缓存目录")
    ap.add_argument("--junit", default="report.xml", help="JUnit XML 输出路径")
    ap.add_argument("--no-cache", action="store_true", help="禁用 plan 缓存")
    args = ap.parse_args()
    args.params = load_yaml_or_json(args.params)
    args.llm_config = load_llm_config(args.llm_config)
    args.plan_cache = None if args.no_cache else args.plan_cache

    exts = ("*.yaml", "*.yml", "*.txt", "*.md")
    cases = []
    for e in exts:
        cases.extend(glob.glob(os.path.join(args.case_dir, e)))
    cases = sorted(set(cases))
    if not cases:
        print("[ci] 用例目录无文件: %s" % args.case_dir)
        sys.exit(2)

    results = []
    for c in cases:
        print("\n[ci] === %s ===" % os.path.basename(c))
        results.append(run_one(c, args))

    if args.junit:
        d = os.path.dirname(args.junit)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(args.junit, "w", encoding="utf-8") as f:
            f.write(to_junit_xml(results))
        print("\n[ci] JUnit 报告: %s" % args.junit)

    npass = sum(1 for r in results if r["status"] == "PASS")
    print("[ci] 汇总: %d/%d 通过" % (npass, len(results)))
    sys.exit(0 if npass == len(results) else 1)


if __name__ == "__main__":
    main()
