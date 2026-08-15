---
version: '2.0'
api:
  url: /rcc/classroom/seat/terminal/init
  method: POST
  name: 批量初始化 IDV 学生终端，校验终端为座位终端并做权限校验后，通过 ClassroomTerminalHandler 提交初始化批任务（课堂默认不保留镜像，可
  controller: RccSeatManageController
  method_ref: idvInit
  permission: '@EnableAuthority'
  exec_mode: 异步批处理任务（BatchTask，InitIdvBatchTaskHandler，串行）
  async: true
  description: 批量初始化 IDV 学生终端，校验终端为座位终端并做权限校验后，通过 ClassroomTerminalHandler 提交初始化批任务（课堂默认不保留镜像，可按需强制初始化公共终端）
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
  api: POST /rcc/classroom/select
  extract:
    classroomId: $.content[0].classroomId
  purpose: 按教室名精确过滤（matchArr.fieldName=classroomName）
  request:
    body:
      matchArr:
      - type: EXACT
        fieldName: classroomName
        valueArr:
        - ${param.classroom_name}
        matchRule: EQ
- name: create_seat
  api: POST /rcc/classroom/seat/batchCreate
  purpose: 批量创建座位（异步批处理任务）
  request:
    body:
      classroomId:
        value: ${prev.query_classroom.output.classroomId}
      desktopPreName:
        value: ${param.desktopPreName}
      desktopNameStartNum:
        value: ${param.desktopNameStartNum}
      seatNum:
        value: ${param.seatNum}
      studentModeArr:
        value: [VDI]
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
request:
  dto: InitTerminalIdArrWebRequest
  body:
    idArr:
      type: String[]
      required: true
      constraint: '@NotEmpty + @Size(min=1)'
      description: 终端ID数组
      value: ${param.id_arr}
    enableForceInitPublic:
      type: Boolean
      required: true
      constraint: '@NotNull'
      description: 是否强制初始化公共终端
      value: ${param.enable_force_init_public}
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    taskStatus:
      type: String
      description: 批任务初始状态
    taskId:
      type: UUID
      description: 提交成功的批处理任务标识
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
- api: POST /rcc/classroom/seat/list
  produces: $.content.itemArr[*].terminalId
  purpose: 终端ID数组来自座位列表查询出参（SeatInfoDTO.terminalId）
downstream: []
constraints:
- level: PARAM
  field: idArr
  rule: '@NotEmpty + @Size(min=1)'
  failure: 为空时参数校验失败
- level: PARAM
  field: enableForceInitPublic
  rule: '@NotNull'
  failure: 为空时参数校验失败
- level: PERM
  field: idArr
  rule: 终端组数据权限
  failure: 无权限抛业务异常
- level: BIZ
  field: idArr
  rule: 终端必须为座位终端
  failure: validSeatByterminalIdArr 抛错
- level: BIZ
  field: terminalId
  rule: 终端须支持 IDV 初始化
  failure: 初始化命令下发失败批任务项 FAILURE（RCDC_RCC_TERMINAL_INIT_TERMINAL_FAIL）
assertions:
  success:
  - scenario: 传入合法 IDV 座位终端
    expect: $.status=="SUCCESS" 且 $.content.taskId 非空；逐台下发初始化命令并审计成功；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  failure:
  - scenario: 终端非法/非座位终端
    trigger: validSeatByterminalIdArr 抛错
    expect: $.status=="ERROR" 且 $.msgKey=="rcdc_rcc_terminal_not_seat"；无任务提交
  - scenario: 初始化命令下发失败
    trigger: initialize 抛 BusinessException
    expect: $.status=="SUCCESS" 且 $.content.taskId 非空；轮询 content.taskId 至终态 batchTaskItemStatus==FAILURE（审计 RCDC_RCC_TERMINAL_INIT_TERMINAL_FAIL）
cleanup: []
idempotency:
  level: data_level
  note: 重复调用会再次触发终端初始化（重装/重置终端环境）
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
  - name: desktop_name
  - name: desktopNameStartNum
    desc: ''
    used_by: 见 setup/request
  - name: desktopPreName
    desc: ''
    used_by: 见 setup/request
  - name: seatNum
    desc: ''
    used_by: 见 setup/request
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/seat/terminal/init

