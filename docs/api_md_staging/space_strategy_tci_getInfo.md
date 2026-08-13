---
api:
  url: /space/strategy/tci/getInfo
  method: POST
  name: 获取课程策略详情（别名）
  controller: SpaceDeskStrategyGroupTCIController
  method_ref: detail
  permission: '@EnableAuthority'
  exec_mode: sync
  async: false
  description: getInfo 与 detail 是同一方法（@RequestMapping({"detail","getInfo"})），完整文档见 space_strategy_tci_detail.md
  alias_of: /space/strategy/tci/detail
request:
  dto: IdWebRequest
  body:
    id:
      type: UUID
      required: true
      description: 策略组ID
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
      description: 策略组详情对象（getInfo 与 detail 同方法，完整字段见 detail 文档）
      alias_of: /space/strategy/tci/detail
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
assertions:
  success:
  - scenario: 正常查询
    expect: $.status=="SUCCESS"；$.content.id 非空；$.content.strategyType 等字段（完整见 detail 出参）
  failure:
  - scenario: 策略不存在
    trigger: id 无效
    expect: status==ERROR（策略不存在类 msgKey）
idempotency:
  level: fully_idempotent
  note: 只读查询，可安全重试
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
---
# POST /space/strategy/tci/getInfo

> 获取课程策略详情（**别名**）

## 入参详情

### IdWebRequest（框架类）

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| id | UUID | 是 | @NotNull | 策略组ID |

**getInfo 与 POST /space/strategy/tci/detail 是同一方法**：源码 `@RequestMapping(value = {"detail", "getInfo"})`，两者请求/响应完全一致。

📎 完整文档：[space_strategy_tci_detail.md](space_strategy_tci_detail.md)

| 项 | 值 |
|---|---|
| 真实方法 | `detail(IdWebRequest, SessionContext)` |
| 权限 | @EnableAuthority |
| 入参 | id: UUID（必填） |
| 说明 | 获取 TCI 策略详情 |

## 出参详情

> getInfo 与 detail 是同一方法（@RequestMapping({"detail","getInfo"})），返回 DefaultWebResponse\<SpaceDeskStrategyGroupTCI\> 完整对象。

### 外层响应（SK 框架统一包装）

| 字段 | 类型 | 说明 |
|---|---|---|
| status | String | SUCCESS/ERROR |
| message | String | 提示消息 |
| msgKey | String | 错误消息key |
| msgArgArr | String[] | 消息参数数组 |
| content | SpaceDeskStrategyGroupTCI | 策略组详情对象 |

### content 业务字段（SpaceDeskStrategyGroupTCI，完整 18 字段）

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
| name | String | 策略组名称 |
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

> 完整说明（含约束/断言）见 space_strategy_tci_detail.md。
