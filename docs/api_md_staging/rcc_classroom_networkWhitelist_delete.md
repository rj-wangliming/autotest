---
version: '2.0'
api:
  url: /rcc/classroom/networkWhitelist/delete
  method: POST
  name: 删除教室禁网白名单：按白名单ID数组提交删除批处理，支持单条删除时携带原白名单信息
  controller: RccClassroomManageController
  method_ref: editNetworkWhiteList
  permission: '@EnableAuthority'
  exec_mode: async_batch
  async: false
  description: 删除教室禁网白名单：按白名单ID数组提交删除批处理，支持单条删除时携带原白名单信息
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: create_classroom
  api: POST /rcc/classroom/create
  purpose: 创建教室（异步批任务，需轮询批任务完成后再查询教室）
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
  purpose: 按名称过滤查询教室（searchKeyword=${param.classroom_name}），获取 classroomId
  request:
    body:
      searchKeyword: ${param.classroom_name}
- name: get_white_list
  api: POST /rcc/classroom/networkWhitelist/list
  extract:
    whiteListId: $.content.itemArr[0].id
  purpose: 按起始IP过滤（matchArr.fieldName=startIp）
  request:
    body:
      matchArr:
      - type: FUZZY
        fieldNameArr:
        - startIp
        value: ${param.start_ip}
        matchRule: LIKE
request:
  dto: DeleteNetworkWhiteListRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 教室ID
      value: ${prev.query_classroom.output.classroomId}
    whiteListIdArr:
      type: UUID[]
      required: true
      constraint: '@NotEmpty 非空'
      description: 待删除的禁网白名单ID列表
      value: ${prev.get_white_list.output.whiteListId}
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
      description: 删除白名单批处理任务ID
    taskName:
      type: String
      description: 任务名称（删除白名单批任务）
    taskDesc:
      type: String
      description: 任务描述（删除白名单批任务）
polling:
  api: common_get_msgct_detail_info
  # 公共轮询接口：POST /rco/msgct/msg/detail（消息中心），完整文档见 common_get_msgct_detail_info.md
  method: POST
  params:
    msgrelationid: ${content.taskId}
  interval_ms: 2000
  timeout_ms: 120000
  terminal_states:
    success: [SUCCESS]
    failure: [FAILURE, PARTIAL_SUCCESS]
upstream:
- api: POST /rcc/classroom/create -> POST /rcc/classroom/select
  produces: $.content[0].classroomId
  purpose: create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId
- api: POST /rcc/classroom/networkWhitelist/list
  produces: $.content.itemArr[0].id
  purpose: 待删除白名单ID（NetworkWhiteListDTO.id）
downstream:
- api: 内部调用:RccNetworkWhiteListAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: request
  field: classroomId
  rule: '@NotNull 非空'
  failure: webmvc 参数校验异常
- level: request
  field: whiteListIdArr
  rule: '@NotEmpty 非空'
  failure: webmvc 参数校验异常
- level: business
  field: classroomId
  rule: 管理员需具备该教室终端组数据权限
  failure: rccPermissionChecker 抛出权限异常
assertions:
  success:
  - scenario: 白名单存在且删除成功
    expect: $.status=="SUCCESS"；$.content.taskId 非空（批处理任务已提交）
  failure:
  - scenario: 白名单不存在
    trigger: whiteListIdArr 含已删除/无效ID
    expect: $.status=="SUCCESS"；轮询终态对应项 batchTaskItemStatus==FAILURE
  - scenario: 无权限
    trigger: 教室不在权限范围
    expect: status==ERROR；msgKey==RCDC_SAPCE_DATA_PERMISSION_DENIED
cleanup: []
idempotency:
  level: data_level
  note: 删除不存在的白名单会失败；重复提交相同ID第二次无目标可删
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
  - name: start_ip
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/networkWhitelist/delete

> 删除教室禁网白名单：按白名单ID数组提交删除批处理，支持单条删除时携带原白名单信息 ｜ @EnableAuthority ｜ async_batch

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create -> POST /rcc/classroom/select"]
        A2["POST /rcc/classroom/networkWhitelist/list"]
    end
    B["POST /rcc/classroom/networkWhitelist/delete<br>删除教室禁网白名单：按白名单ID数组提交删除批处理，支持单条删除时携带原白名单信<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    A2 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert 参数非空"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: 构造 whiteListIdArr 的 DefaultBatchTaskItem"]
        C4["Step4: buildSingleTask：isSingleTask()（数组长度1）时 h"]
        C5["Step5: 构造 DeleteNetworkWhiteListBatchTaskHandle"]
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
| URL | /rcc/classroom/networkWhitelist/delete |
| Controller | RccClassroomManageController |
| 方法名 | editNetworkWhiteList |
| 权限注解 | @EnableAuthority |
| 执行方式 | async_batch |
| 业务含义 | 删除教室禁网白名单：按白名单ID数组提交删除批处理，支持单条删除时携带原白名单信息 |

## 入参详情

### DeleteNetworkWhiteListRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull 非空 | 教室ID |
| whiteListIdArr | UUID[] | 是 | @NotEmpty 非空 | 待删除的禁网白名单ID列表 |

## 出参详情

| 返回类型 | DefaultWebResponse（data=BatchTaskSubmitResult） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| taskId | UUID | 删除白名单批处理任务ID |
| taskName | String | 任务名称（删除白名单批任务） |
| taskDesc | String | 任务描述（删除白名单批任务） |

## 上游前置业务

### 前置1：POST /rcc/classroom/create -> POST /rcc/classroom/select

create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId（由 field_map 契约映射）

### 前置2：POST /rcc/classroom/networkWhitelist/list

待删除白名单ID（NetworkWhiteListDTO.id）（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：DeleteNetworkWhiteListBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | processItem：getNetworkWhitelist(networkId) 预取 → deleteNetworkWhiteList(networkId, classroomId)，记录成功/失败审计 |
| 2 | onFinish：reForbidNetwork(classroomId)；单条任务返回删除结果 key，多条按成功/失败返回 RCDC_RCC_SEAT_OPERATE_NETWORK_DELETE_RESULT |

### 处理流程

1. Assert 参数非空
2. rccPermissionChecker.checkTerminalGroupPermissionByClassroomId(单教室) 校验权限
3. 构造 whiteListIdArr 的 DefaultBatchTaskItem 迭代器
4. buildSingleTask：isSingleTask()（数组长度1）时 handler.setEnableSingleTask(true) 并预取该白名单 DTO
5. 构造 DeleteNetworkWhiteListBatchTaskHandler，enableParallel 提交批处理

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | classroomId | @NotNull 非空 | webmvc 参数校验异常 |
| request | whiteListIdArr | @NotEmpty 非空 | webmvc 参数校验异常 |
| business | classroomId | 管理员需具备该教室终端组数据权限 | rccPermissionChecker 抛出权限异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| whiteListIdArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 白名单存在且删除成功 | $.status=="SUCCESS"；$.content.taskId 非空（批处理任务已提交） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 白名单不存在 | whiteListIdArr 含已删除/无效ID | $.status=="SUCCESS"；轮询终态对应项 batchTaskItemStatus==FAILURE |
| 无权限 | 教室不在权限范围 | status==ERROR；msgKey==RCDC_SAPCE_DATA_PERMISSION_DENIED |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | medium |
| 说明 | 删除不存在的白名单会失败；重复提交相同ID第二次无目标可删 |
