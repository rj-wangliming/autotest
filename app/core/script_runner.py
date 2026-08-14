# -*- coding: utf-8 -*-
"""裸脚本隔离执行（subprocess 隔离容器）

不再拼装业务代码字符串——业务全部由 executor.run_plan() 方法调用执行。
本模块只做隔离：把 plan+params 序列化为 JSON 临时文件，通过独立入口脚本
以命令行参数方式传递路径（避免 Windows 路径 \\ 被 Python -c 字符串转义）。
兼容 Windows / Linux。
"""
import json
import os
import sys
import time


# 入口脚本模板（独立 .py 文件，不存在路径转义问题）
# __PROJECT_ROOT__ 在写入时被替换为实际项目根目录
# 使用原始字符串 r"" 防止 Windows 路径中的 \ 被解释为转义序列
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
    """subprocess 隔离执行器：独立入口脚本 + 命令行参数（无路径转义问题）

    跨平台兼容：
    - Windows：路径含 \，-c 拼接会被转义，entry 脚本 + r"" 解决
    - Linux：路径为 /，无转义问题，同样兼容
    """

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
        """subprocess 隔离执行：plan/params/entry 都写到临时目录，通过命令行参数传路径

        - 独立 .py 入口脚本避免 -c 字符串中的路径转义问题（Windows / Linux）
        - 继承完整父进程环境变量，避免子进程初始化缺失变量导致崩溃
        """
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

            # 继承父进程完整环境变量，只覆盖必要的变量
            # 父进程 env 缺失会导致子进程 Python 初始化失败（Windows 上
            # _Py_HashRandomization_Init 报错）
            env = dict(os.environ)
            env["TEST_BASE_URL"] = base_url
            env["PYTHONUNBUFFERED"] = "1"
            # 子进程强制 UTF-8 输出，避免 Windows cp936 编码导致 stdout 捕获失败/乱码
            env["PYTHONIOENCODING"] = "utf-8"
            cmd = [
                sys.executable,
                entry_path,
                plan_path,
                params_path,
                base_url,
            ]

            try:
                proc = sp.run(cmd, cwd=project_root, env=env,
                              stdout=sp.PIPE, stderr=sp.STDOUT,
                              encoding="utf-8", errors="replace", timeout=timeout)
                logs = proc.stdout.strip().splitlines() if proc.stdout else []
                rc = proc.returncode
            except sp.TimeoutExpired as e:
                out = e.stdout or b""
                if isinstance(out, bytes):
                    out = out.decode("utf-8", "replace")
                logs = (out.strip().splitlines() if out else []) + [
                    "[error] 子进程执行超时(%ss)，以下为超时前已捕获的输出" % timeout]
                rc = -1
            except Exception as e:
                logs = ["[error] 子进程启动/执行异常: %s" % e]
                rc = -1

        finally:
            # 清理临时目录
            try:
                import shutil
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass

        passed = rc == 0 and any("[result] PASS" in l for l in logs)
        return {"status": "PASS" if passed else "FAIL", "exit_code": rc, "logs": logs,
                "script": "隔离执行（executor.run_plan 方法调用，无拼装脚本）"}
