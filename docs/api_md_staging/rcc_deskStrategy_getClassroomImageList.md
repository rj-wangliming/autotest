---
version: '2.0'
api:
  url: /rcc/deskStrategy/getClassroomImageList
  method: POST
  name: 分页获取课程云桌面策略关联的教室镜像列表。Controller 直接调用 classroomImageAPI.pageClassroomImageQuery(p
  controller: RccDeskStrategyController
  method_ref: getClassroomImageList
  permission: 无
  exec_mode: 同步查询：DMQL 视图分页查询教室镜像列表（按管理员数据权限过滤）
  async: false
  description: 分页获取课程云桌面策略关联的教室镜像列表。Controller 直接调用 classroomImageAPI.pageClassroomImageQuery(pageQueryRequest, sessionContext.getUserId())，由 ClassroomImageAPIImpl 对请求追加数据权限过滤（管理员只能看到有权限的教室镜像）后经 ViewRccClassroomImag
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
request:
  dto: PageQueryRequest (com.ruijie.rcos.sk.pagekit.api.PageQueryRequest，框架类)
  body:
    page:
      type: Integer
      required: true
      constraint: 分页页码（0 基）
      description: pageQueryRequest.getPage()
    limit:
      type: Integer
      required: true
      constraint: 每页条数上限
      description: pageQueryRequest.getLimit()
    matchArr:
      type: Match[]
      required: false
      constraint: 精确匹配条件（字段=值）
      description: 框架 DMQL 视图过滤条件
    sortArr:
      type: Sort[]
      required: false
      constraint: 排序条件数组
      description: 框架透传
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    itemArr:
      type: ViewRccClassroomImageDTO[]
      description: 教室镜像列表
    total:
      type: long
      description: 总条数
    id:
      type: UUID
      description: 教室镜像记录 id
    classroomId:
      type: UUID
      description: 关联教室 id
    classroomName:
      type: String
      description: 关联教室名称
    imageId:
      type: UUID
      description: 镜像模板 id
    rootImageName:
      type: String
      description: 镜像根名称
    imageTemplateName:
      type: String
      description: 镜像模板名称
    teacherImage:
      type: Boolean
      description: 是否教师机镜像
    hide:
      type: Boolean
      description: 是否隐藏
    deskStrategyId:
      type: UUID
      description: 关联的课程策略 id
    deskStrategyName:
      type: String
      description: 关联的课程策略名称
    networkId:
      type: UUID
      description: 关联网络策略 id
    version:
      type: Integer
      description: 乐观锁版本号
upstream:
- api: POST /rcc/space/image/list
  produces: $.content.itemArr[*].id
  purpose: 镜像模板ID筛选（可空）
downstream:
- api: POST /rcc/deskStrategy/getClusterSupportEnablePersonalConfig
  purpose: 前端获取教室镜像后携带策略id/集群id计算是否支持浮动个性盘
- api: POST /rcc/classroom/image/teacher/strategy/edit
  purpose: 教室镜像关联策略编辑依赖本接口的教室镜像上下文
constraints:
- level: PARAM
  field: page/limit
  rule: 分页参数非空
  failure: Assert.notNull 校验失败（400）
- level: AUTH
  field: sessionContext
  rule: 需登录携带 SessionContext
  failure: sessionContext 为空断言异常
assertions:
  success:
  - scenario: 存在教室镜像数据
    expect: 返回 200，itemArr 为符合权限的教室镜像分页列表
  - scenario: 无任何教室镜像
    expect: 返回 200，itemArr 空数组，total=0
  failure:
  - scenario: pageQueryRequest 为 null
    trigger: 请求体缺失
    expect: Assert.notNull 抛异常（400）
cleanup:
- api: 无
  note: 只读查询接口，无需清理
idempotency:
  level: non_idempotent
  note: 只读分页查询，无副作用
---
# POST /rcc/deskStrategy/getClassroomImageList

> 分页获取课程云桌面策略关联的教室镜像列表。Controller 直接调用 classroomImageAPI.pageClassroomImageQuery(pageQueryRequest, sessionContext.getUserId())，由 ClassroomImageAPIImpl 对请求追加数据权限过滤（管理员只能看到有权限的教室镜像）后经 ViewRccClassroomImageDTO 视图分页查询返回；用于课程策略配置页选择关联教室镜像。 ｜ 无特殊权限 ｜ 同步查询：DMQL 视图分页查询教室镜像列表（按管理员数据权限过滤）

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/space/image/list"]
    end
    B["POST /rcc/deskStrategy/getClassroomImageList<br>分页获取课程云桌面策略关联的教室镜像列表。Controller 直接调用 cla<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(pageQueryRequest) 与 Asser"]
        C2["Step2: 调用 classroomImageAPI.pageClassroomImageQ"]
        C3["Step3: ClassroomImageAPIImpl 内部追加数据权限过滤后执行 DMQL"]
        C4["Step4: 返回 CommonWebResponse.success(分页结果)"]
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
| URL | /rcc/deskStrategy/getClassroomImageList |
| Controller | RccDeskStrategyController |
| 方法名 | getClassroomImageList |
| 权限注解 | 无 |
| 执行方式 | 同步查询：DMQL 视图分页查询教室镜像列表（按管理员数据权限过滤） |
| 业务含义 | 分页获取课程云桌面策略关联的教室镜像列表。Controller 直接调用 classroomImageAPI.pageClassroomImageQuery(pageQueryRequest, sessionContext.getUserId())，由 ClassroomImageAPIImpl 对请求追加数据权限过滤（管理员只能看到有权限的教室镜像）后经 ViewRccClassroomImageDTO 视图分页查询返回；用于课程策略配置页选择关联教室镜像。 |

## 入参详情

### PageQueryRequest (com.ruijie.rcos.sk.pagekit.api.PageQueryRequest，框架类)

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| page | Integer | 是 | 分页页码（0 基） | pageQueryRequest.getPage() |
| limit | Integer | 是 | 每页条数上限 | pageQueryRequest.getLimit() |
| matchArr | Match[] | 否 | 精确匹配条件（字段=值） | 框架 DMQL 视图过滤条件 |
| sortArr | Sort[] | 否 | 排序条件数组 | 框架透传 |

## 出参详情

| 返回类型 | CommonWebResponse<PageQueryResponse<ViewRccClassroomImageDTO>> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr | ViewRccClassroomImageDTO[] | 教室镜像列表 |
| total | long | 总条数 |
| id | UUID | 教室镜像记录 id |
| classroomId | UUID | 关联教室 id |
| classroomName | String | 关联教室名称 |
| imageId | UUID | 镜像模板 id |
| rootImageName | String | 镜像根名称 |
| imageTemplateName | String | 镜像模板名称 |
| teacherImage | Boolean | 是否教师机镜像 |
| hide | Boolean | 是否隐藏 |
| deskStrategyId | UUID | 关联的课程策略 id |
| deskStrategyName | String | 关联的课程策略名称 |
| networkId | UUID | 关联网络策略 id |
| version | Integer | 乐观锁版本号 |

## 上游前置业务

### 前置1：POST /rcc/space/image/list

镜像模板ID筛选（可空）（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull(pageQueryRequest) 与 Assert.notNull(sessionContext)
2. 调用 classroomImageAPI.pageClassroomImageQuery(pageQueryRequest, sessionContext.getUserId())
3. ClassroomImageAPIImpl 内部追加数据权限过滤后执行 DMQL 视图分页查询
4. 返回 CommonWebResponse.success(分页结果)

## 下游消费方

### 消费1：POST /rcc/deskStrategy/getClassroomImageList

课堂镜像ID，被策略 condition/list（classroomImageId）、lessonImage 分配消费（推断字段名 id/imageId）（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | page/limit | 分页参数非空 | Assert.notNull 校验失败（400） |
| AUTH | sessionContext | 需登录携带 SessionContext | sessionContext 为空断言异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| page | user_input/from_query | 按业务构造 |
| limit | user_input/from_query | 按业务构造 |
| matchArr | user_input/from_query | 按业务构造 |
| sortArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 存在教室镜像数据 | 返回 200，itemArr 为符合权限的教室镜像分页列表 |
| 无任何教室镜像 | 返回 200，itemArr 空数组，total=0 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| pageQueryRequest 为 null | 请求体缺失 | Assert.notNull 抛异常（400） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 无 | 只读查询接口，无需清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 只读分页查询，无副作用 |
