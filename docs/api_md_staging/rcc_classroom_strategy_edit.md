---
version: '2.0'
api:
  url: /rcc/classroom/strategy/edit
  method: POST
  name: 编辑教室策略：调 classroomStrategyAPI.updateClassroomStrategy（内部执行 validate()），成功记录编辑审计日
  controller: RccClassroomStrategyController
  method_ref: editClassroomStrategy
  permission: 无
  exec_mode: 同步
  async: false
  description: 编辑教室策略：调 classroomStrategyAPI.updateClassroomStrategy（内部执行 validate()），成功记录编辑审计日志并返回成功消息；失败记录失败审计日志并返回失败响应。
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: createStrategy
  api: POST /rcc/classroom/strategy/create
  purpose: 造策略数据
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
- name: listStrategy
  api: POST /rcc/classroom/strategy/list
  purpose: 按策略名精确过滤（matchArr.fieldName=classroomStrategyName）
  extract:
    classroomStrategyId: $.content.itemArr[0].classroomStrategyId
  request:
    body:
      matchArr:
      - type: EXACT
        fieldName: classroomStrategyName
        valueArr:
        - ${param.classroom_strategy_name}
        matchRule: EQ
request:
  dto: UpdateClassroomStrategyRequest（继承 ClassroomStrategyRequest）
  body:
    id:
      type: UUID
      required: true
      constraint: '@NotNull'
      description: 教室策略ID
    classroomStrategyName:
      type: String
      required: true
      constraint: '@NotBlank @Size(min=1, max=32)，且匹配名称规格正则'
      description: 教室策略名称
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
    startPolicy:
      type: DesktopStartPolicyEnum
      required: true
      constraint: '@NotNull'
      description: 上课云桌面启动策略（可选值：START_ALL/START_ONLINE）
    defaultEnterImageSwitch:
      type: Boolean
      required: true
      constraint: '@NotNull'
      description: 默认进入指定云桌面开关
    defaultEnterImageSeconds:
      type: Integer
      required: false
      constraint: '@Nullable @Range(min=1, max=60)；开关开启时逻辑必填'
      description: 默认进入指定云桌面倒计时（秒）
    defaultDisplayDeskType:
      type: DefaultDisplayDeskType
      required: true
      constraint: '@NotNull'
      description: 默认展示桌面类型
    reservedStoragePolicy:
      type: ReservedSpaceType
      required: true
      constraint: '@NotNull'
      description: 预留空间类型
    reservedStorageSize:
      type: Integer
      required: false
      constraint: '@Nullable @Range(min=1, max=1024)；预留策略为 USER_DEFINED 时逻辑必填'
      description: 磁盘预留空间大小（GB）
    creatorUserName:
      type: String
      required: false
      constraint: '@Nullable'
      description: 创建者登录名（编辑时沿用）
    updateTime:
      type: Date
      required: false
      constraint: '@Nullable；构造时默认 new Date()'
      description: 更新时间
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
      description: 纯操作接口：content 为空（成功响应仅 status/message，msgKey=RCDC_RCC_CLASSROOM_STRATEGY_EDIT_OPERATE_LOG）（源码：Builder.success(msgKey,args)，content 为空）
upstream:
- api: 内部调用:rcc/ClassroomStrategyAPI
  purpose: 更新教室策略（内部执行 validate()）
- api: 内部调用:audit/BaseAuditLogAPI
  purpose: 记录编辑策略成功/失败审计日志
downstream:
- api: 内部调用:rcc/ClassroomStrategyAPI#updateClassroomStrategy
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: id
  rule: '@NotNull'
  failure: 缺失校验失败
- level: PARAM
  field: classroomStrategyName
  rule: '@NotBlank @Size(1-32) + 名称规格正则'
  failure: 不匹配抛 RCDC_RCC_CLASSROOM_STRATEGY_NAME_NOT_MATCHES_SPECIFICAT
- level: PARAM
  field: linkShutdown/startPolicy/defaultEnterIma
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
  field: id
  rule: 策略必须存在
  failure: 抛 RCDC_RCC_CLASSROOM_STRATEGY_NOT_FOUND
- level: BUSINESS
  field: classroomStrategyName
  rule: 名称唯一（排除自身）
  failure: 抛 RCDC_RCC_CLASSROOM_STRATEGY_NAME_DUPLICATE
assertions:
  success:
  - scenario: 参数合法且策略存在
    expect: $.status==SUCCESS
  failure:
  - scenario: 策略ID不存在
    trigger: id 无效
    expect: $.status==ERROR 且 $.msgKey==RCDC_RCC_CLASSROOM_STRATEGY_EDIT_OPERATE_FAIL_LOG
  - scenario: 名称与其他策略重复
    trigger: classroomStrategyName 被占用
    expect: $.status==ERROR 且 $.msgKey==RCDC_RCC_CLASSROOM_STRATEGY_EDIT_OPERATE_FAIL_LOG（msgArgArr[1] 为名称重复文案）
cleanup: []
prereq_state:
  resource: strategy
  required_state: AVAILABLE
  achieve_via: []

idempotency:
  level: data_level
  note: 按 id 整体更新策略，重复提交收敛于最终值；名称冲突时失败
params:
  required:
  - name: strategy_name
    desc: ''
    used_by: 见 setup/request
  - name: classroom_strategy_name
    desc: ''
    used_by: setup/request
---
# POST /rcc/classroom/strategy/edit

