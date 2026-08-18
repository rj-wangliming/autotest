---
version: '2.0'
api:
  url: /rcc/classroom/network/cancelDisable
  method: POST
  name: 教室批量解除禁网（恢复网络），与禁网流程一致，disableNetwork=false 时走启用网络批处理
  controller: RccClassroomManageController
  method_ref: batchCancelDisableNetwork
  permission: '@EnableAuthority'
  exec_mode: async_batch
  async: false
  description: 教室批量解除禁网（恢复网络），与禁网流程一致，disableNetwork=false 时走启用网络批处理
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: createClassroom
  api: POST /rcc/classroom/create
  purpose: 创建教室
  extract:
    classroomName: ${param.classroom_name}
  request:
    body:
      classroomName: ${param.classroom_name}
  idempotent: recreate
  delete_api: /rcc/classroom/delete
  delete_param: classroomId
- name: listClassroom
  api: POST /rcc/classroom/list
  purpose: 查询教室ID；按教室名精确过滤分页查询教室（matchArr.fieldName=classroomName），取 classroomId
  extract:
    classroomId: $.content.itemArr[0].classroomId
  request:
    body:
      matchArr:
      - type: EXACT
        fieldName: classroomName
        valueArr:
        - ${param.classroom_name}
        matchRule: EQ
request:
  dto: BatchDisableNetworkRequest
  body:
    classroomIdArr:
      type: UUID[]
      required: true
      constraint: '@NotEmpty 非空'
      description: 教室ID列表
      value: ${prev.listClassroom.output.classroomId}
    disableNetwork:
      type: Boolean
      required: true
      constraint: '@NotNull 非空'
      description: false=解除禁网/启用网络
      value: ${param.disable_network}
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    taskId:
      type: UUID
      description: 启用网络批处理任务ID（无座位时为空）
polling:
  api: common_get_msgct_detail_info
  # 公共轮询接口：POST /rco/msgct/msg/detail（消息中心），完整文档见 common_get_msgct_detail_info.md
  method: POST
  params:
    msgrelationid: ${content.taskId}
  optional_when_no_correlation: true
  interval_ms: 2000
  timeout_ms: 120000
  terminal_states:
    success: [SUCCESS]
    failure: [FAILURE, PARTIAL_SUCCESS]
upstream:
- api: 内部调用:ClassroomAPI
  purpose: 设置教室级网络状态为启用
- api: 内部调用:CmrClientAPI
  purpose: 通知CMR
- api: 内部调用:SeatAPI
  purpose: 取教室座位ID
- api: 内部调用:PlatformRcoGlobalParameterAPI
  purpose: 读取并发线程数参数
downstream:
- api: 内部调用:SeatAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: request
  field: classroomIdArr/disableNetwork
  rule: '@NotEmpty/@NotNull'
  failure: webmvc 参数校验异常
- level: business
  field: classroomIdArr
  rule: 管理员需具备教室终端组数据权限
  failure: rccPermissionChecker 抛出权限异常
assertions:
  success:
  - scenario: 教室有座位
    expect: $.status=="SUCCESS"；$.content.taskId 非空（批处理任务已提交）
  failure:
  - scenario: 无权限
    trigger: 教室不在权限范围
    expect: status==ERROR；msgKey==RCDC_SAPCE_DATA_PERMISSION_DENIED
cleanup: []
idempotency:
  level: data_level
  note: 逐座位执行且无防重，重复提交重复下发启用指令；教室级状态重复设置幂等
params:
  required:
  - name: classroom_name
  - name: disable_network
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/network/cancelDisable

> 教室批量解除禁网（恢复网络），与禁网流程一致，disableNetwork=false 时走启用网络批处理 ｜ @EnableAuthority ｜ async_batch

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/network/cancelDisable<br>教室批量解除禁网（恢复网络），与禁网流程一致，disableNetwork=fa<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert 参数非空"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: doBatchDisableNetwork：逐教室设置 ENABLE_NETWO"]
        C4["Step4: 取座位；无座位直接成功；有座位走 getBatchEnableDefaultWe"]
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
| URL | /rcc/classroom/network/cancelDisable |
| Controller | RccClassroomManageController |
| 方法名 | batchCancelDisableNetwork |
| 权限注解 | @EnableAuthority |
| 执行方式 | async_batch |
| 业务含义 | 教室批量解除禁网（恢复网络），与禁网流程一致，disableNetwork=false 时走启用网络批处理 |

## 入参详情

### BatchDisableNetworkRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomIdArr | UUID[] | 是 | @NotEmpty 非空 | 教室ID列表 |
| disableNetwork | Boolean | 是 | @NotNull 非空 | false=解除禁网/启用网络 |

## 出参详情

| 返回类型 | DefaultWebResponse<BatchTaskSubmitResult|SuccessResultResponse> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| taskId | UUID | 启用网络批处理任务ID（无座位时为空） |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 批量处理器：EnableSeatNetworkBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | processItem 逐座位 seatAPI.disableSingleSeatNetwork(seatId, ENABLE_NETWORK) |
| 2 | onFinish 调 seatAPI.refreshDeskInfo 并返回结果 |

### 处理流程

1. Assert 参数非空
2. rccPermissionChecker.checkTerminalGroupPermissionByClassroomId 校验权限
3. doBatchDisableNetwork：逐教室设置 ENABLE_NETWORK + 通知CMR + 记录启用网络审计
4. 取座位；无座位直接成功；有座位走 getBatchEnableDefaultWebResponse 提交 EnableSeatNetworkBatchTaskHandler

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | classroomIdArr/disableNetwork | @NotEmpty/@NotNull | webmvc 参数校验异常 |
| business | classroomIdArr | 管理员需具备教室终端组数据权限 | rccPermissionChecker 抛出权限异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomIdArr | user_input/from_query | 按业务构造 |
| disableNetwork | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教室有座位 | $.status=="SUCCESS"；$.content.taskId 非空（批处理任务已提交） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 无权限 | 教室不在权限范围 | status==ERROR；msgKey==RCDC_SAPCE_DATA_PERMISSION_DENIED |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | low |
| 说明 | 逐座位执行且无防重，重复提交重复下发启用指令；教室级状态重复设置幂等 |
