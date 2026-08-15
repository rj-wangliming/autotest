---
version: '2.0'
api:
  url: /rcc/classroom/strategy/create
  method: POST
  name: 创建教室策略：注入 creatorUserName 后调 classroomStrategyAPI.createClassroomStrategy（内部执行 C
  controller: RccClassroomStrategyController
  method_ref: createClassroomStrategy
  permission: 无
  exec_mode: 同步
  async: false
  description: 创建教室策略：注入 creatorUserName 后调 classroomStrategyAPI.createClassroomStrategy（内部执行 ClassroomStrategyRequest.validate 校验），成功记录创建审计日志并返回成功消息；失败记录失败审计日志并返回失败响应。
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: createStrategy
  api: POST /rcc/classroom/strategy/create
  purpose: 被测接口本身（造策略数据）
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
  dto: CreateClassroomStrategyRequest（继承 ClassroomStrategyRequest）
  body:
    classroomStrategyName:
      type: String
      required: true
      constraint: '@NotBlank @Size(min=1, max=32)，且匹配名称规格正则'
      description: 教室策略名称
      value: ${param.classroom_strategy_name}
    classroomStrategyDesc:
      type: String
      required: false
      constraint: '@Nullable @Size(max=128)'
      description: 教室策略描述
    linkShutdown:
      type: Boolean
      required: true
      constraint: '@NotNull'
      description: 终端联动关机开关
      value: false
    startPolicy:
      type: DesktopStartPolicyEnum
      required: true
      constraint: '@NotNull'
      description: 上课云桌面启动策略（可选值：START_ALL=启动所有云桌面 / START_ONLINE=仅启动终端连接的云桌面）
      value: START_ONLINE
    defaultEnterImageSwitch:
      type: Boolean
      required: true
      constraint: '@NotNull'
      description: 默认进入指定云桌面开关
      value: false
    defaultEnterImageSeconds:
      type: Integer
      required: false
      constraint: '@Nullable @Range(min=1, max=60)；开关开启时逻辑必填'
      description: 默认进入指定云桌面倒计时（秒）
    defaultDisplayDeskType:
      type: DefaultDisplayDeskType
      required: true
      constraint: '@NotNull'
      description: 默认展示桌面类型（可选值：CLASSROOM_MODE=默认课程镜像桌面 / LOCAL_DESK_MODE=公共本地镜像 / PERSONAL_VDI_DESK_MODE=个人云桌面）
      value: CLASSROOM_MODE
    reservedStoragePolicy:
      type: ReservedSpaceType
      required: true
      constraint: '@NotNull'
      description: 预留空间类型（可选值：SYSTEM_DEFAULT=系统默认 / USER_DEFINED=用户自定义，USER_DEFINED 时 reservedStorageSize 必填）
      value: SYSTEM_DEFAULT
    reservedStorageSize:
      type: Integer
      required: false
      constraint: '@Nullable @Range(min=1, max=1024)；预留策略为 USER_DEFINED 时逻辑必填'
      description: 磁盘预留空间大小（GB）
    creatorUserName:
      type: String
      required: false
      constraint: '@Nullable；服务端从 sessionContext.getUserName() 注入'
      description: 创建者登录名
    createTime:
      type: Date
      required: false
      constraint: '@Nullable；构造时默认 new Date()'
      description: 创建时间
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    content:
      type: 'null'
      description: 纯操作接口：content 为空（成功响应仅 status/message，msgKey=RCDC_RCC_CLASSROOM_STRATEGY_CREATE_OPERATE_LOG）（源码：Builder.success(msgKey,args)，content 为空）
upstream:
- api: 内部调用:rcc/ClassroomStrategyAPI
  purpose: 创建教室策略（内部执行 validate()）
- api: 内部调用:audit/BaseAuditLogAPI
  purpose: 记录创建策略成功/失败审计日志
downstream:
- api: /rcc/classroom/create（CreateClassroomWebRequest）消费
  purpose: 策略ID被教室创建 POST /rcc/classroom/create（CreateClassroomWebReque
constraints:
- level: PARAM
  field: classroomStrategyName
  rule: '@NotBlank @Size(1-32) + 名称规格正则（^[0-9a-zA-Z\u4e00-\u9fa5\.\-@'
  failure: 不匹配抛 RCDC_RCC_CLASSROOM_STRATEGY_NAME_NOT_MATCHES_SPECIFICAT
- level: PARAM
  field: linkShutdown
  rule: '@NotNull'
  failure: 缺失校验失败
- level: PARAM
  field: startPolicy
  rule: '@NotNull'
  failure: 缺失校验失败
- level: PARAM
  field: defaultEnterImageSwitch
  rule: '@NotNull'
  failure: 缺失校验失败
- level: PARAM
  field: defaultDisplayDeskType
  rule: '@NotNull'
  failure: 缺失校验失败
- level: PARAM
  field: reservedStoragePolicy
  rule: '@NotNull'
  failure: 缺失校验失败
