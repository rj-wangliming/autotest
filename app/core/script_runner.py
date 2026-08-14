# -*- coding: utf-8 -*-
"""裸脚本隔离执行（subprocess 隔离容器）

不再拼装业务代码字符串——业务全部由 executor.run_plan() 方法调用执行。
本模块只做隔离：把 plan+params 序列化为 JSON 临时文件，通过独立入口脚本
以命令行参数方式传递路径（避免 Windows 路径 \ 被 Python -c 字符串转义）。
"""
import json
import os
import sys
import time


# 入口脚本模板（独立 .py 文件，不存在路径转义问题）
# __PROJECT_ROOT__ 在写入时被替换为实际项目根目录（使用原始字符串语法防 \ 转义）
_ENTRY_TEMPLATE = r"""\
import sys, json, os

# 先加入项目根目录（确保 app 包可导入）
sys.path.insert(0, r"__PROJECT_ROOT__")
from __MODULE__ import run_plan

plan_path = sys.argv[1]
params_path = sys.argv[2] if len(sys.argv) > 2 and os.path.exists(sys.argv[2]) else ""
base_url = sys.argv[3] if len(sys.argv) > 3 else "http://127.0.0.1:8080"

plan = json.load(open(plan_path, encoding="utf-8"))
params = json.load(open(params_path, encoding="utf-8")) if params_path else {}
run_plan(plan, params, base_url)
"""


class ScriptRunner:
    """subprocess 隔离执行器：独立入口脚本 + 命令行参数（无路径转义问题）"""

    def __init__(self, executor_module="app.core.executor"):
        self.executor_module = executor_module

    def _write_entry_script(self, tmp_dir, project_root):
        """写入入口脚本文件，返回 .py 路径"""
        entry_path = os.path.join(tmp_dir, "_autotest_entry.py")
        with open(entry_path, "w", encoding="utf-8") as f:
            f.write(_ENTRY_TEMPLATE
                    .replace("__PROJECT_ROOT__", project_root)
                    .replace("__MODULE__", self.executor_module))
        return entry_path

    def run_isolated(self, plan, params, base_url, timeout=120, log_cb=None):
        """subprocess 隔离执行：plan/params/entry 都写到临时目录，通过命令行参数传路径"""
        import subprocess as sp
        import tempfile

        tmp_dir = tempfile.mkdtemp(prefix="autotest_")
        try:
            # 序列化 plan/params 到临时文件
            plan_path = os.path.join(tmp_dir, "plan.json")
            with open(plan_path, "w", encoding="utf-8") as pf:
                json.dump(plan, pf, ensure_ascii=False)

            params_path = ""
            if params:
                params_path = os.path.join(tmp_dir, "params.json")
                with open(params_path, "w", encoding="utf-8") as pf:
                    json.dump(params, pf, ensure_ascii=False)

            # 项目根目录（app/core/script_runner.py 的上三级）
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))))

            # 写入入口脚本（注入项目根目录）
            entry_path = self._write_entry_script(tmp_dir, project_root)

            # 继承父进程环境，只覆盖必要的变量
            env = dict(os.environ)
            env["TEST_BASE_URL"] = base_url
            env["PYTHONUNBUFFERED"] = "1"
            cmd = [
                sys.executable,
                entry_path,
                plan_path,
                params_path,
                base_url,
            ]

            proc = sp.run(cmd, cwd=project_root, env=env,
                          stdout=sp.PIPE, stderr=sp.STDOUT, text=True, timeout=timeout)
            logs = proc.stdout.strip().splitlines() if proc.stdout else []
            rc = proc.returncode

        finally:
            # 清理临时目录
            try:
                import shutil
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass

        rc = proc.returncode
        passed = rc == 0 and any("[result] PASS" in l for l in logs)
        return {"status": "PASS" if passed else "FAIL", "exit_code": rc, "logs": logs,
                "script": "隔离执行（executor.run_plan 方法调用，无拼装脚本）"}
