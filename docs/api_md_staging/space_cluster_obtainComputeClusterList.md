---
version: '2.0'
api:
  url: /space/cluster/obtainComputeClusterList
  method: POST
  name: 分页获取计算集群列表。从 matchArr 抽取 imageTemplateId/storagePoolId/networkId 数组，其余 match 保留后
  controller: SpaceClusterController
  method_ref: obtainComputeClusterList
  permission: 无
  exec_mode: 同步分页：计算集群分页 + 资源适配性检查回填 canUsed/canInstallDrive
  async: false
  description: 分页获取计算集群列表。从 matchArr 抽取 imageTemplateId/storagePoolId/networkId 数组，其余 match 保留后经 PlatformComputeClusterMgmtAPI.pageQuery 分页查询集群；再构造 ComputerClusterResourceAdaptCheckRequest（fromImage=false）调用 cluster
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: get_cluster
  api: POST /space/cluster/obtainComputeClusterList
  extract:
    clusterId: $.content.itemArr[0].computerClusterId
    platformId: $.content.itemArr[0].platformId
  purpose: 获取计算集群ID与云平台ID（取第一条，无名称过滤）
request:
  dto: PageQueryRequest（框架类，matchArr 支持 imageTemplateId/storagePoolId/networkId 特殊字段）
  body:
    page:
      type: Integer
      required: true
      constraint: 分页页码
      description: request.getPage()
    limit:
      type: Integer
      required: true
      constraint: 每页条数
      description: request.getLimit()
    matchArr[].fieldName=imageTemplateId:
      type: UUID[]
      required: false
      constraint: EXACT 匹配
      description: 镜像模板 id 数组，用于适配性检查
    matchArr[].fieldName=storagePoolId:
      type: UUID[]
      required: false
      constraint: EXACT 匹配
      description: 存储池 id 数组
    matchArr[].fieldName=networkId:
      type: UUID[]
      required: false
      constraint: EXACT 匹配
      description: 网络策略 id 数组
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
    itemArr:
      type: PlatformClusterInfoResponse[]
      description: 集群列表
    total:
      type: long
      description: 总条数
    id:
      type: UUID
      description: 集群 id
    computerClusterId:
      type: UUID
      description: 计算集群 id
    clusterName:
      type: String
      description: 集群名称
    clusterDesc:
      type: String
      description: 集群描述
    clusterState:
      type: CloudClusterStateEnums
      description: 集群状态
    totalCpu:
      type: long
      description: 总 CPU 核数
    usedCpu:
      type: long
      description: 已用 CPU 核数
    totalMemory:
      type: long
      description: 总内存 MB
    usedMemory:
      type: long
      description: 已用内存 MB
    architecture:
      type: String
      description: CPU 架构
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
    canUsed:
      type: Boolean
      description: 适配性检查是否可用（默认 true）
    canUsedMessage:
      type: String
      description: 不可用原因
    canInstallDrive:
      type: Boolean
      description: 是否可安装驱动（适配检查回填，默认 false）
    "itemArr[]_id":
      type: UUID
      description: 集群ID
    "itemArr[]_computerClusterId":
      type: UUID
      description: 计算集群ID
    "itemArr[]_clusterName":
      type: String
      description: 集群名称
    "itemArr[]_clusterDesc":
      type: String
      description: 集群描述
    "itemArr[]_clusterState":
      type: CloudClusterStateEnums
      description: 集群状态
    "itemArr[]_totalCpu":
      type: long
      description: 总CPU核数
    "itemArr[]_usedCpu":
      type: long
      description: 已用CPU核数
    "itemArr[]_totalMemory":
      type: long
      description: 总内存（MB）
    "itemArr[]_usedMemory":
      type: long
      description: 已用内存（MB）
    "itemArr[]_architecture":
      type: String
      description: CPU架构（x86_64、ARM）
    "itemArr[]_platformId":
      type: UUID
      description: 平台ID
    "itemArr[]_createTime":
      type: Date
      description: 创建时间
    "itemArr[]_updateTime":
      type: Date
      description: 更新时间
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
    "itemArr[]_archSet":
      type: Set<String>
      description: CPU架构集合
    "itemArr[]_canUsed":
      type: Boolean
      description: 适配性检查是否可用（默认true）
    "itemArr[]_canUsedMessage":
      type: String
      description: 不可用原因
    "itemArr[]_canInstallDrive":
      type: Boolean
      description: 是否可安装驱动（适配检查回填，默认false）