- level: BUSINESS
  field: defaultEnterImageSeconds
  rule: defaultEnterImageSwitch=true 时必须填写
  failure: 抛 RCDC_RCC_CLASSROOM_STRATEGY_DEFAULT_ENTER_IMAGE_SECONDS_IS
- level: BUSINESS
  field: reservedStorageSize
  rule: reservedStoragePolicy=USER_DEFINED 时必须填写
  failure: 抛 RCDC_RCC_CLASSROOM_STRATEGY_RESERVED_STORAGE_SIZE_IS_NULL
- level: BUSINESS
  field: classroomStrategyName
  rule: 名称唯一
  failure: 抛 RCDC_RCC_CLASSROOM_STRATEGY_NAME_DUPLICATE
assertions:
  success:
  - scenario: 参数合法且名称唯一
    expect: $.status==SUCCESS
  failure:
  - scenario: 名称重复
    trigger: classroomStrategyName 已存在
    expect: $.status==ERROR 且 $.msgKey==RCDC_RCC_CLASSROOM_STRATEGY_CREATE_OPERATE_FAIL_LOG
  - scenario: 默认进入桌面开关开启但倒计时为空
    trigger: defaultEnterImageSwitch=true，defaultEnterImageSeconds 缺省
    expect: $.status==ERROR 且 $.msgKey==RCDC_RCC_CLASSROOM_STRATEGY_CREATE_OPERATE_FAIL_LOG（msgArgArr[1] 为倒计时为空文案）
cleanup:
- api: POST /rcc/classroom/strategy/delete
  purpose: 删除创建的教室策略（需先取 strategyId）
  depends_on: content.strategyId
idempotency:
  level: data_level
  note: 名称唯一约束兜底，重复提交同名会失败；无显式幂等键
---
# POST /rcc/classroom/strategy/create

> 创建教室策略：注入 creatorUserName 后调 classroomStrategyAPI.createClassroomStrategy（内部执行 ClassroomStrategyRequest.validate 校验），成功记录创建审计日志并返回成功消息；失败记录失败审计日志并返回失败响应。 ｜ 无特殊权限 ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/strategy/create<br>创建教室策略：注入 creatorUserName 后调 classroomSt<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request/sessionContext)"]
        C2["Step2: request.setCreatorUserName(sessionContex"]
        C3["Step3: classroomStrategyAPI.createClassroomStra"]
        C4["Step4: 成功：auditLogAPI.recordLog(RCDC_RCC_CLASSR"]
        C5["Step5: 返回 success(RCDC_RCC_CLASSROOM_STRATEGY_C"]
        C6["Step6: 失败：LOGGER.error 记录，auditLogAPI.recordLog"]
        C1 --> C2
        C7["Step7: 返回 fail(CREATE_OPERATE_FAIL_LOG, [策略名, e"]
        C6 --> C7
        C2 --> C3
        C3 --> C4
        C4 --> C5
        C5 --> C6
    end
    B --> C1
    subgraph 下游消费方
        D1["/rcc/classroom/create（CreateClassroomWebRequest）消费"]
    end
    B -->|数据| D1
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rcc/classroom/strategy/create |
| Controller | RccClassroomStrategyController |
| 方法名 | createClassroomStrategy |
| 权限注解 | 无 |
| 执行方式 | 同步 |
| 业务含义 | 创建教室策略：注入 creatorUserName 后调 classroomStrategyAPI.createClassroomStrategy（内部执行 ClassroomStrategyRequest.validate 校验），成功记录创建审计日志并返回成功消息；失败记录失败审计日志并返回失败响应。 |

## 入参详情

### CreateClassroomStrategyRequest（继承 ClassroomStrategyRequest）

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomStrategyName | String | 是 | @NotBlank @Size(min=1, max=32)，且匹配名称规格正则 | 教室策略名称 |
| classroomStrategyDesc | String | 否 | @Nullable @Size(max=128) | 教室策略描述 |
| linkShutdown | Boolean | 是 | @NotNull | 终端联动关机开关（默认 false） |
| startPolicy | DesktopStartPolicyEnum | 是 | @NotNull | 上课云桌面启动策略（START_ALL=启动所有云桌面 / START_ONLINE=仅启动终端连接的云桌面） |
| defaultEnterImageSwitch | Boolean | 是 | @NotNull | 默认进入指定云桌面开关（默认 false） |
| defaultEnterImageSeconds | Integer | 否 | @Nullable @Range(min=1, max=60)；开关开启时逻辑必填 | 默认进入指定云桌面倒计时（秒） |
| defaultDisplayDeskType | DefaultDisplayDeskType | 是 | @NotNull | 默认展示桌面类型（CLASSROOM_MODE=默认课程镜像桌面 / LOCAL_DESK_MODE=公共本地镜像 / PERSONAL_VDI_DESK_MODE=个人云桌面） |
| reservedStoragePolicy | ReservedSpaceType | 是 | @NotNull | 预留空间类型（SYSTEM_DEFAULT=系统默认 / USER_DEFINED=用户自定义，USER_DEFINED 时 reservedStorageSize 必填） |
| reservedStorageSize | Integer | 否 | @Nullable @Range(min=1, max=1024)；预留策略为 USER_DEFINED 时逻辑必填 | 磁盘预留空间大小（GB） |
| creatorUserName | String | 否 | @Nullable；服务端从 sessionContext.getUserName() 注入 | 创建者登录名 |
| createTime | Date | 否 | @Nullable；构造时默认 new Date() | 创建时间 |

