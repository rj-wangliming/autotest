---
version: '2.0'
api:
  url: /rcc/space/image/list
  method: POST
  name: 分页查询镜像模板（过滤掉已发布到教室的课堂镜像）。流程：rccSpacePoolWebHelper.covert 将请求转 LocalImageTemplate
  controller: RccSpaceController
  method_ref: listImageTemplate
  permission: 无
  exec_mode: 同步
  async: false
  description: 分页查询镜像模板（过滤掉已发布到教室的课堂镜像）。流程：rccSpacePoolWebHelper.covert 将请求转 LocalImageTemplatePageRequest；classroomImageAPI.findAllClassroomImage 查出教室已发布镜像并从结果排除；超管（isAllGroupPermission）用 listAllImageTemplate 全量镜像剔
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
request:
  dto: RccSpaceListImageWebRequest
  body:
    page:
      type: Integer
      required: true
      constraint: '@NotNull @Range(0-2147483647)'
      description: 页码，默认0
    limit:
      type: Integer
      required: true
      constraint: '@NotNull @Range(1-2147483647)'
      description: 每页条数，默认1
    searchKeyword:
      type: String
      required: false
      constraint: '@Nullable'
      description: 搜索关键字
    noPermission:
      type: Boolean
      required: false
      constraint: '@Nullable'
      description: 是否不需要数据权限（管理员管理侧放行）
    exactMatchArr:
      type: ExactMatch[]
      required: false
      constraint: '@Nullable'
      description: 精确匹配条件（支持 imageRoleType 等）
    sortArr:
      type: Sort[]
      required: false
      constraint: '@Nullable'
      description: 排序条件
    customMatchArr:
      type: Match[]
      required: false
      constraint: '@Nullable'
      description: 自定义匹配条件（保留 CompositeMatch）
    customData:
      type: String
      required: false
      constraint: '@Nullable'
      description: 扩展透传数据
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    itemArr:
      type: CbbImageTemplateDetailDTO[]
      description: 镜像模板分页记录（位于 content 下：$.content.itemArr）
    total:
      type: Integer
      description: 总记录数（$.content.total）
    itemArr[]_id:
      type: UUID
      description: 镜像模板ID
    itemArr[]_cpu:
      type: Integer
      description: CPU核数
    itemArr[]_memory:
      type: Integer
      description: 内存（GB）
    itemArr[]_systemDisk:
      type: Integer
      description: 系统盘大小（GB）
    itemArr[]_network:
      type: CbbImageTemplateNetworkDTO
      description: 镜像模板网络
    itemArr[]_imageName:
      type: String
      description: 镜像名称
    itemArr[]_imageFileName:
      type: String
      description: 镜像文件名
    itemArr[]_note:
      type: String
      description: 备注
    itemArr[]_osType:
      type: CbbOsType
      description: 操作系统类型
    itemArr[]_imageState:
      type: ImageTemplateState
      description: 镜像状态
    itemArr[]_cbbImageType:
      type: CbbImageType
      description: 镜像类型
    itemArr[]_tempVmId:
      type: UUID
      description: 临时虚拟机ID
    itemArr[]_tempVmIp:
      type: String
      description: 临时虚拟机IP
    itemArr[]_vmPhysicsServerId:
      type: UUID
      description: 虚拟机物理服务器ID
    itemArr[]_imageSystemSize:
      type: Integer
      description: 镜像系统盘大小
    itemArr[]_clouldDeskopNumOfRecoverable:
      type: Integer
      description: 还原桌面数
    itemArr[]_clouldDeskopNumOfPersonal:
      type: Integer
      description: 个性化桌面数
    itemArr[]_clouldDeskopNumOfAppLayer:
      type: Integer
      description: 应用分层桌面数
    itemArr[]_clouldDeskopNumOfFullCloneRecoverable:
      type: Integer
      description: 全克隆还原桌面数
    itemArr[]_clouldDeskopNumOfFullClonePersonal:
      type: Integer
      description: 全克隆个性化桌面数
    itemArr[]_clouldDeskopNumOfFullCloneAppLayer:
      type: Integer
      description: 全克隆应用分层桌面数
    itemArr[]_editErrorMessage:
      type: String
      description: 编辑错误信息
    itemArr[]_editErrorMessageKey:
      type: String
      description: 编辑错误信息Key
    itemArr[]_supportGoldenImage:
      type: Boolean
      description: 是否支持黄金镜像
    itemArr[]_canUsed:
      type: Boolean
      description: 是否可用
    itemArr[]_canUsedMessage:
      type: String
      description: 不可用原因
    itemArr[]_vmState:
      type: ExternalImageVmState
      description: 虚拟机状态
    itemArr[]_guesttoolState:
      type: ImageTemplateGuestToolState
      description: GuestTool状态
    itemArr[]_canEditSystemDiskSize:
      type: Boolean
      description: 是否可编辑系统盘大小
    itemArr[]_terminalId:
      type: String
      description: 终端ID
    itemArr[]_enableNested:
      type: Boolean
      description: 是否启用嵌套虚拟化
    itemArr[]_enableSoftwareDecode:
      type: Boolean
      description: 是否启用软件解码
    itemArr[]_imageVmHost:
      type: ImageVmHost
      description: 镜像虚拟机宿主机
    itemArr[]_vgpuInfoDTO:
      type: VgpuInfoDTO
      description: vGPU信息
    itemArr[]_vgpuInfoDTOHistoryList:
      type: List<VgpuInfoDTO>
      description: vGPU历史信息列表
    itemArr[]_loaderPatitionNumber:
      type: Integer
      description: 加载器分区数
    itemArr[]_loaderPath:
      type: String
      description: 加载器路径
    itemArr[]_partType:
      type: PartType
      description: 分区类型
    itemArr[]_ftpUploadState:
      type: FtpUploadState
      description: FTP上传状态
    itemArr[]_controlState:
      type: ControlStateEnum
      description: 控制状态
    itemArr[]_imageDiskList:
      type: List<CbbImageDiskInfoDTO>
      description: 镜像磁盘列表
    itemArr[]_createTime:
      type: Date
      description: 创建时间
    itemArr[]_lastEditTime:
      type: Date
      description: 最后编辑时间
    itemArr[]_guestToolVersion:
      type: String
      description: GuestTool版本
    itemArr[]_lastRecoveryPointId:
      type: UUID
      description: 最后还原点ID
    itemArr[]_hasInstallScsiController:
      type: Boolean
      description: 是否安装SCSI控制器
    itemArr[]_storageDriverVersion:
      type: String
      description: 存储驱动版本
    itemArr[]_beforeStorageDriverVersion:
      type: String
      description: 编辑前存储驱动版本
    itemArr[]_enableVirtualEmulation:
      type: Boolean
      description: 是否启用虚拟化仿真
    itemArr[]_beforeEditEnableVirtualEmulation:
      type: Boolean
      description: 编辑前是否启用虚拟化仿真
    itemArr[]_vmSystemDiskSn:
      type: String
      description: 虚拟机系统盘序列号
    itemArr[]_remoteTerminalImageEditState:
      type: CbbRemoteTerminalImageEditEnum
      description: 远程终端镜像编辑状态
    itemArr[]_editUploadDownloadPercentage:
      type: String
      description: 编辑上传下载进度百分比
    itemArr[]_createMode:
      type: CbbImageTemplateCreateMode
      description: 镜像创建模式
    itemArr[]_isAd:
      type: Boolean
      description: 是否AD域
    itemArr[]_computerName:
      type: String
      description: 计算机名
    itemArr[]_imageUsage:
      type: ImageUsageTypeEnum
      description: 镜像用途
    itemArr[]_terminalImageDownloadProgressInfo:
      type: CbbTerminalImageDownloadProgressDTO
      description: 终端镜像下载进度
    itemArr[]_totalImageFileSize:
      type: Integer
      description: 镜像文件总大小
    itemArr[]_clusterInfo:
      type: ClusterInfoDTO
      description: 集群信息
    itemArr[]_storagePool:
      type: PlatformStoragePoolDTO
      description: 存储池信息
    itemArr[]_enableUamAgent:
      type: Boolean
      description: 是否启用UAM代理
    itemArr[]_vmClusterId:
      type: UUID
      description: 虚拟机集群ID
    itemArr[]_vmStoragePoolId:
      type: UUID
      description: 虚拟机存储池ID
    itemArr[]_cbbImageFormat:
      type: ImageFormat
      description: 镜像格式
    itemArr[]_editErrorMessageList:
      type: List<String>
      description: 编辑错误信息列表
    itemArr[]_imageDriverList:
      type: List<DriverWithImageDTO>
      description: 镜像驱动列表
    itemArr[]_hasImportDriverPackage:
      type: Boolean
      description: 是否导入驱动包
    itemArr[]_isGlobalImage:
      type: Boolean
      description: 是否全局镜像
    itemArr[]_enableGlobalImage:
      type: Boolean
      description: 是否启用全局镜像
    itemArr[]_osIsoFileId:
      type: UUID
      description: 操作系统ISO文件ID
    itemArr[]_osVersion:
      type: String
      description: 操作系统版本
    itemArr[]_enableMultipleVersion:
      type: Boolean
      description: 是否启用多版本
    itemArr[]_isNewestVersion:
      type: Boolean
      description: 是否最新版本
    itemArr[]_rootImageId:
      type: UUID
      description: 根镜像ID
    itemArr[]_rootImageName:
      type: String
      description: 根镜像名称
    itemArr[]_sourceSnapshotId:
      type: UUID
      description: 源快照ID
    itemArr[]_imageRoleType:
      type: ImageRoleType
      description: 镜像角色类型
    itemArr[]_terminalLocalEditType:
      type: ImageTerminalLocalEditType
      description: 终端本地编辑类型
    itemArr[]_diskController:
      type: String
      description: 磁盘控制器
    itemArr[]_cpuArch:
      type: CbbCpuArchType
      description: CPU架构
    itemArr[]_enableDesktopUpgrade:
      type: Boolean
      description: 是否启用桌面升级
    itemArr[]_baseFileSize:
      type: Long
      description: 基础文件大小
    itemArr[]_diff1FileSize:
      type: Long
      description: 差异文件1大小
    itemArr[]_diff2FileSize:
      type: Long
      description: 差异文件2大小
    itemArr[]_publishedSlimmingVersion:
      type: Integer
      description: 已发布瘦身版本
    itemArr[]_currentSlimmingVersion:
      type: Integer
      description: 当前瘦身版本
    itemArr[]_hasImageSlimming:
      type: Boolean
      description: 是否已镜像瘦身
    itemArr[]_slimFlag:
      type: Integer
      description: 瘦身标记
    itemArr[]_platformId:
      type: UUID
      description: 云平台ID（父类）
    itemArr[]_platformType:
      type: CloudPlatformType
      description: 云平台类型（父类）
    itemArr[]_platformName:
      type: String
      description: 云平台名称（父类）
    itemArr[]_platformStatus:
      type: CloudPlatformStatus
      description: 云平台状态（父类）