upstream:
- api: POST /rcc/space/image/list
  produces: $.content.itemArr[*].id
  purpose: 镜像模板ID筛选（可空），来源为镜像列表
- api: POST /space/storagePool/list
  produces: $.content.itemArr[*].id
  purpose: 存储池ID筛选（可空）
- api: POST /space/clouddesktop/deskNetwork/list
  produces: $.content.itemArr[*].id
  purpose: 网络ID筛选（可空）
downstream:
- api: POST /space/storagePool/list
  purpose: 选择集群后联动查询该集群可用存储池
- api: POST /space/clouddesktop/deskNetwork/list
  purpose: 选择集群后联动查询可用网络策略
- api: POST /space/deskStrategy/vgpu/list
  purpose: 携带选中集群 id 查询 VGPU 选项
constraints:
- level: BUSINESS
  field: 集群
  rule: 集群不满足镜像/存储池/网络适配条件时置为不可用
  failure: canUsed=false 并携带 canUsedMessage（接口不报错）
assertions:
  success:
  - scenario: 有集群且适配通过
    expect: $.content.itemArr 非空 且 $.content.itemArr[0].canUsed==true
  - scenario: 无集群数据
    expect: $.content.itemArr 为空
  - scenario: 集群资源不满足条件
    expect: $.content.itemArr[0].canUsed==false 且 $.content.itemArr[0].canUsedMessage 非空
  failure:
  - scenario: request 为 null
    trigger: 请求体缺失
    expect: $.status==ERROR
cleanup:
- api: 无
  note: 只读查询接口
idempotency:
  level: non_idempotent
  note: 只读查询，无副作用
---
# POST /space/cluster/obtainComputeClusterList

> 分页获取计算集群列表。从 matchArr 抽取 imageTemplateId/storagePoolId/networkId 数组，其余 match 保留后经 PlatformComputeClusterMgmtAPI.pageQuery 分页查询集群；再构造 ComputerClusterResourceAdaptCheckRequest（fromImage=false）调用 clusterResourceAdaptCheck 做资源适配性检查，将 canUsed/canUsedMessage/canInstallDrive 合并进 PlatformClusterInfoResponse 返回。 ｜ 无特殊权限 ｜ 同步分页：计算集群分页 + 资源适配性检查回填 canUsed/canInstallDrive

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/space/image/list"]
        A2["POST /space/storagePool/list"]
        A3["POST /space/clouddesktop/deskNetwork/list"]
    end
    B["POST /space/cluster/obtainComputeClusterList<br>分页获取计算集群列表。从 matchArr 抽取 imageTemplateId<br>权限: 无"]
    A1 -->|数据| B
    A2 -->|数据| B
    A3 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request)"]
        C2["Step2: 遍历 matchArr 抽取 imageTemplateId/storagePo"]
        C3["Step3: 构建分页请求，clusterAPI.pageQuery 查询集群"]
        C4["Step4: 结果为空 → 直接返回 success(pageResponse)"]
        C5["Step5: assembleRequest 构造 ComputerClusterResour"]
        C6["Step6: clusterAPI.clusterResourceAdaptCheck 执行适"]
        C1 --> C2
        C7["Step7: 逐条 BeanUtils 拷贝→PlatformClusterInfoRespo"]
        C8["Step8: 返回 success(PageQueryResponse<PlatformClu"]
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
| URL | /space/cluster/obtainComputeClusterList |
| Controller | SpaceClusterController |
| 方法名 | obtainComputeClusterList |
| 权限注解 | 无 |
| 执行方式 | 同步分页：计算集群分页 + 资源适配性检查回填 canUsed/canInstallDrive |
| 业务含义 | 分页获取计算集群列表。从 matchArr 抽取 imageTemplateId/storagePoolId/networkId 数组，其余 match 保留后经 PlatformComputeClusterMgmtAPI.pageQuery 分页查询集群；再构造 ComputerClusterResourceAdaptCheckRequest（fromImage=false）调用 clusterResourceAdaptCheck 做资源适配性检查，将 canUsed/canUsedMessage/canInstallDrive 合并进 PlatformClusterInfoResponse 返回。 |

## 入参详情