> 编辑教室策略：调 classroomStrategyAPI.updateClassroomStrategy（内部执行 validate()），成功记录编辑审计日志并返回成功消息；失败记录失败审计日志并返回失败响应。 ｜ 无特殊权限 ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/strategy/edit<br>编辑教室策略：调 classroomStrategyAPI.updateClas<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request/sessionContext)"]
        C2["Step2: classroomStrategyAPI.updateClassroomStra"]
        C3["Step3: 成功：auditLogAPI.recordLog(RCDC_RCC_CLASSR"]
        C4["Step4: 返回 success(EDIT_OPERATE_LOG, [策略名])"]
        C5["Step5: 失败：LOGGER.error 记录，auditLogAPI.recordLog"]
        C6["Step6: 返回 fail(EDIT_OPERATE_FAIL_LOG, [策略名, e.g"]
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
| URL | /rcc/classroom/strategy/edit |
| Controller | RccClassroomStrategyController |
| 方法名 | editClassroomStrategy |
| 权限注解 | 无 |
| 执行方式 | 同步 |
| 业务含义 | 编辑教室策略：调 classroomStrategyAPI.updateClassroomStrategy（内部执行 validate()），成功记录编辑审计日志并返回成功消息；失败记录失败审计日志并返回失败响应。 |

## 入参详情

### UpdateClassroomStrategyRequest（继承 ClassroomStrategyRequest）

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| id | UUID | 是 | @NotNull | 教室策略ID |
| classroomStrategyName | String | 是 | @NotBlank @Size(min=1, max=32)，且匹配名称规格正则 | 教室策略名称 |
| classroomStrategyDesc | String | 否 | @Nullable @Size(max=128) | 教室策略描述 |
| linkShutdown | Boolean | 是 | @NotNull | 终端联动关机开关 |
| startPolicy | DesktopStartPolicyEnum | 是 | @NotNull | 上课云桌面启动策略 |
| defaultEnterImageSwitch | Boolean | 是 | @NotNull | 默认进入指定云桌面开关 |
| defaultEnterImageSeconds | Integer | 否 | @Nullable @Range(min=1, max=60)；开关开启时逻辑必填 | 默认进入指定云桌面倒计时（秒） |
| defaultDisplayDeskType | DefaultDisplayDeskType | 是 | @NotNull | 默认展示桌面类型 |
| reservedStoragePolicy | ReservedSpaceType | 是 | @NotNull | 预留空间类型 |
| reservedStorageSize | Integer | 否 | @Nullable @Range(min=1, max=1024)；预留策略为 USER_DEFINED 时逻辑必填 | 磁盘预留空间大小（GB） |
| creatorUserName | String | 否 | @Nullable | 创建者登录名（编辑时沿用） |
| updateTime | Date | 否 | @Nullable；构造时默认 new Date() | 更新时间 |

## 出参详情

| 返回类型 | DefaultWebResponse（data=成功key，msg=RCDC_RCC_CLASSROOM_STRATEGY_EDIT_OPERATE_LOG + 策略名） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| content | null | 纯操作接口：content 为空（成功响应仅 status/message，msgKey=RCDC_RCC_CLASSROOM_STRATEGY_EDIT_OPERATE_LOG） |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 处理流程

1. Assert.notNull(request/sessionContext)
2. classroomStrategyAPI.updateClassroomStrategy(request)（内部 validate：defaultEnterImageSwitch 开启时 seconds 必填、reservedStoragePolicy=USER_DEFINED 时 size 必填、名称规格校验）
3. 成功：auditLogAPI.recordLog(RCDC_RCC_CLASSROOM_STRATEGY_EDIT_OPERATE_LOG, 策略名)
4. 返回 success(EDIT_OPERATE_LOG, [策略名])
5. 失败：LOGGER.error 记录，auditLogAPI.recordLog(EDIT_OPERATE_FAIL_LOG, 策略名, e.getI18nMessage())
6. 返回 fail(EDIT_OPERATE_FAIL_LOG, [策略名, e.getI18nMessage()])

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | id | @NotNull | 缺失校验失败 |
| PARAM | classroomStrategyName | @NotBlank @Size(1-32) + 名称规格正则 | 不匹配抛 RCDC_RCC_CLASSROOM_STRATEGY_NAME_NOT_MATCHES_SPECIFICATION |
| PARAM | linkShutdown/startPolicy/defaultEnterImageSwitch/defaultDisplayDeskType/reservedStoragePolicy | @NotNull | 缺失校验失败 |
| BUSINESS | defaultEnterImageSeconds | defaultEnterImageSwitch=true 时必须填写 | 抛 RCDC_RCC_CLASSROOM_STRATEGY_DEFAULT_ENTER_IMAGE_SECONDS_IS_NULL |
| BUSINESS | reservedStorageSize | reservedStoragePolicy=USER_DEFINED 时必须填写 | 抛 RCDC_RCC_CLASSROOM_STRATEGY_RESERVED_STORAGE_SIZE_IS_NULL |
| BUSINESS | id | 策略必须存在 | 抛 RCDC_RCC_CLASSROOM_STRATEGY_NOT_FOUND |
| BUSINESS | classroomStrategyName | 名称唯一（排除自身） | 抛 RCDC_RCC_CLASSROOM_STRATEGY_NAME_DUPLICATE |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| id | user_input/from_query | 按业务构造 |
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
| updateTime | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 参数合法且策略存在 | $.status==SUCCESS |
### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 策略ID不存在 | id 无效 | $.status==ERROR 且 $.msgKey==RCDC_RCC_CLASSROOM_STRATEGY_EDIT_OPERATE_FAIL_LOG |
| 名称与其他策略重复 | classroomStrategyName 被占用 | $.status==ERROR 且 $.msgKey==RCDC_RCC_CLASSROOM_STRATEGY_EDIT_OPERATE_FAIL_LOG（msgArgArr[1] 为名称重复文案） |
## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | MEDIUM |
| 说明 | 按 id 整体更新策略，重复提交收敛于最终值；名称冲突时失败 |