> 批量初始化 IDV 学生终端，校验终端为座位终端并做权限校验后，通过 ClassroomTerminalHandler 提交初始化批任务（课堂默认不保留镜像，可按需强制初始化公共终端） ｜ @EnableAuthority ｜ 异步批处理任务（BatchTask，InitIdvBatchTaskHandler，串行）

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/seat/list"]
    end
    B["POST /rcc/classroom/seat/terminal/init<br>批量初始化 IDV 学生终端，校验终端为座位终端并做权限校验后，通过 Class<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull 校验 request/builder/sessio"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: seatAPI.validSeatByterminalIdArr 校验终端合法"]
        C4["Step4: classroomTerminalHandler.batchInitTermin"]
        C5["Step5: 构造迭代器（RCDC_RCC_TERMINAL_INIT_TERMINAL_IT"]
        C6["Step6: builder.setTaskName(...) 启动任务"]
        C1 --> C2
        C7["Step7: 返回 CommonWebResponse.success(result)"]
        C6 --> C7
        C2 --> C3
        C3 --> C4
        C4 --> C5
        C5 --> C6
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
| URL | /rcc/classroom/seat/terminal/init |
| Controller | RccSeatManageController |
| 方法名 | idvInit |
| 权限注解 | @EnableAuthority |
| 执行方式 | 异步批处理任务（BatchTask，InitIdvBatchTaskHandler，串行） |
| 业务含义 | 批量初始化 IDV 学生终端，校验终端为座位终端并做权限校验后，通过 ClassroomTerminalHandler 提交初始化批任务（课堂默认不保留镜像，可按需强制初始化公共终端） |

## 入参详情

### InitTerminalIdArrWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| idArr | String[] | 是 | @NotEmpty + @Size(min=1) | 终端ID数组 |
| enableForceInitPublic | Boolean | 是 | @NotNull | 是否强制初始化公共终端 |

## 出参详情

| 返回类型 | CommonWebResponse<BatchTaskSubmitResult> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| taskId | UUID | 提交成功的批处理任务标识 |
| taskStatus | String | 批任务初始状态 |

## 上游前置业务

### 前置1：POST /rcc/classroom/seat/list

终端ID数组来自座位列表查询出参（SeatInfoDTO.terminalId）（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：InitIdvBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | idMap 取 terminalId |
| 2 | cbbTerminalOperatorAPI.findBasicInfoByTerminalId 取 upperMacAddrOrTerminalId 审计标识 |
| 3 | platformRcoUserTerminalMgmtAPI.initialize(new InitTerminalRequest(terminalId, FALSE, enableForceInitPublic)) |
| 4 | 成功：auditLogAPI.recordLog(RCDC_RCC_TERMINAL_INIT_TERMINAL_SUCCESS) 返回 SUCCESS |
| 5 | TerminalOperateSuccessBusinessException：记录成功提示（RCDC_RCC_TERMINAL_INIT_TERMINAL_SUCCESS_HAS_WARN）返回 SUCCESS |
| 6 | BusinessException：recordLog(RCDC_RCC_TERMINAL_INIT_TERMINAL_FAIL) 返回 FAILURE |

### 处理流程

1. Assert.notNull 校验 request/builder/sessionContext
2. rccPermissionChecker.checkTerminalGroupPermissionByTerminalId 校验权限
3. seatAPI.validSeatByterminalIdArr 校验终端合法
4. classroomTerminalHandler.batchInitTerminalTask(request, builder)：TerminalIdMappingUtils.mapping 构建 idMap
5. 构造迭代器（RCDC_RCC_TERMINAL_INIT_TERMINAL_ITEM_NAME）注册 InitIdvBatchTaskHandler 并 setEnableForceInitPublic
6. builder.setTaskName(...) 启动任务
7. 返回 CommonWebResponse.success(result)

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | idArr | @NotEmpty + @Size(min=1) | 为空时参数校验失败 |
| PARAM | enableForceInitPublic | @NotNull | 为空时参数校验失败 |
| PERM | idArr | 终端组数据权限 | 无权限抛业务异常 |
| BIZ | idArr | 终端必须为座位终端 | validSeatByterminalIdArr 抛错 |
| BIZ | terminalId | 终端须支持 IDV 初始化 | 初始化命令下发失败批任务项 FAILURE（RCDC_RCC_TERMINAL_INIT_TERMINAL_FAIL） |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| idArr | user_input/from_query | 按业务构造 |
| enableForceInitPublic | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 传入合法 IDV 座位终端 | $.status=="SUCCESS" 且 $.content.taskId 非空；逐台下发初始化命令并审计成功；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"] |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 终端非法/非座位终端 | validSeatByterminalIdArr 抛错 | $.status=="ERROR" 且 $.msgKey=="rcdc_rcc_terminal_not_seat"；无任务提交 |
| 初始化命令下发失败 | initialize 抛 BusinessException | $.status=="SUCCESS" 且 $.content.taskId 非空；轮询 content.taskId 至终态 batchTaskItemStatus==FAILURE（审计 RCDC_RCC_TERMINAL_INIT_TERMINAL_FAIL） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | LOW |
| 说明 | 重复调用会再次触发终端初始化（重装/重置终端环境） |
