---
version: '2.0'
api:
  url: /space/storagePool/list
  method: POST
  name: 分页查询存储池列表并做可用性过滤。从 matchArr 抽取 imageTemplateId/clusterId/networkId/hasNotAllowRe
  controller: SpaceStoragePoolController
  method_ref: listStoragePool
  permission: 无
  exec_mode: 同步分页：存储池分页 + 集群/镜像/冗余策略多重可用性过滤
  async: false
  description: 分页查询存储池列表并做可用性过滤。从 matchArr 抽取 imageTemplateId/clusterId/networkId/hasNotAllowRedundancyRAID1，经 storagePoolServerMgmtAPI.pageQuery 分页查询；对每个存储池按类型（SAMBA 不支持、外置存储不支持、SAN 与非 SAN 混布限制）、关联集群、镜像模板 CPU 架构、单版
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
request:
  dto: PageQueryRequest（框架类，matchArr 支持 imageTemplateId/clusterId/networkId/hasNotAllowRedundancyRAID1 特殊字段）
  body:
    page:
      type: Integer
      required: true
      constraint: 分页页码
      description: pageQueryRequest.getPage()
    limit:
      type: Integer
      required: true
      constraint: 每页条数
      description: pageQueryRequest.getLimit()
    matchArr[].fieldName=imageTemplateId:
      type: UUID[]
      required: false
      constraint: EXACT
      description: 镜像模板 id 数组，校验镜像-存储池兼容性
    matchArr[].fieldName=clusterId:
      type: UUID[]
      required: false
      constraint: EXACT
      description: 计算集群 id 数组，仅返回关联这些集群的存储池
    matchArr[].fieldName=networkId:
      type: UUID[]
      required: false
      constraint: EXACT
      description: 网络策略 id 数组（当前仅抽取不参与过滤）
    matchArr[].fieldName=hasNotAllowRedundancyRAID1:
      type: Boolean
      required: false
      constraint: EXACT
      description: true 时 RAID1_1D0B 冗余策略存储池不可用（浮动个性盘限制）
    sortArr:
      type: Sort[]
      required: false
      constraint: 排序
      description: 透传
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    total:
      type: long
      description: 总条数
    id:
      type: UUID
      description: 存储池 id
    storagePoolId:
      type: UUID
      description: 存储池 id（storagePoolId）
    name:
      type: String
      description: 存储池名称
    storagePoolType:
      type: StoragePoolType
      description: 存储池类型（POS/SAN/SAMBA/RG_PDS 等）
    redundancyStrategy:
      type: RedundancyStrategy
      description: 冗余策略（RAID0/RAID1 等）
    totalCapacity:
      type: Long
      description: 总容量
    usedCapacity:
      type: Long
      description: 已用容量
    storagePoolMgmtState:
      type: enum
      description: 存储池管理状态
    storagePoolHealthState:
      type: enum
      description: 存储池健康状态
    platformId:
      type: UUID
      description: 所属平台ID
    platformName:
      type: String
      description: 所属平台名称
    platformType:
      type: String
      description: 所属平台类型
    platformStatus:
      type: String
      description: 所属平台状态
    storageClusterId:
      type: UUID
      description: 存储集群 id
    canUsed:
      type: Boolean
      description: 是否可用（默认 true）
    useInLocalDisk:
      type: Boolean
      description: 是否可用于本地磁盘（默认 true；SAN 环境非 SAN 存储置 false）
    canUsedMessage:
      type: String
      description: 不可用原因
    itemArr:
      type: StoragePoolDetailResponse[]
      description: 存储池详情列表
    "itemArr[]_id":
      type: UUID
      description: 存储池ID
    "itemArr[]_storagePoolId":
      type: UUID
      description: 存储池ID（业务侧）
    "itemArr[]_name":
      type: String
      description: 存储池名称
    "itemArr[]_storagePoolType":
      type: StoragePoolType
      description: 存储池类型（POS/SAN/SAMBA/RG_PDS 等）
    "itemArr[]_redundancyStrategy":
      type: RedundancyStrategy
      description: 冗余策略（RAID0/RAID1 等）
    "itemArr[]_totalCapacity":
      type: Long
      description: 总容量
    "itemArr[]_usedCapacity":
      type: Long
      description: 已用容量
    "itemArr[]_storagePoolMgmtState":
      type: StoragePoolMgmtState
      description: 存储池管理状态
    "itemArr[]_storagePoolHealthState":
      type: StoragePoolHealthState
      description: 存储池健康状态
    "itemArr[]_description":
      type: String
      description: 存储池描述
    "itemArr[]_createTime":
      type: Date
      description: 创建时间
    "itemArr[]_updateTime":
      type: Date
      description: 更新时间
    "itemArr[]_storageClusterId":
      type: UUID
      description: 存储集群ID
    "itemArr[]_platformId":
      type: UUID
      description: 平台ID
    "itemArr[]_platformName":
      type: String
      description: 云平台名称
    "itemArr[]_platformType":
      type: CloudPlatformType
      description: 云平台类型
    "itemArr[]_platformStatus":
      type: CloudPlatformStatus
      description: 云平台状态
    "itemArr[]_cloudPlatformId":
      type: String
      description: 云平台唯一标识
    "itemArr[]_options":
      type: StoragePoolOptionsDTO
      description: 存储扩展参数
    "itemArr[]_canUsed":
      type: Boolean
      description: 是否可用（默认true）
    "itemArr[]_useInLocalDisk":
      type: Boolean
      description: 是否可用于本地磁盘（默认true；SAN 环境非 SAN 存储置 false）
    "itemArr[]_canUsedMessage":
      type: String
      description: 不可用原因
