---
version: '2.0'
api:
  url: /rcc/classroom/networkWhitelist/create
  method: POST
  name: 创建教室禁网白名单：校验IP合法性与该教室IP重复后提交创建白名单批处理任务
  controller: RccClassroomManageController
  method_ref: createNetworkWhiteList
  permission: '@EnableAuthority'
  exec_mode: async_batch
  async: false
  description: 创建教室禁网白名单：校验IP合法性与该教室IP重复后提交创建白名单批处理任务
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
request:
  dto: CreateNetworkWhiteListRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 教室ID；ID 来自前置步骤 setup 产出（${prev.*}）
      value: ${prev.query_classroom.output.classroomId}
    startIp:
      type: String
      required: true
      constraint: '@NotNull 非空（内部再校验IPv4格式/区间）'
      description: 起始IP
      value: ${param.startIp}
    endIp:
      type: String
      required: true
      constraint: '@NotNull 非空（内部再校验IPv4格式/区间）'
      description: 结束IP
      value: ${param.endIp}
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
      description: 创建白名单批处理任务ID
    taskName:
      type: String
      description: 任务名称（创建白名单批任务）
    taskDesc:
      type: String
      description: 任务描述（创建白名单批任务）
upstream:
- api: POST /rcc/classroom/create -> POST /rcc/classroom/select
  produces: $.content[0].classroomId
  purpose: create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId
downstream:
- api: POST /rcc/classroom/networkWhitelist/delete|edit|getWhiteList
  purpose: 产出的禁网白名单ID（NetworkWhiteListDTO.id），create 为异步批任务响应不含ID，需经 list 查询
constraints:
- level: request
  field: startIp/endIp
  rule: '@NotNull 且 checkNetworkValid 校验合法IPv4与start<=end'
  failure: IP格式非法或起止颠倒抛异常
- level: business
  field: startIp/endIp
  rule: IP区间不能与教室已有白名单重复
  failure: checkIpDuplicateInClassroomForManageNetworkWhitelist 抛异常
- level: business
  field: classroomId
  rule: 管理员需具备该教室终端组数据权限
  failure: rccPermissionChecker 抛出权限异常
assertions:
  success:
  - scenario: IP合法且不重复
    expect: $.status=="SUCCESS"；$.content.taskId 非空（批处理任务已提交）
  failure:
  - scenario: IP格式非法
    trigger: startIp/endIp 非IPv4或start>end
    expect: status==ERROR（checkNetworkValid 抛 IP 格式/网段校验异常，如 RCDC_RCC_NETWORK_WHITELIST_START_IP_NET_INVALID）
  - scenario: IP区间重复
    trigger: 该教室已存在相交白名单
    expect: status==ERROR；msgKey==RCDC_RCC_NETWORK_WHITELIST_ERR
cleanup:
- api: POST /rcc/classroom/networkWhitelist/delete
  purpose: 删除创建的网络白名单（需先取 id）
  depends_on: content.id
idempotency:
  level: data_level
  note: IP查重仅拦截已存在记录，并发/重复提交可能创建重复白名单
params:
  required:
  - name: classroom_name
  - name: endIp
    desc: ''
    used_by: 见 setup/request
  - name: startIp
    desc: ''
    used_by: 见 setup/request
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/networkWhitelist/create

> 创建教室禁网白名单：校验IP合法性与该教室IP重复后提交创建白名单批处理任务 ｜ @EnableAuthority ｜ async_batch

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create -> POST /rcc/classroom/select"]
    end
    B["POST /rcc/classroom/networkWhitelist/create<br>创建教室禁网白名单：校验IP合法性与该教室IP重复后提交创建白名单批处理任务<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert request/builder/sessionContext 非空"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: classroomAPI.getClassroomName 取教室名"]
        C4["Step4: BeanUtils 拷贝到 CreateNetworkWhitelistDTO "]
        C5["Step5: networkWhiteListAPI.checkIpDuplicateInCl"]
        C6["Step6: 构造 CreateNetworkWhiteBatchTaskItem 与 Cre"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
        C4 --> C5
        C5 --> C6
    end
    B --> C1
    subgraph 下游消费方
        D1["POST /rcc/classroom/networkWhitelist/delete|edit|getWhiteList"]
    end
    B -->|数据| D1
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rcc/classroom/networkWhitelist/create |
| Controller | RccClassroomManageController |
| 方法名 | createNetworkWhiteList |
| 权限注解 | @EnableAuthority |
| 执行方式 | async_batch |
| 业务含义 | 创建教室禁网白名单：校验IP合法性与该教室IP重复后提交创建白名单批处理任务 |

## 入参详情

### CreateNetworkWhiteListRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull 非空 | 教室ID |
| startIp | String | 是 | @NotNull 非空（内部再校验IPv4格式/区间） | 起始IP |
| endIp | String | 是 | @NotNull 非空（内部再校验IPv4格式/区间） | 结束IP |

## 出参详情

| 返回类型 | DefaultWebResponse（data=BatchTaskSubmitResult） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| taskId | UUID | 创建白名单批处理任务ID |
| taskName | String | 任务名称（创建白名单批任务） |
| taskDesc | String | 任务描述（创建白名单批任务） |

## 上游前置业务

### 前置1：POST /rcc/classroom/create -> POST /rcc/classroom/select

create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：CreateNetworkWhiteListBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | processItem：networkWhiteListAPI.createNetworkWhitelist(request) + reForbidNetwork(classroomId)，记录成功/失败审计 |
| 2 | onFinish：按成功失败数返回 RCDC_RCC_SEAT_OPERATE_NETWORK_CREATE_SUC/FAIL |

### 处理流程

1. Assert request/builder/sessionContext 非空
2. rccPermissionChecker.checkTerminalGroupPermissionByClassroomId(单教室, sessionContext) 校验权限
3. classroomAPI.getClassroomName 取教室名
4. BeanUtils 拷贝到 CreateNetworkWhitelistDTO 并 checkNetworkValid() 校验IP格式与起止区间
5. networkWhiteListAPI.checkIpDuplicateInClassroomForManageNetworkWhitelist 查重
6. 构造 CreateNetworkWhiteBatchTaskItem 与 CreateNetworkWhiteListBatchTaskHandler，enableParallel 提交批处理

## 下游消费方

### 消费1：POST /rcc/classroom/networkWhitelist/delete|edit|getWhiteList

产出的禁网白名单ID（NetworkWhiteListDTO.id），create 为异步批任务响应不含ID，需经 list 查询（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | startIp/endIp | @NotNull 且 checkNetworkValid 校验合法IPv4与start<=end | IP格式非法或起止颠倒抛异常 |
| business | startIp/endIp | IP区间不能与教室已有白名单重复 | checkIpDuplicateInClassroomForManageNetworkWhitelist 抛异常 |
| business | classroomId | 管理员需具备该教室终端组数据权限 | rccPermissionChecker 抛出权限异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
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
| IP区间重复 | 该教室已存在相交白名单 | status==ERROR；msgKey==RCDC_RCC_NETWORK_WHITELIST_ERR |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | low |
| 说明 | IP查重仅拦截已存在记录，并发/重复提交可能创建重复白名单 |