## 出参详情

| 返回类型 | DefaultWebResponse（data=成功key，msg=RCDC_RCC_CLASSROOM_STRATEGY_CREATE_OPERATE_LOG + 策略名） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| content | null | 纯操作接口：content 为空（成功响应仅 status/message，msgKey=RCDC_RCC_CLASSROOM_STRATEGY_CREATE_OPERATE_LOG） |

## 上游前置业务

（无上游数据依赖）
## 内部处理流程

### 处理流程

1. Assert.notNull(request/sessionContext)
2. request.setCreatorUserName(sessionContext.getUserName())
3. classroomStrategyAPI.createClassroomStrategy(request)（内部 validate：defaultEnterImageSwitch 开启时 seconds 必填、reservedStoragePolicy=USER_DEFINED 时 size 必填、名称规格校验）
4. 成功：auditLogAPI.recordLog(RCDC_RCC_CLASSROOM_STRATEGY_CREATE_OPERATE_LOG, 策略名)
5. 返回 success(RCDC_RCC_CLASSROOM_STRATEGY_CREATE_OPERATE_LOG, [策略名])
6. 失败：LOGGER.error 记录，auditLogAPI.recordLog(CREATE_OPERATE_FAIL_LOG, 策略名, e.getI18nMessage())
7. 返回 fail(CREATE_OPERATE_FAIL_LOG, [策略名, e.getI18nMessage()])

## 下游消费方

### 消费1：/rcc/classroom/create（CreateClassroomWebRequest）消费

消费方（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | classroomStrategyName | @NotBlank @Size(1-32) + 名称规格正则（^[0-9a-zA-Z\u4e00-\u9fa5\.\-@]...） | 不匹配抛 RCDC_RCC_CLASSROOM_STRATEGY_NAME_NOT_MATCHES_SPECIFICATION |
| PARAM | linkShutdown | @NotNull | 缺失校验失败 |
| PARAM | startPolicy | @NotNull | 缺失校验失败 |
| PARAM | defaultEnterImageSwitch | @NotNull | 缺失校验失败 |
| PARAM | defaultDisplayDeskType | @NotNull | 缺失校验失败 |
| PARAM | reservedStoragePolicy | @NotNull | 缺失校验失败 |
| BUSINESS | defaultEnterImageSeconds | defaultEnterImageSwitch=true 时必须填写 | 抛 RCDC_RCC_CLASSROOM_STRATEGY_DEFAULT_ENTER_IMAGE_SECONDS_IS_NULL |
| BUSINESS | reservedStorageSize | reservedStoragePolicy=USER_DEFINED 时必须填写 | 抛 RCDC_RCC_CLASSROOM_STRATEGY_RESERVED_STORAGE_SIZE_IS_NULL |
| BUSINESS | classroomStrategyName | 名称唯一 | 抛 RCDC_RCC_CLASSROOM_STRATEGY_NAME_DUPLICATE |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomStrategyName | user_input/from_query | 按业务构造 |
| classroomStrategyDesc | user_input/from_query | 按业务构造 |
| linkShutdown | user_input/from_query | 按业务构造 |
| startPolicy | user_input/from_query | 按业务构造 |
| defaultEnterImageSwitch | user_input/from_query | 按业务构造 |
| defaultEnterImageSeconds | user_input/from_query | 按业务构造 |
| defaultDisplayDeskType | user_input/from_query | 按业务构造 |
| reservedStoragePolicy | user_input/from_query | 按业务构造 |
| reservedStorageSize | user_input/from_query | 按业务构造 |
| creatorUserName | user_input/from_query | 按业务构造 |
| createTime | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 参数合法且名称唯一 | $.status==SUCCESS |
### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 名称重复 | classroomStrategyName 已存在 | $.status==ERROR 且 $.msgKey==RCDC_RCC_CLASSROOM_STRATEGY_CREATE_OPERATE_FAIL_LOG |
| 默认进入桌面开关开启但倒计时为空 | defaultEnterImageSwitch=true，defaultEnterImageSeconds 缺省 | $.status==ERROR 且 $.msgKey==RCDC_RCC_CLASSROOM_STRATEGY_CREATE_OPERATE_FAIL_LOG（msgArgArr[1] 为倒计时为空文案） |
## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | MEDIUM |
| 说明 | 名称唯一约束兜底，重复提交同名会失败；无显式幂等键 |