upstream:
- api: POST /space/cluster/obtainComputeClusterList
  produces: $.content.itemArr[*].id
  purpose: 计算集群ID筛选（可空），来源为集群列表
downstream:
- api: POST /space/cluster/obtainComputeClusterList
  purpose: 选择存储池后联动刷新集群可用性
- api: POST /space/strategygroup/vdi/create
  purpose: 创建课程策略时选择系统盘存储池
constraints:
- level: BUSINESS
  field: storagePoolType
  rule: SAMBA 类型不支持
  failure: canUsed=false（RCDC_RCC_STORAGE_POOL_SAMBA_TYPE_NOT_SUPPORT）
- level: BUSINESS
  field: storagePoolType
  rule: 外置存储类型不支持
  failure: canUsed=false（RCDC_RCC_STORAGE_POOL_EXTERNAL_TYPE_NOT_SUPPOR
- level: BUSINESS
  field: storagePoolType
  rule: 默认存储为 SAN 时非 SAN 存储不用于本地磁盘
  failure: useInLocalDisk=false（RCDC_RCC_STORAGE_POOL_POS_TYPE_NOT_SUPP
- level: BUSINESS
  field: redundancyStrategy
  rule: hasNotAllowRedundancyRAID1=true 时 RAID1_1D0B 不可用
  failure: canUsed=false（RCDC_RCC_STORAGE_POOL_LIMIT_RAID1）
- level: BUSINESS
  field: clusterId
  rule: 存储池必须关联所选集群
  failure: canUsed=false（RCDC_RCC_STORAGE_NOT_CLUSTER，携带集群名）
- level: BUSINESS
  field: imageTemplateId
  rule: 单版本镜像与存储池平台/存储位置/类型一致
  failure: canUsed=false（RCDC_RCC_STORAGE_POOL_CLUSTER_NOT_SUPPORT_SELE
assertions:
  success:
  - scenario: 存储池全部兼容
    expect: $.content.itemArr 非空
  - scenario: 存在不可用存储池
    expect: $.content.itemArr 非空 且 itemArr 中存在 canUsed==false 的记录
  failure:
  - scenario: pageQueryRequest 为 null
    trigger: 请求体缺失
    expect: $.status==ERROR
cleanup:
- api: 无
  note: 只读查询接口
idempotency:
  level: non_idempotent
  note: 只读查询，无副作用
---
# POST /space/storagePool/list

