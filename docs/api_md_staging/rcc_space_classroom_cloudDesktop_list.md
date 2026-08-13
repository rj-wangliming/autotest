---
version: '2.0'
api:
  url: /rcc/space/classroom/cloudDesktop/list
  method: POST
  name: '教学桌面池云桌面列表分页查询。入参为 PageQueryRequest，用 pageQueryBuilderFactory.newRequestBuilder '
  controller: RccSpaceController
  method_ref: classroomCloudDesktopList
  permission: 无
  exec_mode: 同步
  async: false
  description: 教学桌面池云桌面列表分页查询。入参为 PageQueryRequest，用 pageQueryBuilderFactory.newRequestBuilder 构造查询；若管理员非全组权限则通过 listTerminalGroupIdByAdminId 获取终端组权限并追加 in(classroomTerminalGroupId,...) 过滤（权限为空返回空页），最后调 rccSpaceAPI.
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: create_classroom
  api: POST /rcc/classroom/create
  purpose: 创建教室产生 classroomId
  request:
    body:
      classroomName: ${param.classroom_name}
  idempotent: recreate
  delete_api: /rcc/classroom/delete
  delete_param: classroomId
- name: select_classroom_id
  api: POST /rcc/classroom/select
  purpose: 按名称过滤查询教室（searchKeyword=${param.classroom_name}）
  extract:
    classroomId: $.content[0].classroomId
  request:
    body:
      searchKeyword: ${param.classroom_name}
