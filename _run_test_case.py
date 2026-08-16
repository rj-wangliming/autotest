#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""通过 API 执行测试用例"""
import requests
import json
import time

base_url = "http://127.0.0.1:5001"

use_case = """前置步骤：
    1、教室云桌面列表中有多个云桌面处于运行中
执行步骤：
    1、教室详情 - 云桌面列表中选择多个正在运行的VDI云桌面点击【重启云桌面】按钮重启云桌面
预测结果：
    1、勾选的云桌面重启成功"""

params = {
    "classroom_name": "a_classroom_01",
    "desktop_name": "vd1",
    "desktopPreName": "vdaaa",
    "desktopNameStartNum": 1,
    "seatNum": 1,
    "student_image_name": "",
    "image_name": "",
    "student_start_ip": "1.1.1.2",
}

# 1. 执行用例
print("=== 提交用例 ===")
r = requests.post(f"{base_url}/api/execute", json={
    "use_case": use_case,
    "params": params
    # 不传 base_url，让服务器从 global_params.yaml 加载
}, timeout=10)
print("status:", r.status_code)
data = r.json()
print("response:", json.dumps(data, ensure_ascii=False, indent=2))

sid = data.get("session_id")
if not sid:
    print("ERROR: 没有 session_id")
    exit(1)

# 2. 轮询执行状态
print("\n=== 轮询执行状态 ===")
for i in range(60):
    time.sleep(2)
    r2 = requests.get(f"{base_url}/api/execution/{sid}", timeout=5)
    d = r2.json()
    status = d.get("status")
    logs_count = len(d.get("logs", []))
    print(f"  [{i*2}s] status={status} logs={logs_count}")
    
    # 打印最新日志
    if d.get("logs"):
        last_log = d["logs"][-1]
        print(f"    最新: [{last_log.get('level')}] {last_log.get('msg', '')[:80]}")
    
    if status in ("PASS", "FAIL", "ERROR"):
        break

# 3. 打印最终结果
print("\n=== 最终结果 ===")
r3 = requests.get(f"{base_url}/api/execution/{sid}", timeout=5)
d3 = r3.json()
print("status:", d3.get("status"))
print("log_file:", d3.get("log_file"))
result = d3.get("result", {})
print("result status:", result.get("status"))
print("result error:", result.get("error", ""))

# 打印所有日志
print("\n=== 完整日志 ===")
for log in d3.get("logs", []):
    print(f"  [{log.get('level')}] {log.get('msg', '')}")
