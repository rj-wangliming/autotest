# -*- coding: utf-8 -*-
"""无封装测试平台启动入口"""
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.logger import setup_app_logging
setup_app_logging()  # 项目运行日志 → logs/app/YYYY-MM-DD.log

from app.web.app import app, index

logger = logging.getLogger("autotest")

if __name__ == "__main__":
    n = len(index.load())
    logger.info("✅ 已加载 %d 个接口文档", n)
    logger.info("🌐 无封装测试平台: http://127.0.0.1:5001")
    app.run(host="127.0.0.1", port=5001, debug=False)