upstream:
- api: 内部调用:rcc/RccSpacePoolWebHelper
  purpose: 请求转换分页查询对象
- api: 内部调用:rcc/ClassroomImageAPI
  purpose: 查询教室已发布镜像用于排除
- api: 内部调用:pa/PlatformImageTemplateMgmtAPI
  purpose: 超管查询全量镜像
- api: 内部调用:pa/PlatformAdminDataPermissionAPI
  purpose: 非超管查询有数据权限的镜像ID
downstream:
- api: 内部调用:pa/PlatformImageTemplateMgmtAPI#pageQueryLocalPageImageTemplate
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: sessionContext/webRequest
  rule: 不能为 null
  failure: Assert 失败
- level: PARAM
  field: page/limit
  rule: '@NotNull @Range 校验'
  failure: 越界校验失败
- level: BUSINESS
  field: imageId
  rule: 教室已发布镜像不展示；非超管仅展示权限内镜像
  failure: 无权限时返回空列表
assertions:
  success:
  - scenario: 超管查询镜像列表
    expect: $.content.itemArr 非空
  - scenario: 非超管带权限查询
    expect: $.content.itemArr 非空
  - scenario: 多版本镜像（imageRoleType=VERSION）
    expect: $.content.itemArr 非空
  failure:
  - scenario: 非超管无镜像权限
    trigger: 管理员无镜像数据权限
    expect: $.status==SUCCESS 且 $.content.itemArr 为空
  - scenario: 入参为 null
    trigger: webRequest 缺省
    expect: $.status==ERROR
