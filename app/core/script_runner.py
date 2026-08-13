# -*- coding: utf-8 -*-
"""裸脚本隔离执行（subprocess 隔离容器）

不再拼装业务代码字符串——业务全部由 executor.run_plan() 方法调用执行。
本模块只做隔离：把 plan+params 序列化传给 subprocess 固定入口，实时捕获日志。
"""
import json
import os
import sys
import time


class ScriptRunner:
    """subprocess 隔离执行器：固定入口 + 数据传递（无字符串拼装）"""

    def __init__(self, executor_module="app.core.executor"):
        self.executor_module = executor_module

    def _build_entry(self, plan_path, params_path, base_url):
        """生成固定入口命令（唯一字符串拼装点是入口调用，非业务代码）"""
        return [
            sys.executable, "-c",
            "import sys,json;"
            "sys.path.insert(0, '.');"
            "from %s import run_plan;"
            "plan=json.load(open('%s'));"
            "params=json.load(open('%s')) if __import__('os').path.exists('%s') else {};"
            "run_plan(plan, params, '%s')"
            % (self.executor_module, plan_path, params_path, params_path, base_url),
        ]

    def run_isolated(self, plan, params, base_url, timeout=120, log_cb=None):
        """subprocess 隔离执行：plan 数据 → 固定入口 → run_plan 方法调用"""
        import subprocess as sp
        import tempfile

        # 序列化 plan/params 到临时文件（数据传递，非代码）
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as pf:
            json.dump(plan, pf, ensure_ascii=False)
            plan_path = pf.name
        params_path = ""
        if params:
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as pf:
                json.dump(params, pf, ensure_ascii=False)
                params_path = pf.name

        env = {"TEST_BASE_URL": base_url, "PYTHONUNBUFFERED": "1"}
        cmd = self._build_entry(plan_path, params_path, base_url)
        proc = sp.Popen(cmd, env=env, stdout=sp.PIPE, stderr=sp.STDOUT, text=True)
        logs = []
        deadline = time.time() + timeout
        try:
            while True:
                if proc.poll() is not None:
                    rest = proc.stdout.read()
                    if rest:
                        logs.extend(l.strip() for l in rest.splitlines() if l.strip())
                    break
                if time.time() > deadline:
                    proc.kill()
                    logs.append("[error] 执行超时")
                    if log_cb:
                        log_cb("error", "执行超时")
                    break
                line = proc.stdout.readline()
                if line:
                    line = line.strip()
                    logs.append(line)
                    if log_cb:
                        log_cb("info", line)
                else:
                    time.sleep(0.05)
        finally:
            # 清理临时文件
            for p in (plan_path, params_path):
                if p and os.path.exists(p):
                    try:
                        os.unlink(p)
                    except Exception:
                        pass

        rc = proc.poll()
        passed = rc == 0 and any("[result] PASS" in l for l in logs)
        return {"status": "PASS" if passed else "FAIL", "exit_code": rc, "logs": logs,
                "script": "隔离执行（executor.run_plan 方法调用，无拼装脚本）"}
