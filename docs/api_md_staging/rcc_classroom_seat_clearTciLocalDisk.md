---
version: '2.0'
api:
  url: /rcc/classroom/seat/clearTciLocalDisk
  method: POST
  name: 批量清空 TCI/IDV 终端本地数据盘，校验终端权限后批处理逐台下发清盘命令
  controller: RccSeatManageController
  method_ref: clearTciLocalDisk
  permission: '@EnableAuthority'
  exec_mode: 异步批处理任务（BatchTask，ClearTciLocalDiskBatchTaskHandler，enableParallel 并行）
  async: true
  description: 批量清空 TCI/IDV 终端本地数据盘，校验终端权限后批处理逐台下发清盘命令
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
  dto: TerminalIdArrWebRequest
  body:
    idArr:
      type: String[]
      required: true
      constraint: '@NotEmpty + @Size(min=1)'
      description: 终端ID数组
      value: ${param.id_arr}
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
  # 公共轮询接口：POST /rco/msgct/msg/detail（消息中心），完整文档见 common_get_msgct_detail_info.md
  method: POST
  params:
    msgrelationid: ${content.taskId}
  interval_ms: 2000
  timeout_ms: 120000
  terminal_states:
    success:
    - SUCCESS
    - PARTIAL_SUCCESS
    failure:
    - FAILURE
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
- level: PERM
  field: idArr
  rule: 终端组数据权限
  failure: 无权限抛业务异常
- level: BIZ
  field: terminalId
  rule: 终端须支持 IDV/TCI 本地盘清空
  failure: 清盘命令失败批任务项 FAILURE（RCDC_RCC_SEAT_OPERATE_CLEAR_TCI_LOCAL_DIS
assertions:
  success:
  - scenario: 传入合法 IDV/TCI 终端ID
    expect: $.status=="SUCCESS" 且 $.content.taskId 非空；逐台清空本地数据盘并审计成功；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  failure:
  - scenario: 清盘命令失败
    trigger: clearIdvTerminalDataDisk 抛错
    expect: $.status=="SUCCESS" 且 $.content.taskId 非空；轮询 content.taskId 至终态 batchTaskItemStatus==FAILURE 并审计失败日志
  - scenario: 无终端权限
    trigger: 权限校验抛错
    expect: $.status=="ERROR"（数据权限校验失败，msgKey 由权限框架决定）
cleanup: []
idempotency:
  level: data_level
  note: 重复调用会再次清空终端本地数据盘
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
  - name: id_arr
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/seat/clearTciLocalDisk

> 批量清空 TCI/IDV 终端本地数据盘，校验终端权限后批处理逐台下发清盘命令 ｜ @EnableAuthority ｜ 异步批处理任务（BatchTask，ClearTciLocalDiskBatchTaskHandler，enableParallel 并行）

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/seat/list"]
    end
    B["POST /rcc/classroom/seat/clearTciLocalDisk<br>批量清空 TCI/IDV 终端本地数据盘，校验终端权限后批处理逐台下发清盘命令<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull 校验 request/builder/sessio"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: TerminalIdMappingUtils.mapping 构建 idMap "]
        C4["Step4: builder 注册 ClearTciLocalDiskBatchTaskHan"]
        C5["Step5: 返回 DefaultWebResponse.success(result)"]
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
| URL | /rcc/classroom/seat/clearTciLocalDisk |
| Controller | RccSeatManageController |
| 方法名 | clearTciLocalDisk |
| 权限注解 | @EnableAuthority |
| 执行方式 | 异步批处理任务（BatchTask，ClearTciLocalDiskBatchTaskHandler，enableParallel 并行） |
| 业务含义 | 批量清空 TCI/IDV 终端本地数据盘，校验终端权限后批处理逐台下发清盘命令 |

## 入参详情

### TerminalIdArrWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| idArr | String[] | 是 | @NotEmpty + @Size(min=1) | 终端ID数组 |

## 出参详情

| 返回类型 | DefaultWebResponse（data=BatchTaskSubmitResult） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| taskId | UUID | 提交成功的批处理任务标识 |
| taskStatus | String | 批任务初始状态 |

## 上游前置业务

### 前置1：POST /rcc/classroom/seat/list

终端ID数组来自座位列表查询出参（SeatInfoDTO.terminalId）（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：ClearTciLocalDiskBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | idMap 取 terminalId，terminalOperatorAPI.getUpperMacOrTerminalId 取审计标识 |
| 2 | terminalOperatorAPI.clearIdvTerminalDataDisk(terminalId) 下发清盘命令 |
| 3 | 成功：auditLogAPI.recordLog(RCDC_RCC_SEAT_OPERATE_CLEAR_TCI_LOCAL_DISK_SUCCESS_LOG) 返回 SUCCESS |
| 4 | BusinessException：recordLog(FAIL_LOG) 返回 FAILURE |

### 处理流程

1. Assert.notNull 校验 request/builder/sessionContext
2. rccPermissionChecker.checkTerminalGroupPermissionByTerminalId 校验权限
3. TerminalIdMappingUtils.mapping 构建 idMap 与迭代器（RCDC_RCC_SEAT_OPERATE_CLEAR_TCI_LOCAL_DISK_ITEM_NAME）
4. builder 注册 ClearTciLocalDiskBatchTaskHandler 并行启动
5. 返回 DefaultWebResponse.success(result)

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | idArr | @NotEmpty + @Size(min=1) | 为空时参数校验失败 |
| PERM | idArr | 终端组数据权限 | 无权限抛业务异常 |
| BIZ | terminalId | 终端须支持 IDV/TCI 本地盘清空 | 清盘命令失败批任务项 FAILURE（RCDC_RCC_SEAT_OPERATE_CLEAR_TCI_LOCAL_DISK_FAIL_LOG） |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| idArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 传入合法 IDV/TCI 终端ID | $.status=="SUCCESS" 且 $.content.taskId 非空；逐台清空本地数据盘并审计成功；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"] |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 清盘命令失败 | clearIdvTerminalDataDisk 抛错 | $.status=="SUCCESS" 且 $.content.taskId 非空；轮询 content.taskId 至终态 batchTaskItemStatus==FAILURE 并审计失败日志 |
| 无终端权限 | 权限校验抛错 | $.status=="ERROR"（数据权限校验失败，msgKey 由权限框架决定） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | LOW |
| 说明 | 重复调用会再次清空终端本地数据盘 |