> 分页查询存储池列表并做可用性过滤。从 matchArr 抽取 imageTemplateId/clusterId/networkId/hasNotAllowRedundancyRAID1，经 storagePoolServerMgmtAPI.pageQuery 分页查询；对每个存储池按类型（SAMBA 不支持、外置存储不支持、SAN 与非 SAN 混布限制）、关联集群、镜像模板 CPU 架构、单版本镜像跨平台/外置/类型不一致等规则计算 canUsed/canUsedMessage；若 hasNotAllowRedundancyRAID1=true 则将 RAID1_1D0B 冗余策略存储池置为不可用。 ｜ 无特殊权限 ｜ 同步分页：存储池分页 + 集群/镜像/冗余策略多重可用性过滤

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /space/cluster/obtainComputeClusterList"]
    end
    B["POST /space/storagePool/list<br>分页查询存储池列表并做可用性过滤。从 matchArr 抽取 imageTemp<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(pageQueryRequest)"]
        C2["Step2: 遍历 matchArr 抽取 imageTemplateId/clusterId"]
        C3["Step3: 构建分页请求，storagePoolServerMgmtAPI.pageQuer"]
        C4["Step4: 结果为空 → 返回 success(空 items)"]
        C5["Step5: getStoragePoolByIds：queryAllClusterInfoL"]
        C6["Step6: 逐条处理：SAMBA 类型→canUsed=false；外置存储→canUsed"]
        C1 --> C2
        C7["Step7: dealWithRedundancyStrategy：hasNotAllowRe"]
        C8["Step8: 返回 success(PageResponse<StoragePoolDetai"]
        C6 --> C7
        C7 --> C8
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
| URL | /space/storagePool/list |
| Controller | SpaceStoragePoolController |
| 方法名 | listStoragePool |
| 权限注解 | 无 |
| 执行方式 | 同步分页：存储池分页 + 集群/镜像/冗余策略多重可用性过滤 |
| 业务含义 | 分页查询存储池列表并做可用性过滤。从 matchArr 抽取 imageTemplateId/clusterId/networkId/hasNotAllowRedundancyRAID1，经 storagePoolServerMgmtAPI.pageQuery 分页查询；对每个存储池按类型（SAMBA 不支持、外置存储不支持、SAN 与非 SAN 混布限制）、关联集群、镜像模板 CPU 架构、单版本镜像跨平台/外置/类型不一致等规则计算 canUsed/canUsedMessage；若 hasNotAllowRedundancyRAID1=true 则将 RAID1_1D0B 冗余策略存储池置为不可用。 |

## 入参详情

### PageQueryRequest（框架类，matchArr 支持 imageTemplateId/clusterId/networkId/hasNotAllowRedundancyRAID1 特殊字段）

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| page | Integer | 是 | 分页页码 | pageQueryRequest.getPage() |
| limit | Integer | 是 | 每页条数 | pageQueryRequest.getLimit() |
| matchArr[].fieldName=imageTemplateId | UUID[] | 否 | EXACT | 镜像模板 id 数组，校验镜像-存储池兼容性 |
| matchArr[].fieldName=clusterId | UUID[] | 否 | EXACT | 计算集群 id 数组，仅返回关联这些集群的存储池 |
| matchArr[].fieldName=networkId | UUID[] | 否 | EXACT | 网络策略 id 数组（当前仅抽取不参与过滤） |
| matchArr[].fieldName=hasNotAllowRedundancyRAID1 | Boolean | 否 | EXACT | true 时 RAID1_1D0B 冗余策略存储池不可用（浮动个性盘限制） |
| sortArr | Sort[] | 否 | 排序 | 透传 |

## 出参详情

| 返回类型 | DefaultWebResponse<PageResponse<StoragePoolDetailResponse>> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr | StoragePoolDetailResponse[] | 存储池详情列表（元素字段见下） |
| total | long | 总条数 |
| id | UUID | 存储池ID |
| storagePoolId | UUID | 存储池ID（业务侧） |
| name | String | 存储池名称 |
| storagePoolType | StoragePoolType | 存储池类型（POS/SAN/SAMBA/RG_PDS 等） |
| redundancyStrategy | RedundancyStrategy | 冗余策略（RAID0/RAID1 等） |
| totalCapacity | Long | 总容量 |
| usedCapacity | Long | 已用容量 |
| storagePoolMgmtState | StoragePoolMgmtState | 存储池管理状态 |
| storagePoolHealthState | StoragePoolHealthState | 存储池健康状态 |
| description | String | 存储池描述 |
| createTime | Date | 创建时间 |
| updateTime | Date | 更新时间 |
| storageClusterId | UUID | 存储集群ID |
| platformId | UUID | 平台ID |
| platformName | String | 云平台名称 |
| platformType | CloudPlatformType | 云平台类型 |
| platformStatus | CloudPlatformStatus | 云平台状态 |
| cloudPlatformId | String | 云平台唯一标识 |
| options | StoragePoolOptionsDTO | 存储扩展参数 |
| canUsed | Boolean | 是否可用（默认true） |
| useInLocalDisk | Boolean | 是否可用于本地磁盘（默认true；SAN 环境非 SAN 存储置 false） |
| canUsedMessage | String | 不可用原因 |