cleanup: []
idempotency:
  level: non_idempotent
  note: 只读分页查询，无副作用
---
# POST /rcc/space/image/list

> 分页查询镜像模板（过滤掉已发布到教室的课堂镜像）。流程：rccSpacePoolWebHelper.covert 将请求转 LocalImageTemplatePageRequest；classroomImageAPI.findAllClassroomImage 查出教室已发布镜像并从结果排除；超管（isAllGroupPermission）用 listAllImageTemplate 全量镜像剔除已发布后按 id 过滤；非超管经 adminDataPermissionAPI.listImageIdByAdminId 获取权限镜像（无权限直接返回空），并按 exactMatch 中 imageRoleType 是否为 VERSION 决定按 rootImageId 或 id 过滤；最后 cbbImageTemplateMgmtAPI.pageQueryLocalPageImageTemplate 分页返回。 ｜ 无特殊权限 ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/space/image/list<br>分页查询镜像模板（过滤掉已发布到教室的课堂镜像）。流程：rccSpacePool<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(sessionContext/webRequest"]
        C2["Step2: rccSpacePoolWebHelper.covert(webRequest)"]
        C3["Step3: classroomImageAPI.findAllClassroomImage("]
        C4["Step4: 超管：listAllImageTemplate 全量镜像剔除已发布镜像ID，ap"]
        C5["Step5: 非超管：listImageIdByAdminId 获取权限镜像ID并剔除已发布；"]
        C6["Step6: cbbImageTemplateMgmtAPI.pageQueryLocalPa"]
        C1 --> C2
        C7["Step7: 返回 DefaultWebResponse.success(response)"]
        C6 --> C7
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
| URL | /rcc/space/image/list |
| Controller | RccSpaceController |
| 方法名 | listImageTemplate |
| 权限注解 | 无 |
| 执行方式 | 同步 |
| 业务含义 | 分页查询镜像模板（过滤掉已发布到教室的课堂镜像）。流程：rccSpacePoolWebHelper.covert 将请求转 LocalImageTemplatePageRequest；classroomImageAPI.findAllClassroomImage 查出教室已发布镜像并从结果排除；超管（isAllGroupPermission）用 listAllImageTemplate 全量镜像剔除已发布后按 id 过滤；非超管经 adminDataPermissionAPI.listImageIdByAdminId 获取权限镜像（无权限直接返回空），并按 exactMatch 中 imageRoleType 是否为 VERSION 决定按 rootImageId 或 id 过滤；最后 cbbImageTemplateMgmtAPI.pageQueryLocalPageImageTemplate 分页返回。 |

## 入参详情

### RccSpaceListImageWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| page | Integer | 是 | @NotNull @Range(0-2147483647) | 页码，默认0 |
| limit | Integer | 是 | @NotNull @Range(1-2147483647) | 每页条数，默认1 |
| searchKeyword | String | 否 | @Nullable | 搜索关键字 |
| noPermission | Boolean | 否 | @Nullable | 是否不需要数据权限（管理员管理侧放行） |
| exactMatchArr | ExactMatch[] | 否 | @Nullable | 精确匹配条件（支持 imageRoleType 等） |
| sortArr | Sort[] | 否 | @Nullable | 排序条件 |
| customMatchArr | Match[] | 否 | @Nullable | 自定义匹配条件（保留 CompositeMatch） |
| customData | String | 否 | @Nullable | 扩展透传数据 |

## 出参详情

| 返回类型 | DefaultWebResponse（content=DefaultPageResponse<CbbImageTemplateDetailDTO>） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr | CbbImageTemplateDetailDTO[] | 镜像模板分页记录（位于 content 下：$.content.itemArr） |
| total | Integer | 总记录数（$.content.total） |
| itemArr[].id | UUID | 镜像模板ID |
| itemArr[].cpu | Integer | CPU核数 |
| itemArr[].memory | Integer | 内存（GB） |
| itemArr[].systemDisk | Integer | 系统盘大小（GB） |
| itemArr[].network | CbbImageTemplateNetworkDTO | 镜像模板网络 |
| itemArr[].imageName | String | 镜像名称 |
| itemArr[].imageFileName | String | 镜像文件名 |
| itemArr[].note | String | 备注 |
| itemArr[].osType | CbbOsType | 操作系统类型 |
| itemArr[].imageState | ImageTemplateState | 镜像状态 |
| itemArr[].cbbImageType | CbbImageType | 镜像类型 |
| itemArr[].tempVmId | UUID | 临时虚拟机ID |
| itemArr[].tempVmIp | String | 临时虚拟机IP |
| itemArr[].vmPhysicsServerId | UUID | 虚拟机物理服务器ID |
| itemArr[].imageSystemSize | Integer | 镜像系统盘大小 |
| itemArr[].clouldDeskopNumOfRecoverable | Integer | 还原桌面数 |
| itemArr[].clouldDeskopNumOfPersonal | Integer | 个性化桌面数 |
| itemArr[].clouldDeskopNumOfAppLayer | Integer | 应用分层桌面数 |
| itemArr[].clouldDeskopNumOfFullCloneRecoverable | Integer | 全克隆还原桌面数 |
| itemArr[].clouldDeskopNumOfFullClonePersonal | Integer | 全克隆个性化桌面数 |
| itemArr[].clouldDeskopNumOfFullCloneAppLayer | Integer | 全克隆应用分层桌面数 |
| itemArr[].editErrorMessage | String | 编辑错误信息 |
| itemArr[].editErrorMessageKey | String | 编辑错误信息Key |
| itemArr[].supportGoldenImage | Boolean | 是否支持黄金镜像 |
| itemArr[].canUsed | Boolean | 是否可用 |
| itemArr[].canUsedMessage | String | 不可用原因 |
| itemArr[].vmState | ExternalImageVmState | 虚拟机状态 |
| itemArr[].guesttoolState | ImageTemplateGuestToolState | GuestTool状态 |
| itemArr[].canEditSystemDiskSize | Boolean | 是否可编辑系统盘大小 |
| itemArr[].terminalId | String | 终端ID |
| itemArr[].enableNested | Boolean | 是否启用嵌套虚拟化 |
| itemArr[].enableSoftwareDecode | Boolean | 是否启用软件解码 |
| itemArr[].imageVmHost | ImageVmHost | 镜像虚拟机宿主机 |
| itemArr[].vgpuInfoDTO | VgpuInfoDTO | vGPU信息 |
| itemArr[].vgpuInfoDTOHistoryList | List<VgpuInfoDTO> | vGPU历史信息列表 |
| itemArr[].loaderPatitionNumber | Integer | 加载器分区数 |
| itemArr[].loaderPath | String | 加载器路径 |
| itemArr[].partType | PartType | 分区类型 |
| itemArr[].ftpUploadState | FtpUploadState | FTP上传状态 |
| itemArr[].controlState | ControlStateEnum | 控制状态 |
| itemArr[].imageDiskList | List<CbbImageDiskInfoDTO> | 镜像磁盘列表 |
| itemArr[].createTime | Date | 创建时间 |
| itemArr[].lastEditTime | Date | 最后编辑时间 |
| itemArr[].guestToolVersion | String | GuestTool版本 |
| itemArr[].lastRecoveryPointId | UUID | 最后还原点ID |
| itemArr[].hasInstallScsiController | Boolean | 是否安装SCSI控制器 |
| itemArr[].storageDriverVersion | String | 存储驱动版本 |
| itemArr[].beforeStorageDriverVersion | String | 编辑前存储驱动版本 |
| itemArr[].enableVirtualEmulation | Boolean | 是否启用虚拟化仿真 |
| itemArr[].beforeEditEnableVirtualEmulation | Boolean | 编辑前是否启用虚拟化仿真 |
| itemArr[].vmSystemDiskSn | String | 虚拟机系统盘序列号 |
| itemArr[].remoteTerminalImageEditState | CbbRemoteTerminalImageEditEnum | 远程终端镜像编辑状态 |
| itemArr[].editUploadDownloadPercentage | String | 编辑上传下载进度百分比 |
| itemArr[].createMode | CbbImageTemplateCreateMode | 镜像创建模式 |
| itemArr[].isAd | Boolean | 是否AD域 |
| itemArr[].computerName | String | 计算机名 |
| itemArr[].imageUsage | ImageUsageTypeEnum | 镜像用途 |
| itemArr[].terminalImageDownloadProgressInfo | CbbTerminalImageDownloadProgressDTO | 终端镜像下载进度 |
| itemArr[].totalImageFileSize | Integer | 镜像文件总大小 |
| itemArr[].clusterInfo | ClusterInfoDTO | 集群信息 |
| itemArr[].storagePool | PlatformStoragePoolDTO | 存储池信息 |
| itemArr[].enableUamAgent | Boolean | 是否启用UAM代理 |
| itemArr[].vmClusterId | UUID | 虚拟机集群ID |
| itemArr[].vmStoragePoolId | UUID | 虚拟机存储池ID |
| itemArr[].cbbImageFormat | ImageFormat | 镜像格式 |
| itemArr[].editErrorMessageList | List<String> | 编辑错误信息列表 |
| itemArr[].imageDriverList | List<DriverWithImageDTO> | 镜像驱动列表 |
| itemArr[].hasImportDriverPackage | Boolean | 是否导入驱动包 |
| itemArr[].isGlobalImage | Boolean | 是否全局镜像 |
| itemArr[].enableGlobalImage | Boolean | 是否启用全局镜像 |
| itemArr[].osIsoFileId | UUID | 操作系统ISO文件ID |
| itemArr[].osVersion | String | 操作系统版本 |
| itemArr[].enableMultipleVersion | Boolean | 是否启用多版本 |
| itemArr[].isNewestVersion | Boolean | 是否最新版本 |
| itemArr[].rootImageId | UUID | 根镜像ID |
| itemArr[].rootImageName | String | 根镜像名称 |
| itemArr[].sourceSnapshotId | UUID | 源快照ID |
| itemArr[].imageRoleType | ImageRoleType | 镜像角色类型 |
| itemArr[].terminalLocalEditType | ImageTerminalLocalEditType | 终端本地编辑类型 |
| itemArr[].diskController | String | 磁盘控制器 |
| itemArr[].cpuArch | CbbCpuArchType | CPU架构 |
| itemArr[].enableDesktopUpgrade | Boolean | 是否启用桌面升级 |
| itemArr[].baseFileSize | Long | 基础文件大小 |
| itemArr[].diff1FileSize | Long | 差异文件1大小 |
| itemArr[].diff2FileSize | Long | 差异文件2大小 |
| itemArr[].publishedSlimmingVersion | Integer | 已发布瘦身版本 |
| itemArr[].currentSlimmingVersion | Integer | 当前瘦身版本 |
| itemArr[].hasImageSlimming | Boolean | 是否已镜像瘦身 |
| itemArr[].slimFlag | Integer | 瘦身标记 |
| itemArr[].platformId | UUID | 云平台ID（父类） |
| itemArr[].platformType | CloudPlatformType | 云平台类型（父类） |
| itemArr[].platformName | String | 云平台名称（父类） |
| itemArr[].platformStatus | CloudPlatformStatus | 云平台状态（父类） |
## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 处理流程

1. Assert.notNull(sessionContext/webRequest)
2. rccSpacePoolWebHelper.covert(webRequest) 转换为 LocalImageTemplatePageRequest（保留 CompositeMatch）
3. classroomImageAPI.findAllClassroomImage() 获取教室已发布镜像ID，从查询条件中移除
4. 超管：listAllImageTemplate 全量镜像剔除已发布镜像ID，appendImageIdMatchEqual(pageSearchRequest, 剩余ID, IMAGE_ID)
5. 非超管：listImageIdByAdminId 获取权限镜像ID并剔除已发布；为空直接返回空 itemArr；exactMatch 中 imageRoleType==VERSION 时按 ROOT_IMAGE_ID 过滤否则按 IMAGE_ID 过滤
6. cbbImageTemplateMgmtAPI.pageQueryLocalPageImageTemplate(pageSearchRequest) 分页查询
7. 返回 DefaultWebResponse.success(response)

## 下游消费方

### 消费1：POST /rcc/space/image/list

镜像模板ID，被 space publish/edit 的 imageTemplateIdArr 消费（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | sessionContext/webRequest | 不能为 null | Assert 失败 |
| PARAM | page/limit | @NotNull @Range 校验 | 越界校验失败 |
| BUSINESS | imageId | 教室已发布镜像不展示；非超管仅展示权限内镜像 | 无权限时返回空列表 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| page | user_input/from_query | 按业务构造 |
| limit | user_input/from_query | 按业务构造 |
| searchKeyword | user_input/from_query | 按业务构造 |
| noPermission | user_input/from_query | 按业务构造 |
| exactMatchArr | user_input/from_query | 按业务构造 |
| sortArr | user_input/from_query | 按业务构造 |
| customMatchArr | user_input/from_query | 按业务构造 |
| customData | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 超管查询镜像列表 | $.content.itemArr 非空 |
| 非超管带权限查询 | $.content.itemArr 非空 |
| 多版本镜像（imageRoleType=VERSION） | $.content.itemArr 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 非超管无镜像权限 | 管理员无镜像数据权限 | $.status==SUCCESS 且 $.content.itemArr 为空 |
| 入参为 null | webRequest 缺省 | $.status==ERROR |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 只读分页查询，无副作用 |
