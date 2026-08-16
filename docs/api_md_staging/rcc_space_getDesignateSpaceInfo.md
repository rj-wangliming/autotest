---
version: '2.0'
api:
  url: /rcc/space/getDesignateSpaceInfo
  method: POST
  name: 查询指定类型的实训桌面池或教学桌面池列表。入参 type 为 BusinessTypeAndCreateSourceEnum：RCC_CLASSROOM（教学桌
  controller: RccSpaceController
  method_ref: getDesignateSpaceInfo
  permission: 无
  exec_mode: 同步
  async: false
  description: 查询指定类型的实训桌面池或教学桌面池列表。入参 type 为 BusinessTypeAndCreateSourceEnum：RCC_CLASSROOM（教学桌面池）时返回 rccSpaceAPI.findAllSpace() 全部教学实训空间；RCO_SPACE（实训桌面池）时经 platformSubSysResRelationAPI.findByResourceTypeInSpace(Res
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
request:
  dto: RccSpaceBusinessTypeAndCreateSourceRequest
  body:
    type:
      type: BusinessTypeAndCreateSourceEnum
      required: true
      constraint: '@NotNull'
      description: 业务类型与创建来源：RCC_CLASSROOM=教学桌面池、RCO_SPACE=实训桌面池、RCO_COMMON=办公桌面
      value: ${param.type}
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    content:
      type: RccSpaceInfoDTO[]
      description: 指定业务类型的空间列表（元素字段见下）
    allowMaxUseTime::
      type: Integer
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.allowMaxUseTime）
    allowUseTimeInfo::
      type: String
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.allowUseTimeInfo）
    allowUseTimeInfoDTOArr::
      type: RccAllowUseTimeInfoDTO[]
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.allowUseTimeInfoDTOArr）
    beforeRecycleNotifyTime::
      type: Integer
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.beforeRecycleNotifyTime）
    businessType::
      type: BusinessType
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.businessType）
    canUsed::
      type: Boolean
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.canUsed）
    canUsedMessage::
      type: String
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.canUsedMessage）
    classroomId::
      type: UUID
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.classroomId）
    classroomName::
      type: String
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.classroomName）
    clusterId::
      type: UUID
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.clusterId）
    clusterInfo::
      type: ClusterInfoDTO
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.clusterInfo）
    conflictDeskNum::
      type: Integer
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.conflictDeskNum）
    connectedNum::
      type: Integer
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.connectedNum）
    cpu::
      type: Integer
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.cpu）
    createSource::
      type: CreateSource
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.createSource）
    description::
      type: String
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.description）
    deskCreateMode::
      type: DeskCreateMode
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.deskCreateMode）
    desktopNum::
      type: Integer
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.desktopNum）
    desktopPoolCreateTime::
      type: Date
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.desktopPoolCreateTime）
    desktopPoolId::
      type: UUID
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.desktopPoolId）
    desktopPoolName::
      type: String
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.desktopPoolName）
    desktopPoolNamePrefix::
      type: String
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.desktopPoolNamePrefix）
    desktopPoolUpdateTime::
      type: Date
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.desktopPoolUpdateTime）
    desktopType::
      type: CbbCloudDeskPattern
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.desktopType）
    enableAllowMaxUseTime::
      type: Boolean
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.enableAllowMaxUseTime）
    enableAllowUseTimeInfo::
      type: Boolean
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.enableAllowUseTimeInfo）
    enableSpecifiedIpRange::
      type: Boolean
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.enableSpecifiedIpRange）
    id::
      type: UUID
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.id）
    idleDesktopRecover::
      type: Integer
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.idleDesktopRecover）
    imageTemplateId::
      type: UUID
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.imageTemplateId）
    imageTemplateName::
      type: String
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.imageTemplateName）
    isOpenMaintenance::
      type: Boolean
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.isOpenMaintenance）
    memory::
      type: Double
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.memory）
    name::
      type: String
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.name）
    networkId::
      type: UUID
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.networkId）
    networkName::
      type: String
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.networkName）
    osType::
      type: CbbOsType
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.osType）
    platformId::
      type: UUID
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.platformId）
    platformName::
      type: String
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.platformName）
    platformStatus::
      type: CloudPlatformStatus
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.platformStatus）
    platformType::
      type: CloudPlatformType
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.platformType）
    poolModel::
      type: CbbDesktopPoolModel
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.poolModel）
    poolState::
      type: CbbDesktopPoolState
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.poolState）
    preStartDesktopNum::
      type: Integer
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.preStartDesktopNum）
    rootImageId::
      type: UUID
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.rootImageId）
    rootImageName::
      type: String
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.rootImageName）
    softwareStrategyId::
      type: UUID
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.softwareStrategyId）
    softwareStrategyName::
      type: String
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.softwareStrategyName）
    spaceCreateTime::
      type: Date
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.spaceCreateTime）
    spaceId::
      type: UUID
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.spaceId）
    spaceName::
      type: String
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.spaceName）
    spaceUpdateTime::
      type: Date
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.spaceUpdateTime）
    storagePool::
      type: StoragePoolDetailDTO
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.storagePool）
    storagePoolId::
      type: UUID
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.storagePoolId）
    strategyId::
      type: UUID
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.strategyId）
    strategyName::
      type: String
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.strategyName）
    systemDisk::
      type: Integer
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.systemDisk）
    userProfileStrategyId::
      type: UUID
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.userProfileStrategyId）
    userProfileStrategyName::
      type: String
      description: 空间列表元素字段（源码 RccSpaceInfoDTO.userProfileStrategyName）

    id:
      type: UUID
      description: 记录ID
    name:
      type: String
      description: 名称
    spaceId:
      type: UUID
      description: 实训空间ID
    spaceName:
      type: String
      description: 实训空间名称
    classroomId:
      type: UUID
      description: 绑定的教室ID
    enableAllowMaxUseTime:
      type: Boolean
      description: 是否开启单次允许接入最大时间配置
    allowMaxUseTime:
      type: Integer
      description: 单次允许接入最大时间
    beforeRecycleNotifyTime:
      type: Integer
      description: 断开连接前提示时间
    enableAllowUseTimeInfo:
      type: Boolean
      description: 是否开启实训桌面池接入控制策略
    allowUseTimeInfo:
      type: String
      description: 云桌面允许登录时间（字符串）
    allowUseTimeInfoDTOArr:
      type: RccAllowUseTimeInfoDTO[]
      description: 云桌面允许登录时间配置
    spaceCreateTime:
      type: Date
      description: 实训空间创建时间
    spaceUpdateTime:
      type: Date
      description: 实训空间更新时间
    desktopPoolId:
      type: UUID
      description: 桌面池ID
    desktopPoolName:
      type: String
      description: 桌面池名称
    desktopPoolNamePrefix:
      type: String
      description: 云桌面名称前缀（null时采用桌面池名称）
    poolModel:
      type: CbbDesktopPoolModel
      description: 池模式
    idleDesktopRecover:
      type: Integer
      description: 空闲桌面自动回收时间（分钟）
    description:
      type: String
      description: 备注
    strategyId:
      type: UUID
      description: 云桌面策略ID
    strategyName:
      type: String
      description: 云桌面策略名称
    networkId:
      type: UUID
      description: 网络策略ID
    networkName:
      type: String
      description: 网络策略名称
    poolState:
      type: CbbDesktopPoolState
      description: 桌面池状态
    preStartDesktopNum:
      type: Integer
      description: 维持预启动数
    isOpenMaintenance:
      type: Boolean
      description: 是否开启维护模式
    desktopPoolCreateTime:
      type: Date
      description: 桌面池创建时间
    desktopPoolUpdateTime:
      type: Date
      description: 桌面池更新时间
    softwareStrategyId:
      type: UUID
      description: 软件策略ID
    softwareStrategyName:
      type: String
      description: 软件策略名称
    userProfileStrategyId:
      type: UUID
      description: 用户配置策略ID
    userProfileStrategyName:
      type: String
      description: 用户配置策略名称
    clusterId:
      type: UUID
      description: 计算集群ID
    platformId:
      type: UUID
      description: 云平台ID
    storagePoolId:
      type: UUID
      description: 存储池ID
    businessType:
      type: BusinessType
      description: 业务类型
    createSource:
      type: CreateSource
      description: 创建来源
    enableSpecifiedIpRange:
      type: Boolean
      description: 是否开启特定终端IP允许访问
    canUsed:
      type: Boolean
      description: 是否可勾选（默认true）
    canUsedMessage:
      type: String
      description: canUsed=false 的提示语
    conflictDeskNum:
      type: Integer
      description: 池中配置不一致的桌面数量
    clusterInfo:
      type: ClusterInfoDTO
      description: 计算集群信息
    storagePool:
      type: StoragePoolDetailDTO
      description: 存储池详情
    classroomName:
      type: String
      description: 教室名称
    desktopType:
      type: CbbCloudDeskPattern
      description: 云桌面类型
    memory:
      type: Double
      description: 内存大小（GB）
    cpu:
      type: Integer
      description: CPU核数
    systemDisk:
      type: Integer
      description: 系统盘大小（GB）
    deskCreateMode:
      type: DeskCreateMode
      description: 创建方式
    imageTemplateId:
      type: UUID
      description: 镜像模板ID
    imageTemplateName:
      type: String
      description: 镜像模板名称
    rootImageId:
      type: UUID
      description: 根镜像ID
    rootImageName:
      type: String
      description: 根镜像名称
    osType:
      type: CbbOsType
      description: 操作系统类型
    desktopNum:
      type: Integer
      description: 桌面数量
    connectedNum:
      type: Integer
      description: 连接数
    platformType:
      type: CloudPlatformType
      description: 云平台类型（继承 RccPlatformBaseInfoDTO）
    platformName:
      type: String
      description: 云平台名称（继承 RccPlatformBaseInfoDTO）
    platformStatus:
      type: CloudPlatformStatus
      description: 云平台状态（继承 RccPlatformBaseInfoDTO）
upstream:
- api: 内部调用:rcc/RccSpaceAPI
  purpose: RCC_CLASSROOM 时查询全部教学实训空间
- api: 内部调用:pa/PlatformSubSysResRelationAPI
  purpose: RCO_SPACE 时按资源类型 DESK_POOL 查询子系统资源关联
- api: 内部调用:pa/PlatformDesktopPoolMgmtAPI
  purpose: 按桌面池ID列表查询基本信息
downstream:
- api: 内部调用:rcc/RccSpaceAPI#findAllSpace
  purpose: 内部调用（非 HTTP 端点）
- api: 内部调用:pa/PlatformDesktopPoolMgmtAPI#getDesktopPoolInfoByIdList
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: type
  rule: '@NotNull'
  failure: 缺失时校验失败
- level: BUSINESS
  field: type
  rule: 仅处理 RCC_CLASSROOM 与 RCO_SPACE 两类
  failure: 其他枚举返回空列表
assertions:
  success:
  - scenario: type=RCC_CLASSROOM
    expect: $.content 非空
  - scenario: type=RCO_SPACE 且存在关联桌面池
    expect: $.content 非空
  failure:
  - scenario: type 缺失
    trigger: type 未传
    expect: $.status==ERROR
  - scenario: RCO_SPACE 无关联资源
    trigger: 无子系统关联桌面池
    expect: $.status==SUCCESS 且 $.content 为空
cleanup: []
idempotency:
  level: non_idempotent
  note: 只读查询，无副作用
params:
  required:
  - name: type
---
# POST /rcc/space/getDesignateSpaceInfo

> 查询指定类型的实训桌面池或教学桌面池列表。入参 type 为 BusinessTypeAndCreateSourceEnum：RCC_CLASSROOM（教学桌面池）时返回 rccSpaceAPI.findAllSpace() 全部教学实训空间；RCO_SPACE（实训桌面池）时经 platformSubSysResRelationAPI.findByResourceTypeInSpace(ResourceType.DESK_POOL) 找到关联桌面池ID，再 desktopPoolMgmtAPI.getDesktopPoolInfoByIdList 查询并转换为 RccSpaceInfoDTO；其他类型返回空列表。 ｜ 无特殊权限 ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/space/getDesignateSpaceInfo<br>查询指定类型的实训桌面池或教学桌面池列表。入参 type 为 BusinessT<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request)"]
        C2["Step2: type==RCC_CLASSROOM：rccSpaceAPI.findAllS"]
        C3["Step3: type==RCO_SPACE：platformSubSysResRelatio"]
        C4["Step4: 其他类型返回空列表"]
        C5["Step5: 返回 CommonWebResponse.success(list)"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
        C4 --> C5
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
| URL | /rcc/space/getDesignateSpaceInfo |
| Controller | RccSpaceController |
| 方法名 | getDesignateSpaceInfo |
| 权限注解 | 无 |
| 执行方式 | 同步 |
| 业务含义 | 查询指定类型的实训桌面池或教学桌面池列表。入参 type 为 BusinessTypeAndCreateSourceEnum：RCC_CLASSROOM（教学桌面池）时返回 rccSpaceAPI.findAllSpace() 全部教学实训空间；RCO_SPACE（实训桌面池）时经 platformSubSysResRelationAPI.findByResourceTypeInSpace(ResourceType.DESK_POOL) 找到关联桌面池ID，再 desktopPoolMgmtAPI.getDesktopPoolInfoByIdList 查询并转换为 RccSpaceInfoDTO；其他类型返回空列表。 |

## 入参详情

### RccSpaceBusinessTypeAndCreateSourceRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| type | BusinessTypeAndCreateSourceEnum | 是 | @NotNull | 业务类型与创建来源：RCC_CLASSROOM=教学桌面池、RCO_SPACE=实训桌面池、RCO_COMMON=办公桌面 |

## 出参详情

| 返回类型 | CommonWebResponse<List<RccSpaceInfoDTO>> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 记录ID |
| name | String | 名称 |
| spaceId | UUID | 实训空间ID |
| spaceName | String | 实训空间名称 |
| classroomId | UUID | 绑定的教室ID |
| enableAllowMaxUseTime | Boolean | 是否开启单次允许接入最大时间配置 |
| allowMaxUseTime | Integer | 单次允许接入最大时间 |
| beforeRecycleNotifyTime | Integer | 断开连接前提示时间 |
| enableAllowUseTimeInfo | Boolean | 是否开启实训桌面池接入控制策略 |
| allowUseTimeInfo | String | 云桌面允许登录时间（字符串） |
| allowUseTimeInfoDTOArr | RccAllowUseTimeInfoDTO[] | 云桌面允许登录时间配置 |
| spaceCreateTime | Date | 实训空间创建时间 |
| spaceUpdateTime | Date | 实训空间更新时间 |
| desktopPoolId | UUID | 桌面池ID |
| desktopPoolName | String | 桌面池名称 |
| desktopPoolNamePrefix | String | 云桌面名称前缀（null时采用桌面池名称） |
| poolModel | CbbDesktopPoolModel | 池模式 |
| idleDesktopRecover | Integer | 空闲桌面自动回收时间（分钟） |
| description | String | 备注 |
| strategyId | UUID | 云桌面策略ID |
| strategyName | String | 云桌面策略名称 |
| networkId | UUID | 网络策略ID |
| networkName | String | 网络策略名称 |
| poolState | CbbDesktopPoolState | 桌面池状态 |
| preStartDesktopNum | Integer | 维持预启动数 |
| isOpenMaintenance | Boolean | 是否开启维护模式 |
| desktopPoolCreateTime | Date | 桌面池创建时间 |
| desktopPoolUpdateTime | Date | 桌面池更新时间 |
| softwareStrategyId | UUID | 软件策略ID |
| softwareStrategyName | String | 软件策略名称 |
| userProfileStrategyId | UUID | 用户配置策略ID |
| userProfileStrategyName | String | 用户配置策略名称 |
| clusterId | UUID | 计算集群ID |
| platformId | UUID | 云平台ID |
| storagePoolId | UUID | 存储池ID |
| businessType | BusinessType | 业务类型 |
| createSource | CreateSource | 创建来源 |
| enableSpecifiedIpRange | Boolean | 是否开启特定终端IP允许访问 |
| canUsed | Boolean | 是否可勾选（默认true） |
| canUsedMessage | String | canUsed=false 的提示语 |
| conflictDeskNum | Integer | 池中配置不一致的桌面数量 |
| clusterInfo | ClusterInfoDTO | 计算集群信息 |
| storagePool | StoragePoolDetailDTO | 存储池详情 |
| classroomName | String | 教室名称 |
| desktopType | CbbCloudDeskPattern | 云桌面类型 |
| memory | Double | 内存大小（GB） |
| cpu | Integer | CPU核数 |
| systemDisk | Integer | 系统盘大小（GB） |
| deskCreateMode | DeskCreateMode | 创建方式 |
| imageTemplateId | UUID | 镜像模板ID |
| imageTemplateName | String | 镜像模板名称 |
| rootImageId | UUID | 根镜像ID |
| rootImageName | String | 根镜像名称 |
| osType | CbbOsType | 操作系统类型 |
| desktopNum | Integer | 桌面数量 |
| connectedNum | Integer | 连接数 |
| platformType | CloudPlatformType | 云平台类型（继承 RccPlatformBaseInfoDTO） |
| platformName | String | 云平台名称（继承 RccPlatformBaseInfoDTO） |
| platformStatus | CloudPlatformStatus | 云平台状态（继承 RccPlatformBaseInfoDTO） |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 处理流程

1. Assert.notNull(request)
2. type==RCC_CLASSROOM：rccSpaceAPI.findAllSpace() 返回教学实训空间列表
3. type==RCO_SPACE：platformSubSysResRelationAPI.findByResourceTypeInSpace(DESK_POOL) 查关联 → desktopPoolMgmtAPI.getDesktopPoolInfoByIdList → convertToRccSpaceInfoDTO 转换（BeanUtils 拷贝并设置 desktopPoolId/desktopPoolName）
4. 其他类型返回空列表
5. 返回 CommonWebResponse.success(list)

## 下游消费方

### 消费1：POST /rcc/space/getDesignateSpaceInfo

指定类型空间ID列表，可被下拉选择后用于 detail/edit/delete（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | type | @NotNull | 缺失时校验失败 |
| BUSINESS | type | 仅处理 RCC_CLASSROOM 与 RCO_SPACE 两类 | 其他枚举返回空列表 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| type | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| type=RCC_CLASSROOM | $.content 非空 |
| type=RCO_SPACE 且存在关联桌面池 | $.content 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| type 缺失 | type 未传 | $.status==ERROR |
| RCO_SPACE 无关联资源 | 无子系统关联桌面池 | $.status==SUCCESS 且 $.content 为空 |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 只读查询，无副作用 |
