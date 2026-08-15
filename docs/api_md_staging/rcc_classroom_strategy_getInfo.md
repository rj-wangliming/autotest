---
version: '2.0'
api:
  url: /rcc/classroom/strategy/getInfo
  method: POST
  name: 获取教室策略详情。调 classroomStrategyAPI.getClassroomStrategyById(id) 返回 ClassroomStrateg
  controller: RccClassroomStrategyController
  method_ref: getDeskStrategy
  permission: 无
  exec_mode: 同步
  async: false
  description: 获取教室策略详情。调 classroomStrategyAPI.getClassroomStrategyById(id) 返回 ClassroomStrategyDTO。
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
  dto: IdWebRequest（sk.webmvc 框架类）
  body:
    id:
      type: UUID
      required: true
      constraint: '@NotNull'
      description: 教室策略ID
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    classroomStrategyId:
      type: UUID
      description: 教室策略ID
    classroomStrategyName:
      type: String
      description: 教室策略名称
    classroomStrategyDesc:
      type: String
      description: 教室策略描述
    linkShutdown:
      type: Boolean
      description: 终端联动关机开关
    startPolicy:
      type: DesktopStartPolicyEnum
      description: 上课云桌面启动策略
    defaultEnterImageSwitch/defaultEnterImageSeconds:
      type: Boolean/Integer
      description: 默认进入指定云桌面开关/倒计时
    defaultDisplayDeskType:
      type: DefaultDisplayDeskType
      description: 默认展示桌面类型
    creatorUserName:
      type: String
      description: 创建者登录名
    classroomStrategyState:
      type: ClassroomStrategyState
      description: 策略状态
    createTime/updateTime:
      type: Date
      description: 创建/更新时间
    refClassroomNum:
      type: Integer
      description: 引用该策略的教室数
    reservedStoragePolicy/reservedStorageSize:
      type: ReservedSpaceType/Integer
      description: 预留空间类型/大小
    startMode:
      type: CbbTerminalStartMode
      description: 终端启动模式（默认UEFI）
upstream:
- api: 内部调用:rcc/ClassroomStrategyAPI
  purpose: 按ID查询教室策略详情
downstream:
- api: 内部调用:rcc/ClassroomStrategyAPI#getClassroomStrategyById
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: id
  rule: '@NotNull'
  failure: 缺失校验失败
- level: BUSINESS
  field: id
  rule: 策略必须存在
  failure: 抛 RCDC_RCC_CLASSROOM_STRATEGY_NOT_FOUND
assertions:
  success:
  - scenario: 传入有效策略ID
    expect: $.status=="SUCCESS"；$.content.classroomStrategyId 非空
  failure:
  - scenario: 策略ID不存在
    trigger: id 无效
    expect: status==ERROR；msgKey==RCDC_RCC_CLASSROOM_STRATEGY_NOT_FOUND
cleanup: []
idempotency:
  level: non_idempotent
  note: 纯查询接口，无副作用
params:
  required:
  - name: strategy_name
    desc: ''
    used_by: 见 setup/request
  - name: classroom_strategy_name
    desc: ''
    used_by: setup/request
---
# POST /rcc/classroom/strategy/getInfo

> 获取教室策略详情。调 classroomStrategyAPI.getClassroomStrategyById(id) 返回 ClassroomStrategyDTO。 ｜ 无特殊权限 ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/strategy/getInfo<br>获取教室策略详情。调 classroomStrategyAPI.getClass<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(webRequest)"]
        C2["Step2: classroomStrategyAPI.getClassroomStrateg"]
        C3["Step3: return CommonWebResponse.success(dto)"]
        C1 --> C2
        C2 --> C3
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
| URL | /rcc/classroom/strategy/getInfo |
| Controller | RccClassroomStrategyController |
| 方法名 | getDeskStrategy |
| 权限注解 | 无 |
| 执行方式 | 同步 |
| 业务含义 | 获取教室策略详情。调 classroomStrategyAPI.getClassroomStrategyById(id) 返回 ClassroomStrategyDTO。 |

## 入参详情

### IdWebRequest（sk.webmvc 框架类）

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| id | UUID | 是 | @NotNull | 教室策略ID |

## 出参详情

| 返回类型 | CommonWebResponse（data=ClassroomStrategyDTO） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| classroomStrategyId | UUID | 教室策略ID |
| classroomStrategyName | String | 教室策略名称 |
| classroomStrategyDesc | String | 教室策略描述 |
| linkShutdown | Boolean | 终端联动关机开关 |
| startPolicy | DesktopStartPolicyEnum | 上课云桌面启动策略 |
| defaultEnterImageSwitch | Boolean | 单镜像默认进入开关 |
| defaultEnterImageSeconds | Integer | 单镜像自动进入倒计时秒数 |
| defaultDisplayDeskType | DefaultDisplayDeskType | 默认展示桌面类型 |
| creatorUserName | String | 创建者登录名 |
| classroomStrategyState | ClassroomStrategyState | 策略状态 |
| createTime | Date | 创建时间 |
| updateTime | Date | 更新时间 |
| refClassroomNum | Integer | 引用该策略的教室数 |
| reservedStoragePolicy | ReservedSpaceType | 预留空间类型 |
| reservedStorageSize | Integer | 磁盘预留空间大小 |
| startMode | CbbTerminalStartMode | 终端启动模式（默认UEFI） |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 处理流程

1. Assert.notNull(webRequest)
2. classroomStrategyAPI.getClassroomStrategyById(webRequest.getId()) 查询
3. return CommonWebResponse.success(dto)

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | id | @NotNull | 缺失校验失败 |
| BUSINESS | id | 策略必须存在 | 抛 RCDC_RCC_CLASSROOM_STRATEGY_NOT_FOUND |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| id | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 传入有效策略ID | $.status=="SUCCESS"；$.content.classroomStrategyId 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 策略ID不存在 | id 无效 | status==ERROR；msgKey==RCDC_RCC_CLASSROOM_STRATEGY_NOT_FOUND |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 纯查询接口，无副作用 |
