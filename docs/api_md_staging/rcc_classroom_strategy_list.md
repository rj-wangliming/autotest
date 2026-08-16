---
version: '2.0'
api:
  url: /rcc/classroom/strategy/list
  method: POST
  name: '分页获取教室策略列表。调 classroomStrategyAPI.getClassroomStrategyList(pageQueryRequest) 返回 '
  controller: RccClassroomStrategyController
  method_ref: getPageDeskStrategy
  permission: 无
  exec_mode: 同步分页查询（PageQuery）
  async: false
  description: 分页获取教室策略列表。调 classroomStrategyAPI.getClassroomStrategyList(pageQueryRequest) 返回 PageQueryResponse<ViewClassroomStrategyDTO>。
params:
  required:
  - name: classroom_strategy_name
    desc: ''
    used_by: 见 setup/request
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: createStrategy
  api: POST /rcc/classroom/strategy/create
  purpose: 造策略数据以便列表有数据
  request:
    body:
      classroomStrategyName:
        value: ${param.classroom_strategy_name}
      linkShutdown:
        value: false
      startPolicy:
        value: START_ONLINE
      defaultEnterImageSwitch:
        value: false
      defaultDisplayDeskType:
        value: CLASSROOM_MODE
      reservedStoragePolicy:
        value: SYSTEM_DEFAULT
  extract:
    classroomStrategyName: auto_strategy_<ts>
  idempotent: reuse
  reuse_query:
    api: POST /rcc/classroom/strategy/list
    body:
      matchArr:
      - type: EXACT
        fieldName: classroomStrategyName
        valueArr:
        - ${param.classroom_strategy_name}
        matchRule: EQ
    extract:
      classroomStrategyId: $.content.itemArr[0].classroomStrategyId
request:
  dto: PageQueryRequest（sk.pagekit 框架接口）
  body:
    page:
      type: Integer
      required: false
      constraint: '@Range(min=0)'
      description: 页码
    limit:
      type: Integer
      required: false
      constraint: '@Range(min=1, max=2000)'
      description: 每页条数
    searchKeyword:
      type: String
      required: false
      constraint: '@Nullable'
      description: 搜索关键字
    matchArr:
      type: Match[]
      required: false
      constraint: '@NotNull'
      description: '查询条件数组（元素格式：{type: EXACT, fieldName, valueArr: [值], matchRule: EQ}，精确匹配用 valueArr 数组 + matchRule；模糊用 type: FUZZY + value 单值）'
      value:
      - type: EXACT
        fieldName: classroomStrategyName
        valueArr:
        - ${param.classroom_strategy_name}
        matchRule: EQ
    sortArr:
      type: Sort[]
      required: false
      constraint: '@NotNull'
      description: '排序条件数组（真实请求默认 sortArr=[{fieldName: createTime, direction: DESC}]）'
      value:
      - fieldName: createTime
        direction: DESC
    exactMatchArr:
      type: ExactMatch[]
      required: false
      constraint: '@Nullable（旧格式，name+valueArr）'
      description: 精确匹配条件数组（真实请求默认空数组）
    customData:
      type: String
      required: false
      constraint: '@Nullable'
      description: 自定义扩展数据
    needForceRefresh:
      type: Boolean
      required: false
      constraint: '@Nullable，默认 true（样例值）'
      description: 是否强制刷新
    isAutomaticRefresh:
      type: Boolean
      required: false
      constraint: '@Nullable，默认 false（样例值）'
      description: 是否自动刷新
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    total:
      type: Integer
      description: 总记录数
    itemArr:
      type: ViewClassroomStrategyDTO[]
      description: 策略列表项：classroomStrategyId, classroomStrategyName, classroomS
upstream:
- api: 内部调用:rcc/ClassroomStrategyAPI
  purpose: 分页查询教室策略列表
downstream:
- api: POST /rcc/classroom/create
  purpose: 被教室创建 POST /rcc/classroom/create 消费
constraints:
- level: PARAM
  field: page
  rule: '@Range(min=0)'
  failure: 负数校验失败
- level: PARAM
  field: limit
  rule: '@Range(min=1, max=2000)'
  failure: 越界校验失败
assertions:
  success:
  - scenario: 分页查询
    expect: $.content.itemArr 非空
  failure:
  - scenario: limit 超限
    trigger: limit>2000
    expect: $.status==ERROR
cleanup: []
idempotency:
  level: non_idempotent
  note: 纯查询接口，无副作用
---
# POST /rcc/classroom/strategy/list

> 分页获取教室策略列表。调 classroomStrategyAPI.getClassroomStrategyList(pageQueryRequest) 返回 PageQueryResponse<ViewClassroomStrategyDTO>。 ｜ 无特殊权限 ｜ 同步分页查询（PageQuery）

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/strategy/list<br>分页获取教室策略列表。调 classroomStrategyAPI.getCla<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request/sessionContext)"]
        C2["Step2: classroomStrategyAPI.getClassroomStrateg"]
        C3["Step3: return CommonWebResponse.success(pageQue"]
        C1 --> C2
        C2 --> C3
    end
    B --> C1
    subgraph 下游消费方
        D1["/rcc/classroom/create"]
    end
    B -->|数据| D1
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rcc/classroom/strategy/list |
| Controller | RccClassroomStrategyController |
| 方法名 | getPageDeskStrategy |
| 权限注解 | 无 |
| 执行方式 | 同步分页查询（PageQuery） |
| 业务含义 | 分页获取教室策略列表。调 classroomStrategyAPI.getClassroomStrategyList(pageQueryRequest) 返回 PageQueryResponse<ViewClassroomStrategyDTO>。 |

## 入参详情

### PageQueryRequest（sk.pagekit 框架接口）

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| page | Integer | 否 | @Range(min=0) | 页码 |
| limit | Integer | 否 | @Range(min=1, max=2000) | 每页条数 |
| matchArr | Match[] | 否 | @NotNull | 查询条件数组 |
| sortArr | Sort[] | 否 | @NotNull | 排序条件数组 |
| customData | String | 否 | @Nullable | 自定义扩展数据 |

## 出参详情

| 返回类型 | CommonWebResponse（data=PageQueryResponse<ViewClassroomStrategyDTO>） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr | ViewClassroomStrategyDTO[] | 策略列表项：classroomStrategyId, classroomStrategyName, classroomStrategyDesc, linkShutdown, startPolicy, defaultEnterImageSeconds, defaultEnterImageSwitch, defaultDisplayDeskType, creatorUserName, classroomStrategyState, version, createTime, updateTime, refClassroomNum |
| total | Integer | 总记录数 |

## 上游前置业务

（无上游数据依赖）
## 内部处理流程

### 处理流程

1. Assert.notNull(request/sessionContext)
2. classroomStrategyAPI.getClassroomStrategyList(request) 分页查询
3. return CommonWebResponse.success(pageQueryResponse)

## 下游消费方

### 消费1：/rcc/classroom/create

消费方（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | page | @Range(min=0) | 负数校验失败 |
| PARAM | limit | @Range(min=1, max=2000) | 越界校验失败 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| page | user_input/from_query | 按业务构造 |
| limit | user_input/from_query | 按业务构造 |
| matchArr | user_input/from_query | 按业务构造 |
| sortArr | user_input/from_query | 按业务构造 |
| customData | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 分页查询 | $.content.itemArr 非空 |
### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| limit 超限 | limit>2000 | $.status==ERROR |
## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 纯查询接口，无副作用 |
