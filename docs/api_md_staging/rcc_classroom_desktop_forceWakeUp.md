---
version: '2.0'
api:
  url: /rcc/classroom/desktop/forceWakeUp
  method: POST
  name: 教室云桌面强制唤醒：对课堂VDI桌面批量下发唤醒指令，学生机走座位唤醒、教师机走教师唤醒。
  controller: RccClassroomDesktopController
  method_ref: forceWakeUp
  permission: '@EnableAuthority'
  exec_mode: batch
  async: false
  description: 教室云桌面强制唤醒：对课堂VDI桌面批量下发唤醒指令，学生机走座位唤醒、教师机走教师唤醒。
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: create_classroom
  api: POST /rcc/classroom/create
  purpose: 创建教室（异步批处理任务，出参BatchTaskSubmitResult）
  request:
    body:
      classroomName: ${param.classroom_name}
  idempotent: recreate
  delete_api: /rcc/classroom/delete
  delete_param: classroomId
- name: query_classroom
  api: POST /rcc/classroom/terminal/list
  extract:
    classroomId: $.content.itemArr[0].classroomId
  purpose: 查询教室列表获取classroomId（ViewClassroomInfoEntity.classroomId）；按教室名精确过滤查询教室列表（matchArr.fieldName=classroomName），取 classroomId
  request:
    body:
      matchArr:
      - fieldName: classroomName
        matchType: EQUAL
        value: ${param.classroom_name}
- name: create_seat
  api: POST /rcc/classroom/seat/batchCreate
  purpose: 批量创建座位（异步批处理任务）
  idempotent: recreate
  delete_api: /rcc/classroom/seat/delete
  delete_param: seatIdArr
- name: query_seat
  api: POST /rcc/classroom/seat/list
  extract:
    seatId: $.content.itemArr[0].id
    terminalId: $.content.itemArr[0].terminalId
  purpose: 按座位桌面名过滤（exactMatchArr.name=desktopName）
  request:
    body:
      exactMatchArr:
      - name: desktopName
        valueArr:
        - ${param.desktop_name}
- name: query_desktop
  api: POST /rcc/classroom/desktop/list
  extract:
    desktopId: $.content.itemArr[0].desktopId
  purpose: 按桌面名过滤（matchArr.fieldName=computerName）
  request:
    body:
      matchArr:
      - fieldName: computerName
        matchType: LIKE
        value: ${param.computer_name}
request:
  dto: IdArrWebRequest
  body:
    idArr:
      type: UUID[]
      required: true
      constraint: '@NotEmpty 非空'
      description: 云桌面ID数组
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    content:
      type: BatchTaskSubmitResult
      description: 批量任务提交结果（taskId等），唤醒指令由后台批任务异步下发
polling:
  api: common_get_msgct_detail_info
  method: POST
  params:
    msgrelationid: ${content.taskId}
  interval_ms: 2000
  timeout_ms: 120000
  terminal_states:
    success:
    - SUCCESS
    failure:
    - FAILURE
    - PARTIAL_SUCCESS

upstream:
- api: POST /rcc/classroom/desktop/list
  produces: $.content.itemArr[*].desktopId
  purpose: 桌面ID数组来自桌面列表查询出参（ViewDesktopResultDTO.desktopId）
downstream:
- api: 内部调用:SeatAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: idArr
  rule: 非空
  failure: 参数校验失败（@NotEmpty）
- level: BIZ
  field: desktop
  rule: 桌面必须存在且能查询到
  failure: 单项失败 rcdc_rcc_desktop_force_wake_up_item_fail_desc
- level: BIZ
  field: desktop
  rule: 桌面须处于运行中（RUNNING）
  failure: 唤醒仅对运行中桌面生效；学生桌面无独立开机接口，运行中状态须通过上课（POST /rcc/classroom/cmrcef/lesson/start）间接达成
assertions:
  success:
  - scenario: 课堂桌面存在且可唤醒
    expect: 批量任务提交成功，逐台唤醒成功返回成功项；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  failure:
  - scenario: 桌面不存在或唤醒失败
    trigger: 桌面已删除/离线或平台唤醒命令异常
    expect: $.status=="SUCCESS"；content.taskId 非空；轮询终态对应项 batchTaskItemStatus==FAILURE；审计 rcdc_rcc_desktop_force_wake_up_fail_log