request:
  dto: PageQueryRequest
  body:
    page:
      type: Integer
      required: true
      constraint: '@NotNull @Range(0-2147483647)'
      description: 页码
    limit:
      type: Integer
      required: true
      constraint: '@NotNull @Range(1-2147483647)'
      description: 每页条数
    searchKeyword:
      type: String
      required: false
      constraint: '@Nullable'
      description: 搜索关键字
    matchArr:
      type: Match[]
      required: false
      constraint: '@Nullable'
      description: 自定义匹配条件（含 classroomId 等过滤）
    sortArr:
      type: Sort[]
      required: false
      constraint: '@Nullable'
      description: 排序条件
    exactMatchArr:
      type: ExactMatch[]
      required: false
      constraint: '@Nullable'
      description: 精确匹配条件
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
      type: CloudDesktopDTO[]
      description: 云桌面记录列表（space 模块 CloudDesktopDTO，继承 rco 模块 CloudDesktopDTO）
    total:
      type: Integer
      description: 总记录数
    itemArr[]_desktopId:
      type: UUID
      description: 桌面ID（本模块新增）
    itemArr[]_id:
      type: UUID
      description: 桌面记录ID
    itemArr[]_cbbId:
      type: UUID
      description: CBB桌面ID
    itemArr[]_desktopName:
      type: String
      description: 桌面名称
    itemArr[]_realName:
      type: String
      description: 真实姓名/显示名
    itemArr[]_userId:
      type: UUID
      description: 用户ID
    itemArr[]_userName:
      type: String
      description: 用户名
    itemArr[]_userGroupId:
      type: UUID
      description: 用户组ID
    itemArr[]_userGroup:
      type: String
      description: 用户组名称
    itemArr[]_desktopState:
      type: String
      description: 桌面状态
    itemArr[]_desktopType:
      type: String
      description: 桌面类型
    itemArr[]_sessionType:
      type: CbbDesktopSessionType
      description: 会话类型
    itemArr[]_memory:
      type: Double
      description: 内存（GB）
    itemArr[]_cpu:
      type: Integer
      description: CPU核数
    itemArr[]_systemDisk:
      type: Integer
      description: 系统盘大小（GB）
    itemArr[]_personDisk:
      type: Integer
      description: 个人盘大小（GB）
    itemArr[]_imageName:
      type: String
      description: 镜像名称
    itemArr[]_osName:
      type: String
      description: 操作系统名称
    itemArr[]_desktopIp:
      type: String
      description: 桌面IP
    itemArr[]_desktopIpv6Addr:
      type: String
      description: 桌面IPv6地址
    itemArr[]_desktopMac:
      type: String
      description: 桌面MAC地址
    itemArr[]_autoDeskDhcp:
      type: Boolean
      description: 桌面是否自动获取IP（DHCP）
    itemArr[]_deskGateway:
      type: String
      description: 桌面网关
    itemArr[]_deskMask:
      type: String
      description: 桌面子网掩码
    itemArr[]_autoDeskDns:
      type: Boolean
      description: 桌面是否自动获取DNS
    itemArr[]_deskDnsPrimary:
      type: String
      description: 桌面主DNS
    itemArr[]_deskSecondDnsPrimary:
      type: String
      description: 桌面备DNS
    itemArr[]_terminalId:
      type: String
      description: 终端ID
    itemArr[]_terminalName:
      type: String
      description: 终端名称
    itemArr[]_terminalGroup:
      type: String
      description: 终端分组
    itemArr[]_terminalPlatform:
      type: String
      description: 终端平台
    itemArr[]_terminalIp:
      type: String
      description: 终端IP
    itemArr[]_terminalMac:
      type: String
      description: 终端MAC
    itemArr[]_terminalMask:
      type: String
      description: 终端掩码
    itemArr[]_terminalSystemDiskType:
      type: String
      description: 终端系统盘类型
    itemArr[]_userType:
      type: String
      description: 用户类型
    itemArr[]_deleteTime:
      type: Date
      description: 删除时间
    itemArr[]_isDelete:
      type: Boolean
      description: 是否已删除
    itemArr[]_latestLoginTime:
      type: Date
      description: 最近登录时间
    itemArr[]_latestRunningTime:
      type: Date
      description: 最近运行时间
    itemArr[]_beforeEditGuestToolVersion:
      type: String
      description: 编辑前GuestTool版本
    itemArr[]_isWindowsOsActive:
      type: Boolean
      description: Windows系统是否已激活
    itemArr[]_osActiveBySystem:
      type: Boolean
      description: 系统是否自动激活
    itemArr[]_physicalServerId:
      type: UUID
      description: 物理服务器ID
    itemArr[]_physicalServerIp:
      type: String
      description: 物理服务器IP
    itemArr[]_desktopRole:
      type: String
      description: 桌面角色
    itemArr[]_faultState:
      type: Boolean
      description: 是否故障
    itemArr[]_faultDescription:
      type: String
      description: 故障描述
    itemArr[]_userDescription:
      type: String
      description: 用户描述
    itemArr[]_faultTime:
      type: Date
      description: 故障时间
    itemArr[]_createTime:
      type: Date
      description: 创建时间
    itemArr[]_computerName:
      type: String
      description: 计算机名
    itemArr[]_networkAccessMode:
      type: CbbNetworkAccessModeEnums
      description: 网络接入模式
    itemArr[]_wirelessIp:
      type: String
      description: 无线IP
    itemArr[]_wirelessIpv6Addr:
      type: String
      description: 无线IPv6地址
    itemArr[]_wirelessMacAddr:
      type: String
      description: 无线MAC地址
    itemArr[]_autoWirelessDhcp:
      type: Boolean
      description: 无线是否自动获取IP
    itemArr[]_wirelessGateway:
      type: String
      description: 无线网关
    itemArr[]_wirelessMask:
      type: String
      description: 无线掩码
    itemArr[]_autoWirelessDns:
      type: Boolean
      description: 无线是否自动获取DNS
    itemArr[]_wirelessDnsPrimary:
      type: String
      description: 无线主DNS
    itemArr[]_wirelessSecondDnsPrimary:
      type: String
      description: 无线备DNS
    itemArr[]_enableProxy:
      type: Boolean
      description: 是否启用代理
    itemArr[]_desktopCategory:
      type: String
      description: 桌面分类
    itemArr[]_desktopStrategyId:
      type: UUID
      description: 桌面策略ID
    itemArr[]_groupNamePath:
      type: String
      description: 用户组路径
    itemArr[]_needRefreshStrategy:
      type: Boolean
      description: 是否需要刷新策略
    itemArr[]_hasAutoJoinDomain:
      type: Boolean
      description: 是否自动加入域
    itemArr[]_cbbImageType:
      type: String
      description: 镜像类型
    itemArr[]_vgpuType:
      type: VgpuType
      description: vGPU类型
    itemArr[]_vgpuDesktop:
      type: Boolean
      description: 是否vGPU桌面
    itemArr[]_vgpuModel:
      type: String
      description: vGPU型号
    itemArr[]_enableAgreementAgency:
      type: Boolean
      description: 是否启用协议代理
    itemArr[]_agreementAgencyLimitMode:
      type: AgreementAgencyLimitMode
      description: 协议代理限制模式
    itemArr[]_enableWebClient:
      type: Boolean
      description: 是否启用Web客户端
    itemArr[]_enableMobileClient:
      type: Boolean
      description: 是否启用移动客户端
    itemArr[]_enableUtilizeClient:
      type: Boolean
      description: 是否启用利用客户端
    itemArr[]_remark:
      type: String
      description: 备注
    itemArr[]_osVersion:
      type: String
      description: 操作系统版本
    itemArr[]_osType:
      type: String
      description: 操作系统类型
    itemArr[]_guestToolVersion:
      type: String
      description: GuestTool版本
    itemArr[]_enableCustom:
      type: Boolean
      description: 是否自定义配置
    itemArr[]_deskCreateMode:
      type: String
      description: 桌面创建模式
    itemArr[]_desktopImageType:
      type: CbbOsType
      description: 桌面镜像操作系统类型
    itemArr[]_downloadState:
      type: DownloadStateEnum
      description: 镜像下载状态
    itemArr[]_failCode:
      type: Integer
      description: 失败码
    itemArr[]_downloadPromptMessage:
      type: String
      description: 下载提示信息
    itemArr[]_downloadFinishTime:
      type: Date
      description: 下载完成时间
    itemArr[]_extraDiskList:
      type: List<CbbAddExtraDiskDTO>
      description: 扩展磁盘列表
    itemArr[]_enableFullSystemDisk:
      type: Boolean
      description: 是否启用全盘
    itemArr[]_desktopPoolType:
      type: String
      description: 桌面池类型
    itemArr[]_desktopPoolId:
      type: UUID
      description: 桌面池ID
    itemArr[]_poolStrategyError:
      type: Boolean
      description: 桌面池策略是否异常
    itemArr[]_isOpenMaintenance:
      type: Boolean
      description: 是否开启维护模式
    itemArr[]_isOpenDeskMaintenance:
      type: Boolean
      description: 是否开启桌面维护
    itemArr[]_connectClosedTime:
      type: Date
      description: 连接关闭时间
    itemArr[]_userProfileStrategyId:
      type: UUID
      description: 用户配置策略ID
    itemArr[]_userProfileStrategyName:
      type: String
      description: 用户配置策略名称
    itemArr[]_strategyName:
      type: String
      description: 策略名称
    itemArr[]_networkName:
      type: String
      description: 网络名称
    itemArr[]_imageUsage:
      type: ImageUsageTypeEnum
      description: 镜像用途
    itemArr[]_repairState:
      type: String
      description: 修复状态
    itemArr[]_clusterId:
      type: UUID
      description: 计算集群ID
    itemArr[]_clusterName:
      type: String
      description: 计算集群名称
    itemArr[]_idvTerminalMode:
      type: String
      description: IDV终端模式
    itemArr[]_imageDiskInfoDTOList:
      type: List<CbbImageDiskInfoDTO>
      description: 镜像磁盘信息列表
    itemArr[]_imageId:
      type: UUID
      description: 镜像ID
    itemArr[]_rootImageId:
      type: UUID
      description: 根镜像ID
    itemArr[]_rootImageName:
      type: String
      description: 根镜像名称
    itemArr[]_imageRoleType:
      type: ImageRoleType
      description: 镜像角色类型
    itemArr[]_willApplyImageId:
      type: UUID
      description: 待应用镜像ID
    itemArr[]_hasAppDisk:
      type: Boolean
      description: 是否有应用盘
    itemArr[]_hasAppDiskTest:
      type: Boolean
      description: 是否有测试应用盘
    itemArr[]_disabled:
      type: Boolean
      description: 是否禁用
    itemArr[]_gtAgentState:
      type: CbbGtAgentState
      description: GuestTool代理状态
    itemArr[]_userState:
      type: IacUserStateEnum
      description: 用户状态
    itemArr[]_userAccountExpireDate:
      type: String
      description: 用户账户过期时间
    itemArr[]_userInvalidRecoverTime:
      type: Date
      description: 用户失效恢复时间
    itemArr[]_userInvalidTime:
      type: Integer
      description: 用户失效时长
    itemArr[]_userInvalid:
      type: Boolean
      description: 用户是否失效
    itemArr[]_desktopPoolName:
      type: String
      description: 桌面池名称
    itemArr[]_showRootPwd:
      type: Boolean
      description: 是否显示管理员密码
    itemArr[]_platformId:
      type: UUID
      description: 云平台ID
    itemArr[]_platformName:
      type: String
      description: 云平台名称
    itemArr[]_platformType:
      type: CloudPlatformType
      description: 云平台类型
    itemArr[]_platformStatus:
      type: CloudPlatformStatus
      description: 云平台状态
    itemArr[]_cloudPlatformId:
      type: String
      description: 云平台实例ID
    itemArr[]_cpuArch:
      type: CbbCpuArchType
      description: CPU架构
    itemArr[]_snapshotCount:
      type: Integer
      description: 快照数
    itemArr[]_hasTranslateDesk:
      type: Boolean
      description: 是否有转译桌面
    itemArr[]_hasAllDiskInExtraStorage:
      type: Boolean
      description: 是否所有磁盘均在扩展存储
    itemArr[]_hasSession:
      type: Boolean
      description: 是否有会话
    itemArr[]_strategyType:
      type: String
      description: 策略类型
    itemArr[]_registerState:
      type: CbbDeskRegisterState
      description: 注册状态
    itemArr[]_registerMessage:
      type: String
      description: 注册信息
    itemArr[]_canUpgradeAgent:
      type: Integer
      description: 是否可升级Agent
    itemArr[]_deskType:
      type: String
      description: 桌面类型
    itemArr[]_canSupportMultiSessionRemoteAssist:
      type: Boolean
      description: 是否支持多会话远程协助
    itemArr[]_isAllowCheckUsage:
      type: Boolean
      description: 是否允许查看使用量
    itemArr[]_adOu:
      type: String
      description: AD组织单元
    itemArr[]_cpuUsage:
      type: String
      description: CPU使用率
    itemArr[]_memUsage:
      type: String
      description: 内存使用率
    itemArr[]_diskUsage:
      type: String
      description: 磁盘使用率
    itemArr[]_ownerSystem:
      type: String
      description: 所属系统
    itemArr[]_desktopPoolOwnerSystem:
      type: String
      description: 桌面池所属系统
    itemArr[]_secLicenseType:
      type: String
      description: 安全授权类型
    itemArr[]_hasSecLicense:
      type: Boolean
      description: 是否有安全授权
    itemArr[]_extensionData:
      type: JSONObject
      description: 扩展数据
