import requests, time

case_text = """前置步骤：
【前置】创建教室策略（若已存在同名则幂等通过）
【前置】获取学生机教室策略ID（可选）；按策略名精确过滤
【前置】创建教室（异步批处理任务，出参BatchTask需轮询）
【前置】查询教室列表获取classroomId
【前置】批量创建座位（异步批处理任务）；若教室已分配学生
【前置】按座位桌面名过滤
【前置】获取计算集群ID；取第一条
【前置】查询教室VDI数据盘存储池ID
【前置】获取 VDI 课程策略ID；按策略名精确过滤
【前置】按镜像名精确过滤
【前置】获取计算集群ID与云平台ID；取第一条
【前置】获取存储池ID；取第一条
【前置】获取网络ID；取第一条
【操作】给学生机教室分配课程镜像
【预期】镜像分配成功，桌面可用

参数：
classroom_name: a_classroom_05
classroom_strategy_name: a_cl_strategy_05
desktopPreName: vdtje
strategy_name_vdi: a_strategy_vdi_05
image_name: TEST_WIN10_64_VDI_P
student_image_name: TEST_WIN10_64_VDI_P
student_start_ip: 1.1.1.2
enable_teacher: true
desktopNum: 1
studentModeArr: ["VDI"]
teacher_mode: PC
seatNum: 1
studentEndIp: 1.1.1.3
studentStartIp: 1.1.1.2
teacherIp: 1.1.1.1
"""

resp = requests.post(
    'http://127.0.0.1:5001/api/execute',
    json={"use_case": case_text, "base_url": "https://10.51.167.250:8443/rcdc"},
    timeout=30
)
sid = resp.json().get('session_id', '')
print('Session:', sid)

# Wait for result
for i in range(120):
    time.sleep(5)
    detail = requests.get('http://127.0.0.1:5001/api/execution/' + sid).json()
    status = detail.get('status', '')
    logs = detail.get('logs', [])
    plan = detail.get('plan_meta', {})
    if status in ('done', 'running'):
        print('\n=== Plan Steps:', len(plan.get('steps', [])), '===')
        for s in plan.get('steps', []):
            auto = ' [auto]' if s.get('auto_by_rules') else ''
            print(f'  {s.get("step_name", "")}{auto}: {s.get("api", "")}')
        # Check for auto_provision related steps
        step_names = [s.get('step_name', '') for s in plan.get('steps', [])]
        create_vdi = any('create_vdi' in n for n in step_names)
        get_vdi = any('get_vdi' in n for n in step_names)
        assign_img = any('assign' in n for n in step_names)
        print(f'\n  create_vdi: {create_vdi}, get_vdi: {get_vdi}, assign_img: {assign_img}')
        
        if status == 'done':
            result = detail.get('result', {})
            steps = result.get('steps', [])
            print(f'\n=== Execution: {len(steps)} steps ===')
            for st in steps:
                tag = '✓' if st.get('status') == 'PASS' else ('✗' if st.get('status') == 'FAIL' else '?')
                msg = f'{tag} {st.get("step_name", "")}: {st.get("status", "")}'
                if st.get('error'):
                    msg += f' | {str(st["error"])[:150]}'
                print(msg)
            print('Result:', result.get('status', '?'))
            break
        elif i % 10 == 0:
            print(f'  [poll {i//10}] Running... steps in plan: {len(plan.get("steps", []))}')
