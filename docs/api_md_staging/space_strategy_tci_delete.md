---
version: '2.0'
api:
  url: /space/strategy/tci/delete
  method: POST
  name: 批量删除 TCI 课程策略。框架 defaultBatchDelete 为 idArr 中每个 id 注册批量删除任务；每条 processItem 先做数据权
  controller: SpaceDeskStrategyGroupTCIController
  method_ref: batchDelete
  permission: '@EnableAuthority'
  exec_mode: 异步批量任务：批量注册删除任务，逐条校验+删除状态机（不可撤销）
  async: true
  description: 批量删除 TCI 课程策略。框架 defaultBatchDelete 为 idArr 中每个 id 注册批量删除任务；每条 processItem 先做数据权限校验（checkAdminDataPermission），再调 loadAPI().deleteById → SpaceStrategyGroupTCIValidation.validateBeforeDelete：策略状态必须 AVAI
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: create_tci_strategy
  api: POST /space/strategy/tci/create
  purpose: 创建TCI策略
  request:
    body:
      name: ${param.strategy_name}
  idempotent: reuse
  reuse_query:
    api: POST /space/strategy/tci/list
    body:
      page: 0
      limit: 20
      matchArr:
      - type: EXACT
        fieldName: strategyName
        valueArr:
        - ${param.strategy_name}
        matchRule: EQ
    extract:
      lessonStrategyId: $.content.itemArr[0].id
- name: list_tci_strategy
  api: POST /space/strategy/tci/list
  extract:
    strategyIdArr: $.content.itemArr[*].id
  purpose: 获取策略ID
request:
  dto: IdArrWebRequest（框架类）
  body:
    idArr:
      type: UUID[]
      required: true
      constraint: 非空（Assert.notNull(webRequest)）
      description: 待删除 TCI 课程策略 id 数组
      value: ${prev.list_tci_strategy.output.strategyIdArr}
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    result:
      type: String
      description: 任务提交结果/状态
    taskId:
      type: String
      description: 批量任务 id
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
- api: POST /space/strategy/tci/list
  purpose: TCI课程策略ID数组，来源为策略列表
downstream:
- api: POST /space/strategy/tci/list
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: AUTH
  field: 接口
  rule: '@EnableAuthority 需操作权限'
  failure: 无权限 401/403
- level: BUSINESS
  field: state
  rule: 仅 AVAILABLE 状态可删除
  failure: 62110005 SPACETCI_LESSONSTRATEGY_STRATEGY_STATE_NOT_AVAILABL
- level: BUSINESS
  field: 策略-课程镜像关联
  rule: 被课程镜像使用的策略不可删除
  failure: 62110009 SPACETCI_LESSONSTRATEGY_STRATEGY_USED_BY_CLASSROOM
- level: DATA_PERMISSION
  field: 策略 id
  rule: 非全权限管理员仅可删除授权策略
  failure: checkPermission 抛权限异常，该条任务失败
assertions:
  success:
  - scenario: 策略未被课程镜像使用
    expect: $.content.taskId 非空
  - scenario: 多条 id 部分失败
    expect: 轮询 content.taskId 至终态 batchTaskItemStatus∈["FAILURE"]
  failure:
  - scenario: 策略已被课程镜像绑定
    trigger: t_space_tci_lesson_image 关联该策略
    expect: 轮询 content.taskId 至终态 batchTaskItemStatus∈["FAILURE"]，任务项提示 62110009
  - scenario: 策略状态非 AVAILABLE
    trigger: 策略处于 DELETING
    expect: 轮询 content.taskId 至终态 batchTaskItemStatus∈["FAILURE"]，任务项提示 62110005
cleanup:
- api: 无
  note: 无对应 HTTP 清理接口（删除状态机为内部调用，非 HTTP 端点）
prereq_state:
  resource: strategy
  required_state: AVAILABLE
  achieve_via: []

idempotency:
  level: non_idempotent
  note: 删除任务流各 processor 均做幂等处理；重复提交已删 id 无副作用
params:
  required:
  - name: strategy_name
    desc: ''
    used_by: 见 setup/request
---
# POST /space/strategy/tci/delete

