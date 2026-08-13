---
api:
  url: /space/strategygroup/vdi/getInfo
  method: POST
  name: 获取课程云桌面策略详情（别名）
  controller: SpaceDeskStrategyGroupVDIController
  method_ref: detail
  permission: '@EnableAuthority'
  exec_mode: sync
  async: false
  description: getInfo 与 detail 是同一方法（@RequestMapping({"detail","getInfo"})），完整文档见 space_strategygroup_vdi_detail.md
  alias_of: /space/strategygroup/vdi/detail
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
      type: SpaceDeskStrategyGroupVDI
      description: 策略组详情对象（getInfo 与 detail 同方法，完整字段见 detail 文档）
      alias_of: /space/strategygroup/vdi/detail
      fields:
        id:
          type: UUID
          description: 策略组ID（继承 AbstractDomainObject）
        name:
          type: String
          description: 策略组名称（继承 AbstractDomainObject）
        cpu: Integer
        memory: Integer
        vgpuType: VgpuType
        vgpuExtraInfo: VgpuExtraInfo
        deskCreateMode: DeskCreateMode
        enableHyperVisorImprove: Boolean
        enableNested: Boolean
        enableDoubleScreen: Boolean
        enableHa: Boolean
        haPriority: Integer
        desktopOccupyDriveArr: String[]
        keyboardEmulationType: CbbKeyboardEmulationType
        needHideFloatBar: Boolean
        enableShowLocalDisk: Boolean
        enableStudentAccount: Boolean
        studentAccountPreName: String
        studentAccountPassword: String
        enableAdaptiveResolution: Boolean
        enableSoftwareDecode: Boolean
        shutDownDeleteSystemDisk: Boolean
        note: String
        state: SpaceStrategyGroupState
        pattern: CbbCloudDeskPattern
        strategyType: DeskVirtualizationType
        enablePersonalConfig: Boolean
        deskPersonalConfigStrategyType: CbbDeskPersonalConfigStrategyType
        personalConfigDiskSize: Integer
        systemSize: Integer
        platformStrategyGroup: PlatformStrategyGroup
        enableInternet: Boolean
assertions:
  success:
  - scenario: 正常查询
    expect: status==SUCCESS；content 为策略详情（见 detail 出参）
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
# POST /space/strategygroup/vdi/getInfo

> 获取课程云桌面策略详情（**别名**）

## 入参详情

### IdWebRequest（框架类）

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| id | UUID | 是 | @NotNull | 策略组ID |

**getInfo 与 POST /space/strategygroup/vdi/detail 是同一方法**：源码 `@RequestMapping(value = {"detail", "getInfo"})`，两者请求/响应完全一致。

📎 完整文档：[space_strategygroup_vdi_detail.md](space_strategygroup_vdi_detail.md)

| 项 | 值 |
|---|---|
| 真实方法 | `detail(IdWebRequest, SessionContext)` |
| 权限 | @EnableAuthority |
| 入参 | id: UUID（必填） |
| 说明 | 获取 VDI 策略详情，vgpuExtraInfo.model 含 AGV 时替换为 GPU_AGV |

## 出参详情

> getInfo 与 detail 是同一方法（@RequestMapping({"detail","getInfo"})），返回 DefaultWebResponse\<SpaceDeskStrategyGroupVDI\> 完整对象，出参结构完全一致。

### 外层响应（SK 框架统一包装）

| 字段 | 类型 | 说明 |
|---|---|---|
| status | String | SUCCESS/ERROR |
| message | String | 提示消息 |
| msgKey | String | 错误消息key |
| msgArgArr | String[] | 消息参数数组 |
| content | SpaceDeskStrategyGroupVDI | 策略组详情对象 |

### content 业务字段（SpaceDeskStrategyGroupVDI，完整 31 字段）

**自有字段（SpaceDeskStrategyGroupVDI，20）**

| 字段 | 类型 | 说明 |
|---|---|---|
| cpu | Integer | 桌面CPU核数（VDI生效），1~64 |
| memory | Integer | 桌面内存MB（VDI生效），1024~262144 |
| vgpuType | VgpuType | vGPU类型 |
| vgpuExtraInfo | VgpuExtraInfo | vGPU配置信息（detail 返回时 model 含 AGV 前缀替换为 GPU_AGV 标题） |
| deskCreateMode | DeskCreateMode | 云桌面创建方式 |
| enableHyperVisorImprove | Boolean | 是否配置开启虚机特性提升，默认开启 true |
| enableNested | Boolean | 是否启用嵌套虚拟化（VDI\IDV 生效） |
| enableDoubleScreen | Boolean | 是否启用双屏 |
| enableHa | Boolean | 是否启用高可用特性 |
| haPriority | Integer | 配置HA优先级，0~10 |
| desktopOccupyDriveArr | String[] | 第三方应用盘符（VDI\IDV\TCI 生效） |
| keyboardEmulationType | CbbKeyboardEmulationType | 键盘模拟类型 |
| needHideFloatBar | Boolean | 隐藏学生端浮动条 |
| enableShowLocalDisk | Boolean | 显示VDI数据盘 |
| enableStudentAccount | Boolean | 启用学生端用户名和密码 |
| studentAccountPreName | String | 学生端用户名前缀，1~15 位 |
| studentAccountPassword | String | 学生端密码（detail 出参返回加密后的密文） |
| enableAdaptiveResolution | Boolean | 云桌面分辨率自适应 |
| enableSoftwareDecode | Boolean | 启用3D软解 |
| shutDownDeleteSystemDisk | Boolean | VDI还原类型桌面关机后是否删除系统盘 |

**继承字段（AbstractSpaceDeskStrategyGroup，11）**

| 字段 | 类型 | 说明 |
|---|---|---|
| note | String | 备注 |
| state | SpaceStrategyGroupState | 策略状态（AVAILABLE 等） |
| pattern | CbbCloudDeskPattern | 桌面类型 |
| strategyType | DeskVirtualizationType | 策略类型（VDI/TCI） |
| enablePersonalConfig | Boolean | 是否启用浮动个性配置（默认 false） |
| deskPersonalConfigStrategyType | CbbDeskPersonalConfigStrategyType | 浮动个性配置类型 |
| personalConfigDiskSize | Integer | 浮动个性盘大小 GB，1~2048 |
| systemSize | Integer | 系统盘大小 GB，0~2048 |
| platformStrategyGroup | PlatformStrategyGroup | 平台策略组 |
| desktopOccupyDriveArr | String[] | 第三方应用盘符（父类声明，VDI 子类同名覆盖） |
| enableInternet | Boolean | 联网开关 |

> 完整说明（含约束/断言）见 space_strategygroup_vdi_detail.md。