## 上游前置业务

### 前置1：POST /space/cluster/obtainComputeClusterList

计算集群ID筛选（可空），来源为集群列表（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull(pageQueryRequest)
2. 遍历 matchArr 抽取 imageTemplateId/clusterId/networkId/hasNotAllowRedundancyRAID1，其余 match 保留
3. 构建分页请求，storagePoolServerMgmtAPI.pageQuery 查询存储池分页
4. 结果为空 → 返回 success(空 items)
5. getStoragePoolByIds：queryAllClusterInfoList 建集群 map；storageRelatedMapByStoragePoolIdList 取存储池-集群关联；mapImageTemplateByIdList 取镜像详情；getDefaultStoragePoolDetail 判 SAN
6. 逐条处理：SAMBA 类型→canUsed=false；外置存储→canUsed=false；SAN 环境非 SAN 存储→useInLocalDisk=false；有镜像筛选时校验单版本镜像跨平台/外置/类型与 CPU 架构；有集群筛选时校验存储池是否关联所选集群
7. dealWithRedundancyStrategy：hasNotAllowRedundancyRAID1=true 时 RAID1_1D0B → canUsed=false
8. 返回 success(PageResponse<StoragePoolDetailResponse>)

## 下游消费方

### 消费1：POST /space/storagePool/list

存储池ID，被空间编辑存储池配置消费（推断字段名 id/storagePoolId）（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| BUSINESS | storagePoolType | SAMBA 类型不支持 | canUsed=false（RCDC_RCC_STORAGE_POOL_SAMBA_TYPE_NOT_SUPPORT） |
| BUSINESS | storagePoolType | 外置存储类型不支持 | canUsed=false（RCDC_RCC_STORAGE_POOL_EXTERNAL_TYPE_NOT_SUPPORT） |
| BUSINESS | storagePoolType | 默认存储为 SAN 时非 SAN 存储不用于本地磁盘 | useInLocalDisk=false（RCDC_RCC_STORAGE_POOL_POS_TYPE_NOT_SUPPORT） |
| BUSINESS | redundancyStrategy | hasNotAllowRedundancyRAID1=true 时 RAID1_1D0B 不可用 | canUsed=false（RCDC_RCC_STORAGE_POOL_LIMIT_RAID1） |
| BUSINESS | clusterId | 存储池必须关联所选集群 | canUsed=false（RCDC_RCC_STORAGE_NOT_CLUSTER，携带集群名） |
| BUSINESS | imageTemplateId | 单版本镜像与存储池平台/存储位置/类型一致 | canUsed=false（RCDC_RCC_STORAGE_POOL_CLUSTER_NOT_SUPPORT_SELECT） |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| page | user_input/from_query | 按业务构造 |
| limit | user_input/from_query | 按业务构造 |
| matchArr[].fieldName=imageTemplateId | user_input/from_query | 按业务构造 |
| matchArr[].fieldName=clusterId | user_input/from_query | 按业务构造 |
| matchArr[].fieldName=networkId | user_input/from_query | 按业务构造 |
| matchArr[].fieldName=hasNotAllowRedundancyRAID1 | user_input/from_query | 按业务构造 |
| sortArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 存储池全部兼容 | $.content.itemArr 非空 |
| 存在不可用存储池 | $.content.itemArr 非空 且 itemArr 中存在 canUsed==false 的记录 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| pageQueryRequest 为 null | 请求体缺失 | $.status==ERROR |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 无 | 只读查询接口 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 只读查询，无副作用 |
