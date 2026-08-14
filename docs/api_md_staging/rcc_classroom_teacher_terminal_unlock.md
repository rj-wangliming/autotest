---
version: '2.0'
api:
  url: /rcc/classroom/teacher/terminal/unlock
  method: POST
  name: 解锁教师机终端：按教室获取教师终端ID映射后批量下发解锁终端管理密码指令。
  controller: RccTeacherManageController
  method_ref: unlockTeacherTerminal
  permission: '@EnableAuthority'
  exec_mode: batch
  async: false
  description: 解锁教师机终端：按教室获取教师终端ID映射后批量下发解锁终端管理密码指令。
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
  dto: BatchUnlockTeacherTerminalRequest
  body:
    classroomIdArr:
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
  purpose: 教室ID数组（BatchUnlockTeacherTerminalRequest.classroomIdArr）来自教室终端列表查询出参（ViewClassroomInfoEntity.classroomId）
downstream:
- api: 内部调用:PlatformRcoCertificationStrategyParameterAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: classroomIdArr
  rule: 非空
  failure: 参数校验失败（@NotEmpty）
- level: BIZ
  field: classroom
  rule: 教室必须配置教师终端
  failure: getTeacherByClassroomId 失败返回 rcdc_rcc_module_operate_fail
- level: STATE
  field: terminal
  rule: 终端必须处于锁定状态
  failure: RCDC_RCC_TERMINAL_HAVE_NOT_CLOCK（终端未锁定）
- level: STATE
  field: terminal
  rule: 终端必须在线
  failure: RCDC_RCC_TERMINAL_UNLOCK_TERMINAL_OFFLINE（终端离线）
assertions:
  success:
  - scenario: 教师终端锁定且在线
    expect: $.status=="SUCCESS" 且 $.content.taskId 非空；逐台解锁成功；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  failure:
  - scenario: 教室未配置教师终端
    trigger: classroomTeacherAPI 抛异常
    expect: $.status=="ERROR" 且 $.msgKey=="rcdc_rcc_module_operate_fail"
  - scenario: 终端未锁定
    trigger: 终端当前未锁定
    expect: $.status=="SUCCESS" 且 $.content.taskId 非空；轮询 content.taskId 至终态 batchTaskItemStatus==FAILURE（rcdc_rcc_terminal_have_not_clock）
  - scenario: 终端离线
    trigger: 终端状态 OFFLINE
    expect: $.status=="SUCCESS" 且 $.content.taskId 非空；轮询 content.taskId 至终态 batchTaskItemStatus==FAILURE（rcdc_rcc_terminal_unlock_terminal_offline）
cleanup: []
prereq_state:
  resource: terminal
  required_state: ONLINE
  achieve_via: []

idempotency:
  level: data_level
  note: 对已解锁终端重复调用会报未锁定错误；对锁定终端重复解锁结果一致
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/teacher/terminal/unlock

> 解锁教师机终端：按教室获取教师终端ID映射后批量下发解锁终端管理密码指令。 ｜ @EnableAuthority ｜ batch

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/terminal/list"]
    end
    B["POST /rcc/classroom/teacher/terminal/unlock<br>解锁教师机终端：按教室获取教师终端ID映射后批量下发解锁终端管理密码指令。<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: 断言 request/builder 非空且 classroomIdArr 非空"]
        C2["Step2: 遍历教室调用 classroomTeacherAPI.getTeacherByC"]
        C3["Step3: 映射失败：记失败审计并返回 fail(rcdc_rcc_module_opera"]
        C4["Step4: 构建任务项，UnlockTerminalBatchTaskHandler（注入 "]
        C5["Step5: 提交批量任务返回结果"]
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
| URL | /rcc/classroom/teacher/terminal/unlock |
| Controller | RccTeacherManageController |
| 方法名 | unlockTeacherTerminal |
| 权限注解 | @EnableAuthority |
| 执行方式 | batch |
| 业务含义 | 解锁教师机终端：按教室获取教师终端ID映射后批量下发解锁终端管理密码指令。 |

## 入参详情

### BatchUnlockTeacherTerminalRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomIdArr | UUID[] | 是 | @NotEmpty 非空 | 教室ID数组 |

## 出参详情

| 返回类型 | DefaultWebResponse |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| content | BatchTaskSubmitResult | 批量任务提交结果 |

## 上游前置业务

### 前置1：POST /rcc/classroom/terminal/list

教室ID数组（BatchUnlockTeacherTerminalRequest.classroomIdArr）来自教室终端列表查询出参（ViewClassroomInfoEntity.classroomId）（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：UnlockTerminalBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | 从 idMap 取终端ID，findBasicInfoByTerminalId 获取真实终端信息 |
| 2 | getTerminalLockedStatusById 判断锁定状态；未锁定则记 RCDC_RCC_TERMINAL_HAVE_NOT_CLOCK 并返回 FAILURE |
| 3 | 终端 OFFLINE 则抛 RCDC_RCC_TERMINAL_UNLOCK_TERMINAL_OFFLINE |
| 4 | certificationStrategyParameterAPI.unlockTerminalManagePwd(terminalId) 下发解锁 |
| 5 | 成功记 RCDC_RCC_TERMINAL_UNLOCK_SUCCESS_LOG，失败记 FAIL_LOG 并返回 FAILURE 项 |

### 处理流程

1. 断言 request/builder 非空且 classroomIdArr 非空
2. 遍历教室调用 classroomTeacherAPI.getTeacherByClassroomId 构建 classroomId->teacherTerminalId 映射
3. 映射失败：记失败审计并返回 fail(rcdc_rcc_module_operate_fail)
4. 构建任务项，UnlockTerminalBatchTaskHandler（注入 certificationStrategyParameterAPI/cbbTerminalOperatorAPI/auditLogAPI，设置 idMap）
5. 提交批量任务返回结果

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | classroomIdArr | 非空 | 参数校验失败（@NotEmpty） |
| BIZ | classroom | 教室必须配置教师终端 | getTeacherByClassroomId 失败返回 rcdc_rcc_module_operate_fail |
| STATE | terminal | 终端必须处于锁定状态 | RCDC_RCC_TERMINAL_HAVE_NOT_CLOCK（终端未锁定） |
| STATE | terminal | 终端必须在线 | RCDC_RCC_TERMINAL_UNLOCK_TERMINAL_OFFLINE（终端离线） |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomIdArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教师终端锁定且在线 | $.status=="SUCCESS" 且 $.content.taskId 非空；逐台解锁成功；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"] |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 教室未配置教师终端 | classroomTeacherAPI 抛异常 | $.status=="ERROR" 且 $.msgKey=="rcdc_rcc_module_operate_fail" |
| 终端未锁定 | 终端当前未锁定 | $.status=="SUCCESS" 且 $.content.taskId 非空；轮询 content.taskId 至终态 batchTaskItemStatus==FAILURE（rcdc_rcc_terminal_have_not_clock） |
| 终端离线 | 终端状态 OFFLINE | $.status=="SUCCESS" 且 $.content.taskId 非空；轮询 content.taskId 至终态 batchTaskItemStatus==FAILURE（rcdc_rcc_terminal_unlock_terminal_offline） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | medium |
| 说明 | 对已解锁终端重复调用会报未锁定错误；对锁定终端重复解锁结果一致 |
