---
version: '2.0'
api:
  url: /rcc/classroom/teacher/terminal/wake
  method: POST
  name: 按教室唤醒教师机终端：批量获取教师终端信息后下发唤醒指令（WOL/网络唤醒）。
  controller: RccTeacherManageController
  method_ref: wakeTerminalByClassroom
  permission: '@EnableAuthority'
  exec_mode: batch
  async: false
  description: 按教室唤醒教师机终端：批量获取教师终端信息后下发唤醒指令（WOL/网络唤醒）。
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
  purpose: 按教室名精确过滤（matchArr.fieldName=classroomName）
  request:
    body:
      matchArr:
      - fieldName: classroomName
        matchType: EQUAL
        value: ${param.classroom_name}
request:
  dto: WakeTerminalByClassroomWebRequest
  body:
    classroomArr:
      type: UUID[]
      required: true
      constraint: '@NotEmpty 非空'
      description: 教室ID数组
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
      description: 批量任务提交结果
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
- api: POST /rcc/classroom/terminal/list
  produces: $.content.itemArr[*].classroomId
  purpose: 教室ID数组（WakeTerminalByClassroomWebRequest.classroomArr）来自教室终端列表查询出参（ViewClassroomInfoEntity.classroomId）
downstream:
- api: 内部调用:RccTerminalOperatorAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: classroomArr
  rule: 非空
  failure: 参数校验失败（@NotEmpty）
- level: BIZ
  field: classroom
  rule: 教室必须配置教师终端
  failure: RCDC_RCC_CLASSROOM_TERMINAL_NOT_FIND_MAC（未找到教师终端）
assertions:
  success:
  - scenario: 教室配置教师终端
    expect: $.status=="SUCCESS" 且 $.content.taskId 非空；逐台唤醒成功；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  failure:
  - scenario: 教室未配置教师终端
    trigger: getTeacherInfo 返回空或终端ID为空
    expect: $.status=="SUCCESS" 且 $.content.taskId 非空；轮询 content.taskId 至终态 batchTaskItemStatus==FAILURE（rcdc_rcc_classroom_terminal_not_find_mac）
cleanup: []
idempotency:
  level: data_level
  note: 唤醒对已开机终端重复执行基本无害（状态已一致）
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/teacher/terminal/wake

> 按教室唤醒教师机终端：批量获取教师终端信息后下发唤醒指令（WOL/网络唤醒）。 ｜ @EnableAuthority ｜ batch

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/terminal/list"]
    end
    B["POST /rcc/classroom/teacher/terminal/wake<br>按教室唤醒教师机终端：批量获取教师终端信息后下发唤醒指令（WOL/网络唤醒）。<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: 断言 request 与 builder 非空"]
        C2["Step2: 取 classroomArr 构建任务项迭代器"]
        C3["Step3: 创建 WakeTeacherTerminalBatchTaskHandler 并"]
        C4["Step4: enableParallel 提交批量任务返回结果"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
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
| URL | /rcc/classroom/teacher/terminal/wake |
| Controller | RccTeacherManageController |
| 方法名 | wakeTerminalByClassroom |
| 权限注解 | @EnableAuthority |
| 执行方式 | batch |
| 业务含义 | 按教室唤醒教师机终端：批量获取教师终端信息后下发唤醒指令（WOL/网络唤醒）。 |

## 入参详情

### WakeTerminalByClassroomWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomArr | UUID[] | 是 | @NotEmpty 非空 | 教室ID数组 |

## 出参详情

| 返回类型 | DefaultWebResponse |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| content | BatchTaskSubmitResult | 批量任务提交结果 |

## 上游前置业务

### 前置1：POST /rcc/classroom/terminal/list

教室ID数组（WakeTerminalByClassroomWebRequest.classroomArr）来自教室终端列表查询出参（ViewClassroomInfoEntity.classroomId）（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：WakeTeacherTerminalBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | classroomAPI.getClassroomName(classroomId) 取教室名 |
| 2 | classroomAPI.getTeacherInfo(classroomId)：无教师终端则抛 RCDC_RCC_CLASSROOM_TERMINAL_NOT_FIND_MAC |
| 3 | 构造 TerminaOperatorReqInfoDTO{terminalId, srcPort, destPort} |
| 4 | terminalOperatorAPI.wakeupTerminal 下发唤醒 |
| 5 | 成功记 RCDC_RCC_TEACHER_WAKE_SUC_LOG，失败记 FAIL_LOG（或 COMMON_SIMPLE_FAIL）并返回 FAILURE 项 |

### 处理流程

1. 断言 request 与 builder 非空
2. 取 classroomArr 构建任务项迭代器
3. 创建 WakeTeacherTerminalBatchTaskHandler 并注入 auditLogAPI/cbbPhysicalServerMgmtAPI/rcoGlobalParameterAPI/cbbTerminalOperatorAPI/classroomAPI/terminalOperatorAPI
4. enableParallel 提交批量任务返回结果

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | classroomArr | 非空 | 参数校验失败（@NotEmpty） |
| BIZ | classroom | 教室必须配置教师终端 | RCDC_RCC_CLASSROOM_TERMINAL_NOT_FIND_MAC（未找到教师终端） |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教室配置教师终端 | $.status=="SUCCESS" 且 $.content.taskId 非空；逐台唤醒成功；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"] |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 教室未配置教师终端 | getTeacherInfo 返回空或终端ID为空 | $.status=="SUCCESS" 且 $.content.taskId 非空；轮询 content.taskId 至终态 batchTaskItemStatus==FAILURE（rcdc_rcc_classroom_terminal_not_find_mac） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | medium |
| 说明 | 唤醒对已开机终端重复执行基本无害（状态已一致） |