cleanup: []
idempotency:
  level: data_level
  note: 唤醒对已唤醒桌面重复执行通常无害（状态已一致），但每次提交都会新建批任务并重新下发指令
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
  - name: desktop_name
    desc: ''
    used_by: 见 setup/request
  - name: computer_name
    desc: ''
    used_by: setup/request
---
# POST /rcc/classroom/desktop/forceWakeUp

> 教室云桌面强制唤醒：对课堂VDI桌面批量下发唤醒指令，学生机走座位唤醒、教师机走教师唤醒。 ｜ @EnableAuthority ｜ batch

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/desktop/list"]
    end
    B["POST /rcc/classroom/desktop/forceWakeUp<br>教室云桌面强制唤醒：对课堂VDI桌面批量下发唤醒指令，学生机走座位唤醒、教师机走<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: 断言 request 与 builder 非空"]
        C2["Step2: 取 idArr 并 distinct 构建 DefaultBatchTaskIt"]
        C3["Step3: 创建 RccForceWakeUpDesktopBatchTaskHandler"]
        C4["Step4: 单条设置单任务名称/描述，多条 enableParallel 并行"]
        C5["Step5: 提交批量任务并返回 BatchTaskSubmitResult"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
        C4 --> C5
    end
    B --> C1
    subgraph 下游消费方
        D1["（无 HTTP 下游）"]
    end
    B -->|数据| D1
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rcc/classroom/desktop/forceWakeUp |
| Controller | RccClassroomDesktopController |
| 方法名 | forceWakeUp |
| 权限注解 | @EnableAuthority |
| 执行方式 | batch |
| 业务含义 | 教室云桌面强制唤醒：对课堂VDI桌面批量下发唤醒指令，学生机走座位唤醒、教师机走教师唤醒。 |

## 入参详情

### IdArrWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| idArr | UUID[] | 是 | @NotEmpty 非空 | 云桌面ID数组 |

## 出参详情

| 返回类型 | DefaultWebResponse |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| content | BatchTaskSubmitResult | 批量任务提交结果（taskId等），唤醒指令由后台批任务异步下发 |

## 上游前置业务

### 前置1：POST /rcc/classroom/desktop/list

桌面ID数组来自桌面列表查询出参（ViewDesktopResultDTO.desktopId）（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：RccForceWakeUpDesktopBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | deskMgmtAPI.findById(id) 取桌面名 |
| 2 | classroomDesktopRelationAPI.isTeacherDesk(id) 判断教师桌面 |
| 3 | 学生桌面：seatAPI.getSeatInfoByVDIDesktopId 后 seatAPI.wakeUpDesktop(seatId) |
| 4 | 教师桌面：teacherOperateAPI.wakeUpDesktop(id) |
| 5 | 成功记 RCDC_RCC_DESKTOP_FORCE_WAKE_UP_SUC_LOG，失败记 FAIL_LOG 并返回 FAILURE 项 |

### 处理流程

1. 断言 request 与 builder 非空
2. 取 idArr 并 distinct 构建 DefaultBatchTaskItem 迭代器
3. 创建 RccForceWakeUpDesktopBatchTaskHandler 并注入 deskMgmtAPI/seatAPI/auditLogAPI/classroomDesktopRelationAPI/teacherOperateAPI
4. 单条设置单任务名称/描述，多条 enableParallel 并行
5. 提交批量任务并返回 BatchTaskSubmitResult

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | idArr | 非空 | 参数校验失败（@NotEmpty） |
| BIZ | desktop | 桌面必须存在且能查询到 | 单项失败 rcdc_rcc_desktop_force_wake_up_item_fail_desc |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| idArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

> ⚠️ 断言以 HTTP 响应为准（status + msgKey / BatchTaskSubmitResult），非服务端审计日志。

### 成功场景

| 场景 | 断言点 |
|---|---|
| 课堂桌面存在且可唤醒 | 批量任务提交成功，逐台唤醒成功返回成功项；轮询 content.taskId 至终态 batchTaskItemStatus∈["SUCCESS"] |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 桌面不存在或唤醒失败 | 桌面已删除/离线或平台唤醒命令异常 | $.status=="SUCCESS"；content.taskId 非空；轮询终态对应项 batchTaskItemStatus==FAILURE；审计 rcdc_rcc_desktop_force_wake_up_fail_log |
## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | medium |
| 说明 | 唤醒对已唤醒桌面重复执行通常无害（状态已一致），但每次提交都会新建批任务并重新下发指令 |
