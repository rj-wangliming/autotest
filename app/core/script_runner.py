# -*- coding: utf-8 -*-
"""裸脚本隔离执行（subprocess 隔离容器）

不再拼装业务代码字符串——业务全部由 executor.run_plan() 方法调用执行。
本模块只做隔离：把 plan+params 序列化为 JSON 临时文件，通过独立入口脚本
以命令行参数方式传递路径（避免 Windows 路径 \\ 被 Python -c 字符串转义）。
兼容 Windows / Linux。

实时日志：
- 方案 A：subprocess.Popen 逐行读取 stdout，通过 log_cb 实时回传
- 方案 B：子进程每步追加一行到日志文件，父进程 polling 获取最新
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

    实时日志机制：
    - 方案 A：Popen 逐行读取 stdout，log_cb 实时回传
    - 方案 B：子进程追加日志到文件，父进程 polling 获取最新
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
        - 实时日志：Popen 逐行读 stdout（方案A）+ 文件追加 polling（方案B）
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
                    json.dump(params, pf, encoding="utf-8")

            # 项目根目录（app/core/script_runner.py 的上三级）
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))))

            # 日志文件（方案 B：子进程追加，父进程 polling）
            log_file = os.path.join(tmp_dir, "realtime.log")

            # 写入入口脚本（注入项目根目录 + 日志文件路径）
            entry_path = self._write_entry_script(tmp_dir, project_root)
            # 注入日志文件路径到环境变量
            env = dict(os.environ)
            env["AUTOTEST_LOG_FILE"] = log_file
            env["TEST_BASE_URL"] = base_url
            env["PYTHONUNBUFFERED"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"
            cmd = [
                sys.executable,
                entry_path,
                plan_path,
                params_path,
                base_url,
            ]

            logs = []
            rc = -1
            real_time_lines = []

            try:
                # 方案 A：Popen 逐行读 stdout
                proc = sp.Popen(
                    cmd,
                    cwd=project_root,
                    env=env,
                    stdout=sp.PIPE,
                    stderr=sp.STDOUT,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                )

                # 方案 B：poll 日志文件获取最新内容
                poll_interval = 0.3  # 300ms polling
                last_size = 0
                file_done = False

                def _poll_log_file():
                    """读取日志文件，返回新行"""
                    nonlocal last_size, file_done
                    try:
                        size = os.path.getsize(log_file)
                        if size == 0 and file_done:
                            return
                        with open(log_file, "r", encoding="utf-8") as f:
                            f.seek(last_size)
                            new_content = f.read()
                        last_size = f.tell()
                        if new_content:
                            lines = new_content.strip().splitlines()
                            real_time_lines.extend(lines)
                    except Exception:
                        pass

                # 主循环：读 stdout + poll 文件
                while True:
                    line = proc.stdout.readline()
                    if line:
                        logs.append(line.rstrip("\n"))
                        if log_cb:
                            log_cb("info", line.rstrip("\n"))
                    else:
                        # stdout 为空，poll 日志文件
                        _poll_log_file()
                        retcode = proc.poll()
                        if retcode is not None:
                            # 子进程结束，读剩余 stdout
                            remaining = proc.stdout.read()
                            if remaining:
                                for rl in remaining.strip().splitlines():
                                    logs.append(rl)
                                    if log_cb:
                                        log_cb("info", rl)
                            file_done = True
                            _poll_log_file()  # 最后一次 poll
                            rc = retcode
                            break
                        time.sleep(poll_interval)

                # 超时处理
                if rc < 0:
                    proc.kill()
                    remaining = proc.stdout.read() if proc.stdout else ""
                    if remaining:
                        for rl in remaining.strip().splitlines():
                            logs.append(rl)
                            if log_cb:
                                log_cb("info", rl)
                    file_done = True
                    _poll_log_file()
                    rc = -1
                    # 补上超时标记
                    logs.append("[error] 子进程执行超时(%ss)" % timeout)

            except sp.TimeoutExpired as e:
                logs.append("[error] 子进程执行超时(%ss)" % timeout)
                rc = -1
            except Exception as e:
                logs.append("[error] 子进程启动/执行异常: %s" % e)
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