upstream:
- api: POST /rcc/classroom/create
  produces: $.content.classroomId
  purpose: 教室ID筛选条件（可空），来源为教室创建返回
downstream:
- api: 内部调用:rcc/RccSpaceAPI#getSpaceClassroomDesktop
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: request/sessionContext
  rule: 不能为 null
  failure: Assert 失败
- level: BUSINESS
  field: classroomTerminalGroupId
  rule: 非超管按终端组数据权限过滤
  failure: 无权限返回空列表
assertions:
  success:
  - scenario: 传入课堂云桌面分页条件
    expect: $.content.itemArr 非空
  failure:
  - scenario: 无终端组权限
    trigger: 非超管且未分配权限
    expect: $.status==SUCCESS 且 $.content.itemArr 为空
  - scenario: 入参为 null
    trigger: request 缺失
    expect: $.status==ERROR
cleanup: []
idempotency:
  level: non_idempotent
  note: 只读分页查询，无副作用
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/space/classroom/cloudDesktop/list

> 教学桌面池云桌面列表分页查询。入参为 PageQueryRequest，用 pageQueryBuilderFactory.newRequestBuilder 构造查询；若管理员非全组权限则通过 listTerminalGroupIdByAdminId 获取终端组权限并追加 in(classroomTerminalGroupId,...) 过滤（权限为空返回空页），最后调 rccSpaceAPI.getSpaceClassroomDesktop 返回云桌面分页。 ｜ 无特殊权限 ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create"]
    end
    B["POST /rcc/space/classroom/cloudDesktop/list<br>教学桌面池云桌面列表分页查询。入参为 PageQueryRequest，用 pa<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request) 与 Assert.notNull"]
        C2["Step2: pageQueryBuilderFactory.newRequestBuilde"]
        C3["Step3: getCloudDesktopDTO(requestBuilder, userI"]
        C4["Step4: rccSpaceAPI.getSpaceClassroomDesktop(req"]
        C5["Step5: 返回 CommonWebResponse.success(resp)"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
        C4 --> C5
    end
    B --> C1
    subgraph 下游消费方
        D1["desktop/detail"]
        D2["powerOff/restart/shutdown"]
    end
    B -->|数据| D1
    B -->|数据| D2
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rcc/space/classroom/cloudDesktop/list |
| Controller | RccSpaceController |
| 方法名 | classroomCloudDesktopList |
| 权限注解 | 无 |
| 执行方式 | 同步 |
| 业务含义 | 教学桌面池云桌面列表分页查询。入参为 PageQueryRequest，用 pageQueryBuilderFactory.newRequestBuilder 构造查询；若管理员非全组权限则通过 listTerminalGroupIdByAdminId 获取终端组权限并追加 in(classroomTerminalGroupId,...) 过滤（权限为空返回空页），最后调 rccSpaceAPI.getSpaceClassroomDesktop 返回云桌面分页。 |

## 入参详情

### PageQueryRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| page | Integer | 是 | @NotNull @Range(0-2147483647) | 页码 |
| limit | Integer | 是 | @NotNull @Range(1-2147483647) | 每页条数 |
| searchKeyword | String | 否 | @Nullable | 搜索关键字 |
| matchArr | Match[] | 否 | @Nullable | 自定义匹配条件（含 classroomId 等过滤） |
| sortArr | Sort[] | 否 | @Nullable | 排序条件 |
| exactMatchArr | ExactMatch[] | 否 | @Nullable | 精确匹配条件 |
| customData | String | 否 | @Nullable | 扩展透传数据 |

## 出参详情

| 返回类型 | CommonWebResponse<DefaultPageResponse<CloudDesktopDTO>> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr | CloudDesktopDTO[] | 云桌面记录列表（space 模块 CloudDesktopDTO，继承 rco 模块 CloudDesktopDTO） |
| total | Integer | 总记录数 |
| itemArr[].desktopId | UUID | 桌面ID（本模块新增） |
| itemArr[].id | UUID | 桌面记录ID |
| itemArr[].cbbId | UUID | CBB桌面ID |
| itemArr[].desktopName | String | 桌面名称 |
| itemArr[].realName | String | 真实姓名/显示名 |
| itemArr[].userId | UUID | 用户ID |
| itemArr[].userName | String | 用户名 |
| itemArr[].userGroupId | UUID | 用户组ID |
| itemArr[].userGroup | String | 用户组名称 |
| itemArr[].desktopState | String | 桌面状态 |
| itemArr[].desktopType | String | 桌面类型 |
| itemArr[].sessionType | CbbDesktopSessionType | 会话类型 |
| itemArr[].memory | Double | 内存（GB） |
| itemArr[].cpu | Integer | CPU核数 |
| itemArr[].systemDisk | Integer | 系统盘大小（GB） |
| itemArr[].personDisk | Integer | 个人盘大小（GB） |
| itemArr[].imageName | String | 镜像名称 |
| itemArr[].osName | String | 操作系统名称 |
| itemArr[].desktopIp | String | 桌面IP |
| itemArr[].desktopIpv6Addr | String | 桌面IPv6地址 |
| itemArr[].desktopMac | String | 桌面MAC地址 |
| itemArr[].autoDeskDhcp | Boolean | 桌面是否自动获取IP（DHCP） |
| itemArr[].deskGateway | String | 桌面网关 |
| itemArr[].deskMask | String | 桌面子网掩码 |
| itemArr[].autoDeskDns | Boolean | 桌面是否自动获取DNS |
| itemArr[].deskDnsPrimary | String | 桌面主DNS |
| itemArr[].deskSecondDnsPrimary | String | 桌面备DNS |
| itemArr[].terminalId | String | 终端ID |
| itemArr[].terminalName | String | 终端名称 |
| itemArr[].terminalGroup | String | 终端分组 |
| itemArr[].terminalPlatform | String | 终端平台 |
| itemArr[].terminalIp | String | 终端IP |
| itemArr[].terminalMac | String | 终端MAC |
| itemArr[].terminalMask | String | 终端掩码 |
| itemArr[].terminalSystemDiskType | String | 终端系统盘类型 |
| itemArr[].userType | String | 用户类型 |
| itemArr[].deleteTime | Date | 删除时间 |
| itemArr[].isDelete | Boolean | 是否已删除 |
| itemArr[].latestLoginTime | Date | 最近登录时间 |
| itemArr[].latestRunningTime | Date | 最近运行时间 |
| itemArr[].beforeEditGuestToolVersion | String | 编辑前GuestTool版本 |
| itemArr[].isWindowsOsActive | Boolean | Windows系统是否已激活 |
| itemArr[].osActiveBySystem | Boolean | 系统是否自动激活 |
| itemArr[].physicalServerId | UUID | 物理服务器ID |
| itemArr[].physicalServerIp | String | 物理服务器IP |
| itemArr[].desktopRole | String | 桌面角色 |
| itemArr[].faultState | Boolean | 是否故障 |
| itemArr[].faultDescription | String | 故障描述 |
| itemArr[].userDescription | String | 用户描述 |
| itemArr[].faultTime | Date | 故障时间 |
| itemArr[].createTime | Date | 创建时间 |
| itemArr[].computerName | String | 计算机名 |
| itemArr[].networkAccessMode | CbbNetworkAccessModeEnums | 网络接入模式 |
| itemArr[].wirelessIp | String | 无线IP |
| itemArr[].wirelessIpv6Addr | String | 无线IPv6地址 |
| itemArr[].wirelessMacAddr | String | 无线MAC地址 |
| itemArr[].autoWirelessDhcp | Boolean | 无线是否自动获取IP |
| itemArr[].wirelessGateway | String | 无线网关 |
| itemArr[].wirelessMask | String | 无线掩码 |
| itemArr[].autoWirelessDns | Boolean | 无线是否自动获取DNS |
| itemArr[].wirelessDnsPrimary | String | 无线主DNS |
| itemArr[].wirelessSecondDnsPrimary | String | 无线备DNS |
| itemArr[].enableProxy | Boolean | 是否启用代理 |
| itemArr[].desktopCategory | String | 桌面分类 |
| itemArr[].desktopStrategyId | UUID | 桌面策略ID |
| itemArr[].groupNamePath | String | 用户组路径 |
| itemArr[].needRefreshStrategy | Boolean | 是否需要刷新策略 |
| itemArr[].hasAutoJoinDomain | Boolean | 是否自动加入域 |
| itemArr[].cbbImageType | String | 镜像类型 |
| itemArr[].vgpuType | VgpuType | vGPU类型 |
| itemArr[].vgpuDesktop | Boolean | 是否vGPU桌面 |
| itemArr[].vgpuModel | String | vGPU型号 |
| itemArr[].enableAgreementAgency | Boolean | 是否启用协议代理 |
| itemArr[].agreementAgencyLimitMode | AgreementAgencyLimitMode | 协议代理限制模式 |
| itemArr[].enableWebClient | Boolean | 是否启用Web客户端 |
| itemArr[].enableMobileClient | Boolean | 是否启用移动客户端 |
| itemArr[].enableUtilizeClient | Boolean | 是否启用利用客户端 |
| itemArr[].remark | String | 备注 |
| itemArr[].osVersion | String | 操作系统版本 |
| itemArr[].osType | String | 操作系统类型 |
| itemArr[].guestToolVersion | String | GuestTool版本 |
| itemArr[].enableCustom | Boolean | 是否自定义配置 |
| itemArr[].deskCreateMode | String | 桌面创建模式 |
| itemArr[].desktopImageType | CbbOsType | 桌面镜像操作系统类型 |
| itemArr[].downloadState | DownloadStateEnum | 镜像下载状态 |
| itemArr[].failCode | Integer | 失败码 |
| itemArr[].downloadPromptMessage | String | 下载提示信息 |
| itemArr[].downloadFinishTime | Date | 下载完成时间 |
| itemArr[].extraDiskList | List<CbbAddExtraDiskDTO> | 扩展磁盘列表 |
| itemArr[].enableFullSystemDisk | Boolean | 是否启用全盘 |
| itemArr[].desktopPoolType | String | 桌面池类型 |
| itemArr[].desktopPoolId | UUID | 桌面池ID |
| itemArr[].poolStrategyError | Boolean | 桌面池策略是否异常 |
| itemArr[].isOpenMaintenance | Boolean | 是否开启维护模式 |
| itemArr[].isOpenDeskMaintenance | Boolean | 是否开启桌面维护 |
| itemArr[].connectClosedTime | Date | 连接关闭时间 |
| itemArr[].userProfileStrategyId | UUID | 用户配置策略ID |
| itemArr[].userProfileStrategyName | String | 用户配置策略名称 |
| itemArr[].strategyName | String | 策略名称 |
| itemArr[].networkName | String | 网络名称 |
| itemArr[].imageUsage | ImageUsageTypeEnum | 镜像用途 |
| itemArr[].repairState | String | 修复状态 |
| itemArr[].clusterId | UUID | 计算集群ID |
| itemArr[].clusterName | String | 计算集群名称 |
| itemArr[].idvTerminalMode | String | IDV终端模式 |
| itemArr[].imageDiskInfoDTOList | List<CbbImageDiskInfoDTO> | 镜像磁盘信息列表 |
| itemArr[].imageId | UUID | 镜像ID |
| itemArr[].rootImageId | UUID | 根镜像ID |
| itemArr[].rootImageName | String | 根镜像名称 |
| itemArr[].imageRoleType | ImageRoleType | 镜像角色类型 |
| itemArr[].willApplyImageId | UUID | 待应用镜像ID |
| itemArr[].hasAppDisk | Boolean | 是否有应用盘 |
| itemArr[].hasAppDiskTest | Boolean | 是否有测试应用盘 |
| itemArr[].disabled | Boolean | 是否禁用 |
| itemArr[].gtAgentState | CbbGtAgentState | GuestTool代理状态 |
| itemArr[].userState | IacUserStateEnum | 用户状态 |
| itemArr[].userAccountExpireDate | String | 用户账户过期时间 |
| itemArr[].userInvalidRecoverTime | Date | 用户失效恢复时间 |
| itemArr[].userInvalidTime | Integer | 用户失效时长 |
| itemArr[].userInvalid | Boolean | 用户是否失效 |
| itemArr[].desktopPoolName | String | 桌面池名称 |
| itemArr[].showRootPwd | Boolean | 是否显示管理员密码 |
| itemArr[].platformId | UUID | 云平台ID |
| itemArr[].platformName | String | 云平台名称 |
| itemArr[].platformType | CloudPlatformType | 云平台类型 |
| itemArr[].platformStatus | CloudPlatformStatus | 云平台状态 |
| itemArr[].cloudPlatformId | String | 云平台实例ID |
| itemArr[].cpuArch | CbbCpuArchType | CPU架构 |
| itemArr[].snapshotCount | Integer | 快照数 |
| itemArr[].hasTranslateDesk | Boolean | 是否有转译桌面 |
| itemArr[].hasAllDiskInExtraStorage | Boolean | 是否所有磁盘均在扩展存储 |
| itemArr[].hasSession | Boolean | 是否有会话 |
| itemArr[].strategyType | String | 策略类型 |
| itemArr[].registerState | CbbDeskRegisterState | 注册状态 |
| itemArr[].registerMessage | String | 注册信息 |
| itemArr[].canUpgradeAgent | Integer | 是否可升级Agent |
| itemArr[].deskType | String | 桌面类型 |
| itemArr[].canSupportMultiSessionRemoteAssist | Boolean | 是否支持多会话远程协助 |
| itemArr[].isAllowCheckUsage | Boolean | 是否允许查看使用量 |
| itemArr[].adOu | String | AD组织单元 |
| itemArr[].cpuUsage | String | CPU使用率 |
| itemArr[].memUsage | String | 内存使用率 |
| itemArr[].diskUsage | String | 磁盘使用率 |
| itemArr[].ownerSystem | String | 所属系统 |
| itemArr[].desktopPoolOwnerSystem | String | 桌面池所属系统 |
| itemArr[].secLicenseType | String | 安全授权类型 |
| itemArr[].hasSecLicense | Boolean | 是否有安全授权 |
| itemArr[].extensionData | JSONObject | 扩展数据 |
## 上游前置业务

### 前置1：POST /rcc/classroom/create

教室ID筛选条件（可空），来源为教室创建返回（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull(request) 与 Assert.notNull(sessionContext)
2. pageQueryBuilderFactory.newRequestBuilder(request) 构造分页查询 Builder
3. getCloudDesktopDTO(requestBuilder, userId)：非全组权限时追加 in(classroomTerminalGroupId, 权限终端组ID)，无权限返回空页
4. rccSpaceAPI.getSpaceClassroomDesktop(requestBuilder.build()) 执行查询
5. 返回 CommonWebResponse.success(resp)

## 下游消费方

### 消费1：POST /rcc/space/classroom/cloudDesktop/list

云桌面ID，被 desktop/detail、powerOff/restart/shutdown 消费（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | request/sessionContext | 不能为 null | Assert 失败 |
| BUSINESS | classroomTerminalGroupId | 非超管按终端组数据权限过滤 | 无权限返回空列表 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| page | user_input/from_query | 按业务构造 |
| limit | user_input/from_query | 按业务构造 |
| searchKeyword | user_input/from_query | 按业务构造 |
| matchArr | user_input/from_query | 按业务构造 |
| sortArr | user_input/from_query | 按业务构造 |
| exactMatchArr | user_input/from_query | 按业务构造 |
| customData | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 传入课堂云桌面分页条件 | $.content.itemArr 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 无终端组权限 | 非超管且未分配权限 | $.status==SUCCESS 且 $.content.itemArr 为空 |
| 入参为 null | request 缺失 | $.status==ERROR |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 只读分页查询，无副作用 |
