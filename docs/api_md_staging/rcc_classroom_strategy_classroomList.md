---
version: '2.0'
api:
  url: /rcc/classroom/strategy/classroomList
  method: POST
  name: 查询教室策略关联的教室列表。将 PageWebRequest 包装为 PageSearchRequest；管理员拥有全部终端组权限时直接 findClassro
  controller: RccClassroomStrategyController
  method_ref: getClassroomList
  permission: 无
  exec_mode: 同步分页查询（PageSearch + 数据权限过滤）
  async: false
  description: 查询教室策略关联的教室列表。将 PageWebRequest 包装为 PageSearchRequest；管理员拥有全部终端组权限时直接 findClassroomList(空权限过滤)；否则查询可见终端组ID列表，无任何权限返回空页，有权限则作为权限过滤传入 findClassroomList。返回 DefaultPageResponse<ClassroomStrategyUsedByClass
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
  purpose: 创建教室策略以便关联教室数据
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
  dto: PageWebRequest（sk.webmvc 框架类）
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
    matchArr:
      type: Match[]
      required: false
      constraint: '@NotNull'
      description: 查询条件数组
    sortArr:
      type: Sort[]
      required: false
      constraint: '@NotNull'
      description: 排序条件数组
    customData:
      type: String
      required: false
      constraint: '@Nullable'
      description: 自定义扩展数据
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
      type: ClassroomStrategyUsedByClassro
      description: 教室列表项：classroomId, classroomName, teacherHasCited, studentHa
upstream:
- api: 内部调用:space-pa/SpaceDataPermissionUtils
  purpose: 判断管理员是否拥有全部终端组权限
- api: 内部调用:space-pa/PlatformAdminDataPermissionAPI
  purpose: 查询管理员可见终端组ID列表
- api: 内部调用:rcc/ClassroomStrategyAPI
  purpose: 分页查询策略关联教室列表
downstream:
- api: 内部调用:rcc/ClassroomStrategyAPI#findClassroomList
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: BUSINESS
  field: 数据权限
  rule: 非全权限管理员仅返回其可见终端组内教室
  failure: 无可见终端组时返回空列表（非错误）
assertions:
  success:
  - scenario: 全权限管理员查询
    expect: $.content.itemArr 非空
  - scenario: 非全权限管理员无可见终端组
    expect: $.content.itemArr 为空
  failure:
  - scenario: 系统异常
    trigger: 后端处理异常
    expect: status==ERROR（系统异常类 msgKey）
cleanup: []
idempotency:
  level: non_idempotent
  note: 纯查询接口，无副作用
---
# POST /rcc/classroom/strategy/classroomList

> 查询教室策略关联的教室列表。将 PageWebRequest 包装为 PageSearchRequest；管理员拥有全部终端组权限时直接 findClassroomList(空权限过滤)；否则查询可见终端组ID列表，无任何权限返回空页，有权限则作为权限过滤传入 findClassroomList。返回 DefaultPageResponse<ClassroomStrategyUsedByClassroomDTO>。 ｜ 无特殊权限 ｜ 同步分页查询（PageSearch + 数据权限过滤）

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/strategy/classroomList<br>查询教室策略关联的教室列表。将 PageWebRequest 包装为 PageS<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request/sessionContext)"]
        C2["Step2: new PageSearchRequest(request) 包装分页请求"]
        C3["Step3: spaceDataPermissionUtils.isAllGroupPermi"]
        C4["Step4: 否则 adminDataPermissionAPI.listTerminalGr"]
        C5["Step5: terminalGroupIdList 为空 → 返回空 PageQueryRe"]
        C6["Step6: 非空 → 返回 success(findClassroomList(pageRe"]
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
| URL | /rcc/classroom/strategy/classroomList |
| Controller | RccClassroomStrategyController |
| 方法名 | getClassroomList |
| 权限注解 | 无 |
| 执行方式 | 同步分页查询（PageSearch + 数据权限过滤） |
| 业务含义 | 查询教室策略关联的教室列表。将 PageWebRequest 包装为 PageSearchRequest；管理员拥有全部终端组权限时直接 findClassroomList(空权限过滤)；否则查询可见终端组ID列表，无任何权限返回空页，有权限则作为权限过滤传入 findClassroomList。返回 DefaultPageResponse<ClassroomStrategyUsedByClassroomDTO>。 |

## 入参详情

### PageWebRequest（sk.webmvc 框架类）

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| page | Integer | 否 | @Range(min=0) | 页码 |
| limit | Integer | 否 | @Range(min=1, max=2000) | 每页条数 |
| matchArr | Match[] | 否 | @NotNull | 查询条件数组 |
| sortArr | Sort[] | 否 | @NotNull | 排序条件数组 |
| customData | String | 否 | @Nullable | 自定义扩展数据 |

## 出参详情

| 返回类型 | DefaultWebResponse（data=DefaultPageResponse<ClassroomStrategyUsedByClassroomDTO>） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr | ClassroomStrategyUsedByClassroomDTO[] | 教室列表项：classroomId, classroomName, teacherHasCited, studentHasCited, studentClassroomStrategyId, teacherClassroomStrategyId |
| total | Integer | 总记录数 |

## 上游前置业务

（无上游数据依赖）
## 内部处理流程

### 处理流程

1. Assert.notNull(request/sessionContext)
2. new PageSearchRequest(request) 包装分页请求
3. spaceDataPermissionUtils.isAllGroupPermission(userId) 为 true → findClassroomList(pageRequest, new ArrayList<>()) 并返回
4. 否则 adminDataPermissionAPI.listTerminalGroupIdByAdminId(new ListTerminalGroupIdRequest(userId)) 查询可见终端组
5. terminalGroupIdList 为空 → 返回空 PageQueryResponse<ViewClassroomInfoEntity>
6. 非空 → 返回 success(findClassroomList(pageRequest, terminalGroupIdList))

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| BUSINESS | 数据权限 | 非全权限管理员仅返回其可见终端组内教室 | 无可见终端组时返回空列表（非错误） |

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
| 全权限管理员查询 | $.content.itemArr 非空 |
| 非全权限管理员无可见终端组 | $.content.itemArr 为空 |
### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 权限不足 | 无授权 | 403 |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 纯查询接口，无副作用 |
