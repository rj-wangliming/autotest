---
version: '2.0'
api:
  url: /rcc/classroom/seat/network/cancelDisable
  method: POST
  name: 批量取消禁网（恢复联网）：将教室座位终端网络恢复，处理流程与禁网对称，批处理逐台调用联网命令
  controller: RccSeatManageController
  method_ref: cancelDisableSeatNetwork
  permission: '@EnableAuthority'
  exec_mode: 异步批处理任务（BatchTask，EnableSeatNetworkBatchTaskHandler，enableParallel + enablePerformanceMode 性能模式）
  async: true
  description: 批量取消禁网（恢复联网）：将教室座位终端网络恢复，处理流程与禁网对称，批处理逐台调用联网命令
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
request:
  dto: DisableNetworkRequest
  body:
    seatIdArr:
      type: UUID[]
      required: true
      constraint: '@NotEmpty 至少一个座位'
      description: 待恢复联网的座位ID数组
    disableNetwork:
      type: Boolean
      required: true
      constraint: '@NotNull'
      description: 禁网状态：false=恢复联网
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
  produces: $.content.itemArr[*].id
  purpose: 座位ID数组来自座位列表查询出参（SeatInfoDTO.id），座位由/rcc/classroom/seat/batchCreate创建
downstream: []
constraints:
- level: PARAM
  field: seatIdArr
  rule: '@NotEmpty'
  failure: 为空时参数校验失败
- level: PARAM
  field: disableNetwork
  rule: '@NotNull'
  failure: 为空时 NetStateEnum.getNotify Assert 抛错
- level: PERM
  field: classroomId
  rule: 教室终端组权限
  failure: 无权限抛业务异常
- level: BIZ
  field: seatId
  rule: 座位必须存在
  failure: 批任务项 FAILURE（RCDC_RCC_SEAT_OPERATE_ENABLE_NETWORK_SINGLE_FAI
assertions:
  success:
  - scenario: 传入有效座位ID且 disableNetwork=false
    expect: $.status=="SUCCESS" 且 $.content.taskId 非空；逐台恢复联网并审计成功；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  failure:
  - scenario: 座位不存在/联网命令失败
    trigger: disableSingleSeatNetwork 抛错
    expect: $.status=="SUCCESS" 且 $.content.taskId 非空；轮询 content.taskId 至终态 batchTaskItemStatus==FAILURE 并审计失败日志
  - scenario: disableNetwork 为空
    trigger: 请求缺参
    expect: $.status=="ERROR"（NetStateEnum.getNotify Assert 抛 IllegalArgumentException）
cleanup: []
idempotency:
  level: data_level
  note: 重复调用会再次下发联网命令
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
  - name: desktop_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/seat/network/cancelDisable

> 批量取消禁网（恢复联网）：将教室座位终端网络恢复，处理流程与禁网对称，批处理逐台调用联网命令 ｜ @EnableAuthority ｜ 异步批处理任务（BatchTask，EnableSeatNetworkBatchTaskHandler，enableParallel + enablePerformanceMode 性能模式）

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/seat/list"]
    end
    B["POST /rcc/classroom/seat/network/cancelDisable<br>批量取消禁网（恢复联网）：将教室座位终端网络恢复，处理流程与禁网对称，批处理逐台<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull 校验 request/builder/sessio"]
        C2["Step2: doDisableNetwork：NetStateEnum.getNotify("]
        C3["Step3: getClassroomIdBySeatId 反查教室 → 权限校验 → cla"]
        C4["Step4: netStateEnum=ENABLE_NETWORK → getBatchEn"]
        C5["Step5: builder.setTaskName(RCDC_RCC_SEAT_OPERAT"]
        C6["Step6: 返回 DefaultWebResponse.success(result)"]
        C1 --> C2
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
| URL | /rcc/classroom/seat/network/cancelDisable |
| Controller | RccSeatManageController |
| 方法名 | cancelDisableSeatNetwork |
| 权限注解 | @EnableAuthority |
| 执行方式 | 异步批处理任务（BatchTask，EnableSeatNetworkBatchTaskHandler，enableParallel + enablePerformanceMode 性能模式） |
| 业务含义 | 批量取消禁网（恢复联网）：将教室座位终端网络恢复，处理流程与禁网对称，批处理逐台调用联网命令 |

## 入参详情

### DisableNetworkRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| seatIdArr | UUID[] | 是 | @NotEmpty 至少一个座位 | 待恢复联网的座位ID数组 |
| disableNetwork | Boolean | 是 | @NotNull | 禁网状态：false=恢复联网 |

## 出参详情

| 返回类型 | DefaultWebResponse（data=BatchTaskSubmitResult） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| taskId | UUID | 提交成功的批处理任务标识 |
| taskStatus | String | 批任务初始状态 |

## 上游前置业务

### 前置1：POST /rcc/classroom/seat/list

座位ID数组来自座位列表查询出参（SeatInfoDTO.id），座位由/rcc/classroom/seat/batchCreate创建（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：EnableSeatNetworkBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | seatAPI.getSeatInfo(seatId) 取座位与桌面名 |
| 2 | seatAPI.disableSingleSeatNetwork(seatId, NetStateEnum.ENABLE_NETWORK) 下发联网 |
| 3 | 成功：auditLogAPI.recordLog(RCDC_RCC_SEAT_OPERATE_ENABLE_NETWORK_SINGLE_SUC_LOG) 返回 SUCCESS |
| 4 | BusinessException：recordLog(ENABLE_NETWORK_SINGLE_FAIL_LOG) 返回 FAILURE |

### 处理流程

1. Assert.notNull 校验 request/builder/sessionContext
2. doDisableNetwork：NetStateEnum.getNotify(disableNetwork) 转换枚举
3. getClassroomIdBySeatId 反查教室 → 权限校验 → classroomName
4. netStateEnum=ENABLE_NETWORK → getBatchEnableDefaultWebResponse：构造 EnableSeatNetworkBatchTaskHandler（disableSeat=true）
5. builder.setTaskName(RCDC_RCC_SEAT_OPERATE_ENABLE_NETWORK_SINGLE_TASK_NAME).enableParallel().enablePerformanceMode(...) 启动
6. 返回 DefaultWebResponse.success(result)

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | seatIdArr | @NotEmpty | 为空时参数校验失败 |
| PARAM | disableNetwork | @NotNull | 为空时 NetStateEnum.getNotify Assert 抛错 |
| PERM | classroomId | 教室终端组权限 | 无权限抛业务异常 |
| BIZ | seatId | 座位必须存在 | 批任务项 FAILURE（RCDC_RCC_SEAT_OPERATE_ENABLE_NETWORK_SINGLE_FAIL_LOG） |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| seatIdArr | user_input/from_query | 按业务构造 |
| disableNetwork | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 传入有效座位ID且 disableNetwork=false | $.status=="SUCCESS" 且 $.content.taskId 非空；逐台恢复联网并审计成功；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"] |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 座位不存在/联网命令失败 | disableSingleSeatNetwork 抛错 | $.status=="SUCCESS" 且 $.content.taskId 非空；轮询 content.taskId 至终态 batchTaskItemStatus==FAILURE 并审计失败日志 |
| disableNetwork 为空 | 请求缺参 | $.status=="ERROR"（NetStateEnum.getNotify Assert 抛 IllegalArgumentException） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | LOW |
| 说明 | 重复调用会再次下发联网命令 |
