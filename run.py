# -*- coding: utf-8 -*-
"""无封装测试平台启动入口"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.web.app import app, index

if __name__ == "__main__":
    n = len(index.load())
    print(f"✅ 已加载 {n} 个接口文档")
    print("🌐 无封装测试平台: http://127.0.0.1:5001")
    app.run(host="127.0.0.1", port=5001, debug=False)
