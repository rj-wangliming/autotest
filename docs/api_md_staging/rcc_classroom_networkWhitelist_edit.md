---
version: '2.0'
api:
  url: /rcc/classroom/networkWhitelist/edit
  method: POST
  name: 修改教室禁网白名单：校验IP合法性与重复后提交编辑白名单批处理任务
  controller: RccClassroomManageController
  method_ref: editNetworkWhiteList
  permission: '@EnableAuthority'
  exec_mode: async_batch
  async: false
  description: 修改教室禁网白名单：校验IP合法性与重复后提交编辑白名单批处理任务
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
  dto: EditNetworkWhiteListRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 教室ID
      value: ${prev.query_classroom.output.classroomId}
    whiteListId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 禁网白名单ID
      value: ${prev.get_white_list.output.whiteListId}
    startIp:
      type: String
      required: true
      constraint: '@NotNull 非空（内部校验IPv4）'
      description: 起始IP
      value: ${param.start_ip}
    endIp:
      type: String
      required: true
      constraint: '@NotNull 非空（内部校验IPv4）'
      description: 结束IP
      value: ${param.end_ip}
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
      description: 编辑白名单批处理任务ID
    taskName:
      type: String
      description: 任务名称（编辑白名单批任务）
    taskDesc:
      type: String
      description: 任务描述（编辑白名单批任务）
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
  purpose: 待编辑白名单ID（NetworkWhiteListDTO.id）
downstream:
- api: 内部调用:RccNetworkWhiteListAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: request
  field: classroomId/whiteListId/startIp/endIp
  rule: '@NotNull 非空'
  failure: webmvc 参数校验异常
- level: request
  field: startIp/endIp
  rule: checkNetworkValid 校验合法IPv4与起止区间
  failure: IP格式非法抛异常
- level: business
  field: startIp/endIp
  rule: 新IP区间不能与教室其他白名单重复
  failure: checkIpDuplicate 抛异常
assertions:
  success:
  - scenario: IP合法且不重复
    expect: $.status=="SUCCESS"；$.content.taskId 非空（批处理任务已提交）
  failure:
  - scenario: IP格式非法
    trigger: startIp/endIp 非IPv4或start>end
    expect: status==ERROR（checkNetworkValid 抛 IP 格式/网段校验异常，如 RCDC_RCC_NETWORK_WHITELIST_START_IP_NET_INVALID）
  - scenario: IP区间重复
    trigger: 新区间与其他白名单相交
    expect: status==ERROR；msgKey==RCDC_RCC_NETWORK_WHITELIST_ERR
  - scenario: 白名单不存在
    trigger: whiteListId 无效
    expect: $.status=="SUCCESS"；轮询终态对应项 batchTaskItemStatus==FAILURE
cleanup: []
idempotency:
  level: data_level
  note: 无版本控制，重复提交同参数会重复执行编辑+重下发；IP查重仅拦截已存在记录
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
  - name: start_ip
  - name: end_ip
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/networkWhitelist/edit

> 修改教室禁网白名单：校验IP合法性与重复后提交编辑白名单批处理任务 ｜ @EnableAuthority ｜ async_batch

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create -> POST /rcc/classroom/select"]
        A2["POST /rcc/classroom/networkWhitelist/list"]
    end
    B["POST /rcc/classroom/networkWhitelist/edit<br>修改教室禁网白名单：校验IP合法性与重复后提交编辑白名单批处理任务<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    A2 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert 参数非空"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: classroomAPI.getClassroomName 取教室名"]
        C4["Step4: BeanUtils 拷贝到 EditNetworkWhitelistDTO 并 "]
        C5["Step5: networkWhiteListAPI.checkIpDuplicateInCl"]
        C6["Step6: 构造 EditNetworkWhiteBatchTaskItem 与 EditN"]
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
| URL | /rcc/classroom/networkWhitelist/edit |
| Controller | RccClassroomManageController |
| 方法名 | editNetworkWhiteList |
| 权限注解 | @EnableAuthority |
| 执行方式 | async_batch |
| 业务含义 | 修改教室禁网白名单：校验IP合法性与重复后提交编辑白名单批处理任务 |

## 入参详情

### EditNetworkWhiteListRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull 非空 | 教室ID |
| whiteListId | UUID | 是 | @NotNull 非空 | 禁网白名单ID |
| startIp | String | 是 | @NotNull 非空（内部校验IPv4） | 起始IP |
| endIp | String | 是 | @NotNull 非空（内部校验IPv4） | 结束IP |

## 出参详情

| 返回类型 | DefaultWebResponse（data=BatchTaskSubmitResult） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| taskId | UUID | 编辑白名单批处理任务ID |
| taskName | String | 任务名称（编辑白名单批任务） |
| taskDesc | String | 任务描述（编辑白名单批任务） |

## 上游前置业务

### 前置1：POST /rcc/classroom/create -> POST /rcc/classroom/select

create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId（由 field_map 契约映射）

### 前置2：POST /rcc/classroom/networkWhitelist/list

待编辑白名单ID（NetworkWhiteListDTO.id）（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：EditNetworkWhiteListBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | processItem：getNetworkWhitelist(networkId) 预取 → editNetworkWhitelist(request) + reForbidNetwork(classroomId)，记录成功/失败审计 |
| 2 | onFinish：返回 RCDC_RCC_SEAT_OPERATE_NETWORK_EDIT_SUC/FAIL |

### 处理流程

1. Assert 参数非空
2. rccPermissionChecker.checkTerminalGroupPermissionByClassroomId(单教室) 校验权限
3. classroomAPI.getClassroomName 取教室名
4. BeanUtils 拷贝到 EditNetworkWhitelistDTO 并 checkNetworkValid() 校验IP
5. networkWhiteListAPI.checkIpDuplicateInClassroomForManageNetworkWhitelist 查重
6. 构造 EditNetworkWhiteBatchTaskItem 与 EditNetworkWhiteListBatchTaskHandler，enableParallel 提交批处理

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | classroomId/whiteListId/startIp/endIp | @NotNull 非空 | webmvc 参数校验异常 |
| request | startIp/endIp | checkNetworkValid 校验合法IPv4与起止区间 | IP格式非法抛异常 |
| business | startIp/endIp | 新IP区间不能与教室其他白名单重复 | checkIpDuplicate 抛异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| whiteListId | user_input/from_query | 按业务构造 |
| startIp | user_input/from_query | 按业务构造 |
| endIp | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| IP合法且不重复 | $.status=="SUCCESS"；$.content.taskId 非空（批处理任务已提交） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| IP格式非法 | startIp/endIp 非IPv4或start>end | status==ERROR（checkNetworkValid 抛 IP 格式/网段校验异常，如 RCDC_RCC_NETWORK_WHITELIST_START_IP_NET_INVALID） |
| IP区间重复 | 新区间与其他白名单相交 | status==ERROR；msgKey==RCDC_RCC_NETWORK_WHITELIST_ERR |
| 白名单不存在 | whiteListId 无效 | $.status=="SUCCESS"；轮询终态对应项 batchTaskItemStatus==FAILURE |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | low |
| 说明 | 无版本控制，重复提交同参数会重复执行编辑+重下发；IP查重仅拦截已存在记录 |
