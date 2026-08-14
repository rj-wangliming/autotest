# -*- coding: utf-8 -*-
"""日志落盘：项目运行日志 + 用例执行日志

两类日志独立存放：
- 项目运行日志：logs/app/YYYY-MM-DD.log（按天滚，Flask 请求/异常/启动）
- 用例执行日志：logs/cases/YYYY-MM-DD/HHMMSS_<用例名>.log（每次执行一个文件）

设计原则：
- 落盘点接在「日志汇聚点」，不侵入 executor 各处 self.log 调用
- Web 在 _run_use_case 的 log 回调汇聚（编排 + 子进程 stdout 回传都过这里）
- CLI 在 run_one 传 log_cb 给 run_plan（同时 print 控制台 + 写文件）
"""
import logging
import logging.handlers
import os
import time

# app/core/logger.py → 上两级 = 项目根
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_ROOT = os.path.join(PROJECT_ROOT, "logs")
APP_LOG_DIR = os.path.join(LOG_ROOT, "app")
CASE_LOG_DIR = os.path.join(LOG_ROOT, "cases")

_app_logger_configured = False


def setup_app_logging():
    """配置项目运行日志：根 logger 加按天滚动 FileHandler + 控制台 StreamHandler。

    werkzeug(Flask 请求日志)清掉自带 handler 后冒泡到 root，落盘且不重复。
    幂等：多次调用不重复添加 handler。
    """
    global _app_logger_configured
    if _app_logger_configured:
        return
    os.makedirs(APP_LOG_DIR, exist_ok=True)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S")

    fh = logging.handlers.TimedRotatingFileHandler(
        os.path.join(APP_LOG_DIR, time.strftime("%Y-%m-%d") + ".log"),
        when="midnight", backupCount=14, encoding="utf-8")
    fh.setFormatter(fmt)

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    # 避免重复添加（如 reload）
    root.handlers = [h for h in root.handlers
                     if not isinstance(h, (logging.StreamHandler,))]
    root.addHandler(fh)
    root.addHandler(sh)

    # werkzeug 请求日志：清自带 handler，冒泡到 root（落盘 + 不重复）
    wk = logging.getLogger("werkzeug")
    wk.handlers = []
    wk.propagate = True
    wk.setLevel(logging.INFO)

    _app_logger_configured = True
    logging.getLogger("autotest").info("项目运行日志已启用 → %s", APP_LOG_DIR)


def _sanitize(name):
    """文件名安全化：保留字母数字中文，其余替为 _，限长 40"""
    return "".join(c if (c.isalnum() or c in "-_") else "_" for c in (name or "case"))[:40]


def new_case_log(case_name):
    """创建一次用例执行的日志文件路径，返回绝对路径（不打开文件）。

    目录：logs/cases/YYYY-MM-DD/HHMMSS_<用例名>.log
    """
    date_dir = os.path.join(CASE_LOG_DIR, time.strftime("%Y-%m-%d"))
    os.makedirs(date_dir, exist_ok=True)
    ts = time.strftime("%H%M%S")
    path = os.path.join(date_dir, "%s_%s.log" % (ts, _sanitize(case_name)))
    return path


class CaseFileLogger:
    """用例执行日志文件写句柄：追加写 + 即时 flush，close() 关闭。

    线程安全说明：Web 后台线程内单线程写，无需加锁。
    """

    def __init__(self, log_path):
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self._fp = open(log_path, "a", encoding="utf-8")

    def write(self, level, msg):
        self._fp.write("%s [%s] %s\n" % (time.strftime("%H:%M:%S"), level, msg))
        self._fp.flush()

    def close(self):
        try:
            self._fp.close()
        except Exception:
            pass
