---
api:
  url: /space/strategy/tci/detail
  method: POST
  name: 获取课程策略详情
  controller: SpaceDeskStrategyGroupTCIController
  method_ref: detail
  permission: '@EnableAuthority'
  exec_mode: sync
  async: false
  description: 获取TCI策略组详情（getInfo 为同一方法的别名 @RequestMapping({"detail","getInfo"})）
request:
  body:
    id:
      type: UUID
      required: true
      description: 策略组ID（来自 /space/strategy/tci/list 或 create）
      value: ${param.id}
  dto: IdWebRequest
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    content:
      type: SpaceDeskStrategyGroupTCI
      description: 策略组详情对象（含入参回显+服务端填充字段）
      fields:
        id: UUID
        name: String
        note: String
        state: SpaceStrategyGroupState
        pattern: CbbCloudDeskPattern
        strategyType: DeskVirtualizationType
        enablePersonalConfig: Boolean
        deskPersonalConfigStrategyType: CbbDeskPersonalConfigStrategyType
        personalConfigDiskSize: Integer
        systemSize: Integer
        desktopOccupyDriveArr: String[]
        enableInternet: Boolean
        platformStrategyGroup: PlatformStrategyGroup
        enableDiskConfig: Boolean
        diskSize: Integer
        enableScheduleStrategy: Boolean
        diskRestoreStrategyArr: TCIDiskStrategyDTO[]
        enableAutoEdit: Boolean
        enableForceAutoEdit: Boolean
        enableAdaptiveResolution: Boolean
upstream:
- api: POST /space/strategy/tci/list
  purpose: 获取策略ID（出参 $.content.itemArr[].id → 入参 id）
- api: 管理员登录
  purpose: '@EnableAuthority 前置'
downstream:
- api: POST /space/strategy/tci/edit
  purpose: 编辑前读取详情
constraints:
- level: controller
  field: id
  rule: not_null
  failure: Assert.notNull (#315)
assertions:
  success:
  - scenario: 正常查询
    expect: status==SUCCESS；content.id==传入id
  failure:
  - scenario: 策略不存在
    trigger: id 无效
    expect: status==ERROR
cleanup: []
idempotency:
  level: fully_idempotent
  note: 只读查询，可安全重试
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
---
# POST /space/strategy/tci/detail

> 获取课程策略详情 ｜ @EnableAuthority ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /space/strategy/tci/list<br>获取策略ID"]
        A2["管理员登录"]
    end
    B["POST /space/strategy/tci/detail<br>获取TCI策略详情<br>权限: @EnableAuthority"]
    A1 -->|id| B
    A2 -->|登录态| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(webRequest) #315"]
        C2["Step2: super.defaultDetail(webRequest)"]
    end
    B --> C1
    C1 --> C2
    subgraph 下游消费方
        D1["POST /space/strategy/tci/edit<br>编辑前读取"]
    end
    B -->|数据| D1
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /space/strategy/tci/detail |
| Controller | SpaceDeskStrategyGroupTCIController |
| 方法名 | detail |
| 权限注解 | @EnableAuthority |
| 执行方式 | 同步 |
| 业务含义 | 获取TCI策略组详情（getInfo 为别名） |

## 入参详情

### IdWebRequest（框架类）

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| id | UUID | 是 | @NotNull | 策略组ID |

## 出参详情

| 返回类型 | DefaultWebResponse\<SpaceDeskStrategyGroupTCI\> |
|---|---|

### 外层响应（SK 框架统一包装）

| 字段 | 类型 | 说明 |
|---|---|---|
| status | String | SUCCESS/ERROR |
| message | String | 提示消息 |
| msgKey | String | 错误消息key（成功时为空） |
| msgArgArr | String[] | 消息参数数组 |
| content | SpaceDeskStrategyGroupTCI | 策略组详情对象 |

### content 业务字段（SpaceDeskStrategyGroupTCI，含继承）

**自有字段（SpaceDeskStrategyGroupTCI）**

| 字段 | 类型 | 说明 |
|---|---|---|
| enableDiskConfig | Boolean | 是否开启数据盘 |
| diskSize | Integer | 数据盘大小 GB |
| enableScheduleStrategy | Boolean | 是否开启定时还原策略 |
| diskRestoreStrategyArr | TCIDiskStrategyDTO[] | 磁盘还原策略数组 |
| enableAutoEdit | Boolean | 启用自动编辑（默认 false） |
| enableForceAutoEdit | Boolean | 强制自动编辑（默认 true） |
| enableAdaptiveResolution | Boolean | 自适应分辨率（默认 true） |

**继承字段（AbstractSpaceDeskStrategyGroup）**

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 策略组ID |
| name | String | 策略组名称（继承 AbstractDomainObject） |
| note | String | 备注 |
| state | SpaceStrategyGroupState | 策略状态（AVAILABLE 等） |
| pattern | CbbCloudDeskPattern | 桌面类型（RECOVERABLE/PERSONAL） |
| strategyType | DeskVirtualizationType | 策略类型（TCI/VOI） |
| enablePersonalConfig | Boolean | 是否开启个人配置 |
| deskPersonalConfigStrategyType | CbbDeskPersonalConfigStrategyType | 个人配置策略类型 |
| personalConfigDiskSize | Integer | 个人配置盘大小 |
| systemSize | Integer | 系统盘大小 |
| desktopOccupyDriveArr | String[] | 第三方盘符 I~Z |
| enableInternet | Boolean | 联网开关 |
| platformStrategyGroup | PlatformStrategyGroup | 平台策略组（strategyGroupFacadeStr 含 voi 节点） |

> 源码依据：SpaceDeskStrategyGroupTCIController.detail(#312，@RequestMapping({"detail","getInfo"})) → super.defaultDetail，返回 DefaultWebResponse\<SpaceDeskStrategyGroupTCI\> 完整对象。

## 上游前置业务

### 前置1：POST /space/strategy/tci/list — 获取策略ID

- 产出：$.content.itemArr[].id
- 说明：策略ID由列表/创建接口产出

### 前置2：管理员登录

- 产出：SessionContext
- 说明：@EnableAuthority 前置

## 内部处理流程

1. Assert.notNull(webRequest) 校验入参非空
2. super.defaultDetail(webRequest) 查询策略详情

## 下游消费方

### 消费1：POST /space/strategy/tci/edit — 编辑前读取当前详情

## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| controller | id | not_null | Assert.notNull (#315) |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| id | from_upstream | /space/strategy/tci/list 或 create 产出 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 正常查询 | status==SUCCESS；content.id==传入id |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 策略不存在 | id 无效 | status==ERROR |
| 入参为空 | id 未传 | $.status==ERROR（Assert.notNull 异常，HTTP 400） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| （查询接口无清理） | 只读 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | fully_idempotent（只读查询） |
| 说明 | 可安全重试 |