### PageQueryRequest（框架类，matchArr 支持 imageTemplateId/storagePoolId/networkId 特殊字段）

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| page | Integer | 是 | 分页页码 | request.getPage() |
| limit | Integer | 是 | 每页条数 | request.getLimit() |
| matchArr[].fieldName=imageTemplateId | UUID[] | 否 | EXACT 匹配 | 镜像模板 id 数组，用于适配性检查 |
| matchArr[].fieldName=storagePoolId | UUID[] | 否 | EXACT 匹配 | 存储池 id 数组 |
| matchArr[].fieldName=networkId | UUID[] | 否 | EXACT 匹配 | 网络策略 id 数组 |
| sortArr | Sort[] | 否 | 排序 | 透传 |

## 出参详情

| 返回类型 | DefaultWebResponse<PageQueryResponse<PlatformClusterInfoResponse>> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr | PlatformClusterInfoResponse[] | 集群列表（元素字段见下） |
| total | long | 总条数 |
| id | UUID | 集群ID |
| computerClusterId | UUID | 计算集群ID |
| clusterName | String | 集群名称 |
| clusterDesc | String | 集群描述 |
| clusterState | CloudClusterStateEnums | 集群状态 |
| totalCpu | long | 总CPU核数 |
| usedCpu | long | 已用CPU核数 |
| totalMemory | long | 总内存（MB） |
| usedMemory | long | 已用内存（MB） |
| architecture | String | CPU架构（x86_64、ARM） |
| platformId | UUID | 平台ID |
| createTime | Date | 创建时间 |
| updateTime | Date | 更新时间 |
| platformName | String | 云平台名称 |
| platformType | CloudPlatformType | 云平台类型 |
| platformStatus | CloudPlatformStatus | 云平台状态 |
| cloudPlatformId | String | 云平台唯一标识 |
| archSet | Set<String> | CPU架构集合 |
| canUsed | Boolean | 适配性检查是否可用（默认true） |
| canUsedMessage | String | 不可用原因 |
| canInstallDrive | Boolean | 是否可安装驱动（适配检查回填，默认false） |

## 上游前置业务

### 前置1：POST /rcc/space/image/list

镜像模板ID筛选（可空），来源为镜像列表（由 field_map 契约映射）

### 前置2：POST /space/storagePool/list

存储池ID筛选（可空）（由 field_map 契约映射）

### 前置3：POST /space/clouddesktop/deskNetwork/list

网络ID筛选（可空）（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull(request)
2. 遍历 matchArr 抽取 imageTemplateId/storagePoolId/networkId，其余 match 保留
3. 构建分页请求，clusterAPI.pageQuery 查询集群
4. 结果为空 → 直接返回 success(pageResponse)
5. assembleRequest 构造 ComputerClusterResourceAdaptCheckRequest（fromImage=false，携带 clusterList）
6. clusterAPI.clusterResourceAdaptCheck 执行适配检查，结果转 Map<clusterId, result>
7. 逐条 BeanUtils 拷贝→PlatformClusterInfoResponse，合并 canUsed/canUsedMessage/canInstallDrive
8. 返回 success(PageQueryResponse<PlatformClusterInfoResponse>)

## 下游消费方

### 消费1：POST /space/cluster/obtainComputeClusterList

计算集群ID，被 /space/deskStrategy/vgpu/list、getClusterSupportEnablePersonalConfig、策略 condition/list 消费（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| BUSINESS | 集群 | 集群不满足镜像/存储池/网络适配条件时置为不可用 | canUsed=false 并携带 canUsedMessage（接口不报错） |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| page | user_input/from_query | 按业务构造 |
| limit | user_input/from_query | 按业务构造 |
| matchArr[].fieldName=imageTemplateId | user_input/from_query | 按业务构造 |
| matchArr[].fieldName=storagePoolId | user_input/from_query | 按业务构造 |
| matchArr[].fieldName=networkId | user_input/from_query | 按业务构造 |
| sortArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 有集群且适配通过 | $.content.itemArr 非空 且 $.content.itemArr[0].canUsed==true |
| 无集群数据 | $.content.itemArr 为空 |
| 集群资源不满足条件 | $.content.itemArr[0].canUsed==false 且 $.content.itemArr[0].canUsedMessage 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| request 为 null | 请求体缺失 | $.status==ERROR |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 无 | 只读查询接口 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 只读查询，无副作用 |