> 批量删除 TCI 课程策略。框架 defaultBatchDelete 为 idArr 中每个 id 注册批量删除任务；每条 processItem 先做数据权限校验（checkAdminDataPermission），再调 loadAPI().deleteById → SpaceStrategyGroupTCIValidation.validateBeforeDelete：策略状态必须 AVAILABLE(62110005)，且未被课程镜像关联使用（被使用抛 62110009 SPACETCI_LESSONSTRATEGY_STRATEGY_USED_BY_CLASSROOM）；通过后执行 DeleteSpaceTCIStrategyGroupTaskHandle 状态机（置 DELETING→删平台策略组→删平台关联→删数据权限→删本地主数据+失效缓存）。 ｜ @EnableAuthority ｜ 异步批量任务：批量注册删除任务，逐条校验+删除状态机（不可撤销）

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /space/strategy/tci/list"]
    end
    B["POST /space/strategy/tci/delete<br>批量删除 TCI 课程策略。框架 defaultBatchDelete 为 id<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(webRequest) 与 Assert.notN"]
        C2["Step2: super.defaultBatchDelete(webRequest, bui"]
        C3["Step3: 框架 handler 逐条调用 loadAPI().deleteById(id)"]
        C4["Step4: deleteById → validateBeforeDelete：validS"]
        C5["Step5: 执行 DeleteSpaceTCIStrategyGroupTaskHandle"]
        C6["Step6: 返回 DefaultWebResponse.success(批量任务提交结果)"]
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
| URL | /space/strategy/tci/delete |
| Controller | SpaceDeskStrategyGroupTCIController |
| 方法名 | batchDelete |
| 权限注解 | @EnableAuthority |
| 执行方式 | 异步批量任务：批量注册删除任务，逐条校验+删除状态机（不可撤销） |
| 业务含义 | 批量删除 TCI 课程策略。框架 defaultBatchDelete 为 idArr 中每个 id 注册批量删除任务；每条 processItem 先做数据权限校验（checkAdminDataPermission），再调 loadAPI().deleteById → SpaceStrategyGroupTCIValidation.validateBeforeDelete：策略状态必须 AVAILABLE(62110005)，且未被课程镜像关联使用（被使用抛 62110009 SPACETCI_LESSONSTRATEGY_STRATEGY_USED_BY_CLASSROOM）；通过后执行 DeleteSpaceTCIStrategyGroupTaskHandle 状态机（置 DELETING→删平台策略组→删平台关联→删数据权限→删本地主数据+失效缓存）。 |

## 入参详情

### IdArrWebRequest（框架类）

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| idArr | UUID[] | 是 | 非空（Assert.notNull(webRequest)） | 待删除 TCI 课程策略 id 数组 |

## 出参详情

| 返回类型 | DefaultWebResponse<BatchTaskSubmitResult> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| taskId | String | 批量任务 id |
| result | String | 任务提交结果/状态 |

## 上游前置业务

### 前置1：POST /space/strategy/tci/list

TCI课程策略ID数组，来源为策略列表（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：SK 框架默认批量删除 handler（AbstractCrudControllerTemplate.defaultBatchDelete 内部实现）+ DeleteSpaceTCIStrategyGroupTaskHandle

| 步骤 | 说明 |
|---|---|
| 1 | 取 DefaultBatchTaskItem.itemId（策略 id） |
| 2 | checkAdminDataPermission(id)：非全权限管理员校验数据权限 |
| 3 | loadAPI().deleteById(id) → validateBeforeDelete（状态 62110005 / 被使用 62110009） |
| 4 | DeleteSpaceTCIStrategyGroupTaskHandle 状态机 5 步（置 DELETING→删平台→删关联→删权限→删本地+失效缓存） |

### 处理流程

1. Assert.notNull(webRequest) 与 Assert.notNull(builder)
2. super.defaultBatchDelete(webRequest, builder)：逐条构建 DefaultBatchTaskItem 注册批量删除任务
3. 框架 handler 逐条调用 loadAPI().deleteById(id)（先 checkAdminDataPermission 数据权限校验）
4. deleteById → validateBeforeDelete：validState（非 AVAILABLE 抛 62110005）、validUsedWhenDelete（关联课程镜像抛 62110009）
5. 执行 DeleteSpaceTCIStrategyGroupTaskHandle 状态机：DeleteInitStrategyGroupProcessor（置 DELETING）→ DeletePlatformStrategyGroupProcessor（删平台策略组，幂等）→ DeletePlatformStrategyGroupRelatedProcessor（删平台-课程关联，幂等）→ RemoveStrategyGroupDataPermissionProcessor（删数据权限）→ DeleteLocalStrategyGroupProcessor（删本地主数据+失效缓存）
6. 返回 DefaultWebResponse.success(批量任务提交结果)

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）

> 📖 错误码/状态码对照表见 **code_map_all.md**（工程级全量）与 **error_code_map_tci_strategy.md**（TCI 接口级，含触发条件）。

## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| AUTH | 接口 | @EnableAuthority 需操作权限 | 无权限 401/403 |
| BUSINESS | state | 仅 AVAILABLE 状态可删除 | 62110005 SPACETCI_LESSONSTRATEGY_STRATEGY_STATE_NOT_AVAILABLE |
| BUSINESS | 策略-课程镜像关联 | 被课程镜像使用的策略不可删除 | 62110009 SPACETCI_LESSONSTRATEGY_STRATEGY_USED_BY_CLASSROOM |
| DATA_PERMISSION | 策略 id | 非全权限管理员仅可删除授权策略 | checkPermission 抛权限异常，该条任务失败 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| idArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 策略未被课程镜像使用 | $.content.taskId 非空 |
| 多条 id 部分失败 | 轮询 content.taskId 至终态 batchTaskItemStatus∈["FAILURE"] |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 策略已被课程镜像绑定 | t_space_tci_lesson_image 关联该策略 | 轮询 content.taskId 至终态 batchTaskItemStatus∈["FAILURE"]，任务项提示 62110009 |
| 策略状态非 AVAILABLE | 策略处于 DELETING | 轮询 content.taskId 至终态 batchTaskItemStatus∈["FAILURE"]，任务项提示 62110005 |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 内部调用 / PlatformSubSysResRelationAPI#deleteById / PlatformAdminDataPermissionAPI#deleteByPermissionDataId / repository.deleteById | 删除状态机为不可撤销任务，失败时由框架永久重试直到成功或人工介入 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 删除任务流各 processor 均做幂等处理；重复提交已删 id 无副作用 |
