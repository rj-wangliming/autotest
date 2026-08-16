---
version: '2.0'
api:
  url: /rcc/classroom/list
  method: POST
  name: 分页获取教室信息列表。管理员拥有全部数据权限时直接 classroomAPI.pageQuery；否则查询其可见终端组列表，无任何权限返回空页，有权限则通过 p
  controller: RccClassroomConfigController
  method_ref: getClassroomDetailInfoList
  permission: 无
  exec_mode: 同步分页查询（PageQuery + 数据权限过滤）
  async: false
  description: 分页获取教室信息列表。管理员拥有全部数据权限时直接 classroomAPI.pageQuery；否则查询其可见终端组列表，无任何权限返回空页，有权限则通过 pageQueryBuilderFactory 在 matchArr 中追加 terminalGroupId in 过滤后查询，返回 PageQueryResponse<ViewClassroomInfoEntity>。
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
request:
  dto: ClassroomPageQueryRequest
  body:
    page:
      type: Integer
      required: false
      constraint: '@Range(min=0)，默认0'
      description: 页码（从0开始）
    limit:
      type: Integer
      required: false
      constraint: '@Range(min=1, max=2000)，默认1'
      description: 每页条数
    searchKeyword:
      type: String
      required: false
      constraint: '@Nullable'
      description: 搜索关键字（模糊搜索教室名）
    needForceRefresh:
      type: Boolean
      required: false
      constraint: '@Nullable，默认 false'
      description: 是否强制刷新（真实请求样例默认 false）
    matchArr:
      type: Match[]
      required: false
      constraint: '@NotNull，默认空数组'
      description: 精确/模糊查询条件数组
      value:
      - type: EXACT
        fieldName: classroomName
        valueArr:
        - ${param.classroom_name}
        matchRule: EQ
    sortArr:
      type: Sort[]
      required: false
      constraint: '@NotNull，默认空数组'
      description: 排序条件数组
    customData:
      type: String
      required: false
      constraint: '@Nullable'
      description: 自定义扩展数据
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    itemArr:
      type: ViewClassroomInfoEntity[]
      description: 教室列表项（元素字段见下）
    total:
      type: Integer
      description: 总记录数
    classroomId:
      type: UUID
      description: 教室ID
    classroomName:
      type: String
      description: 教室名称
    classroomState:
      type: ClassroomLessonStatusEnum
      description: 教室上课状态
    studentType:
      type: String
      description: 学生工作模式类型（JSON串，用于派生 studentModeArr）
    studentModeArr:
      type: TerminalTypeEnum[]
      description: 学生工作模式数组
    studentStartIp:
      type: String
      description: 学生终端起始IP
    studentEndIp:
      type: String
      description: 学生终端结束IP
    studentTerminalIpSegment:
      type: String
      description: 学生终端IP段（由 studentStartIp/studentEndIp 生成）
    currentLessonId:
      type: UUID
      description: 当前上课ID
    disableNetwork:
      type: Boolean
      description: 是否禁网
    networkIds:
      type: String
      description: 教室关联网络策略ID聚合串（逗号分隔）
    teacherTerminalId:
      type: String
      description: 教师机终端ID
    teacherIp:
      type: String
      description: 教师机IP
    teacherType:
      type: String
      description: 教师机工作模式类型（JSON串，用于派生 teacherModeArr）
    teacherModeArr:
      type: TerminalTypeEnum[]
      description: 教师机工作模式数组
    teacherDesktopId:
      type: UUID
      description: 教师机云桌面ID
    teacherDesktopName:
      type: String
      description: 教师机云桌面名称
    teacherDesktopIp:
      type: String
      description: 教师机云桌面IP
    teacherId:
      type: UUID
      description: 教师ID
    teacherTerminalState:
      type: CbbTerminalStateEnums
      description: 教师机终端状态
    teacherTerminalModel:
      type: String
      description: 教师机终端型号
    teacherUpgradeVersion:
      type: String
      description: 教师机终端升级版本
    teacherHardwareVersion:
      type: String
      description: 教师机终端硬件版本
    teacherRainOsVersion:
      type: String
      description: 教师机终端RainOS版本
    teacherSerialNumber:
      type: String
      description: 教师机终端序列号
    teacherMac:
      type: String
      description: 教师机终端MAC
    teacherDiskSize:
      type: Long
      description: 教师机终端磁盘大小
    teacherCpuType:
      type: String
      description: 教师机终端CPU型号
    teacherMemory:
      type: Long
      description: 教师机终端内存大小
    teacherTerminalOsType:
      type: String
      description: 教师机终端操作系统类型
    terminalTotalNum:
      type: Integer
      description: 终端总数（学生机+教师机，接口回填）
    terminalOnlineNum:
      type: Integer
      description: 在线终端数（接口回填）
    desktopTotalNum:
      type: Integer
      description: 云桌面总数
    desktopOnlineNum:
      type: Integer
      description: 在线云桌面数
    vdiTeacherImageNum:
      type: Integer
      description: 教师机VDI镜像数
    vdiStudentImageNum:
      type: Integer
      description: 学生机VDI镜像数
    tciTeacherImageNum:
      type: Integer
      description: 教师机TCI镜像数
    tciStudentImageNum:
      type: Integer
      description: 学生机TCI镜像数
    teacherDesktopState:
      type: CbbCloudDeskState
      description: 教师机云桌面状态
    teacherBootManageMode:
      type: CbbTerminalBootManageModeEnums
      description: 教师机终端引导管理模式
    terminalNeedUpgrade:
      type: Boolean
      description: 终端是否需要升级
    publishAsSpace:
      type: Boolean
      description: 是否作为教学实训空间发布
    canTerminalInit:
      type: Boolean
      description: 是否支持终端初始化
    terminalGroupId:
      type: UUID
      description: 关联终端组ID
    teacherLockStatus:
      type: Boolean
      description: 教师机终端锁定状态
    teacherTerminalIp:
      type: String
      description: 教师机绑定的终端IP
    deployMode:
      type: String
      description: 终端部署模式
    teacherPlatformStatus:
      type: CloudPlatformStatus
      description: 教师机镜像使用的云平台状态
    "itemArr[]_classroomId":
      type: UUID
      description: 教室ID
    "itemArr[]_classroomName":
      type: String
      description: 教室名称
    "itemArr[]_classroomState":
      type: ClassroomLessonStatusEnum
      description: 教室上课状态
    "itemArr[]_studentType":
      type: String
      description: 学生工作模式类型（JSON串，用于派生 studentModeArr）
    "itemArr[]_studentModeArr":
      type: TerminalTypeEnum[]
      description: 学生工作模式数组
    "itemArr[]_studentStartIp":
      type: String
      description: 学生终端起始IP
    "itemArr[]_studentEndIp":
      type: String
      description: 学生终端结束IP
    "itemArr[]_studentTerminalIpSegment":
      type: String
      description: 学生终端IP段（由 studentStartIp/studentEndIp 生成）
    "itemArr[]_currentLessonId":
      type: UUID
      description: 当前上课ID
    "itemArr[]_disableNetwork":
      type: Boolean
      description: 是否禁网
    "itemArr[]_networkIds":
      type: String
      description: 教室关联网络策略ID聚合串（逗号分隔）
    "itemArr[]_teacherTerminalId":
      type: String
      description: 教师机终端ID
    "itemArr[]_teacherIp":
      type: String
      description: 教师机IP
    "itemArr[]_teacherType":
      type: String
      description: 教师机工作模式类型（JSON串，用于派生 teacherModeArr）
    "itemArr[]_teacherModeArr":
      type: TerminalTypeEnum[]
      description: 教师机工作模式数组
    "itemArr[]_teacherDesktopId":
      type: UUID
      description: 教师机云桌面ID
    "itemArr[]_teacherDesktopName":
      type: String
      description: 教师机云桌面名称
    "itemArr[]_teacherDesktopIp":
      type: String
      description: 教师机云桌面IP
    "itemArr[]_teacherId":
      type: UUID
      description: 教师ID
    "itemArr[]_teacherTerminalState":
      type: CbbTerminalStateEnums
      description: 教师机终端状态
    "itemArr[]_teacherTerminalModel":
      type: String
      description: 教师机终端型号
    "itemArr[]_teacherUpgradeVersion":
      type: String
      description: 教师机终端升级版本
    "itemArr[]_teacherHardwareVersion":
      type: String
      description: 教师机终端硬件版本
    "itemArr[]_teacherRainOsVersion":
      type: String
      description: 教师机终端RainOS版本
    "itemArr[]_teacherSerialNumber":
      type: String
      description: 教师机终端序列号
    "itemArr[]_teacherMac":
      type: String
      description: 教师机终端MAC
    "itemArr[]_teacherDiskSize":
      type: Long
      description: 教师机终端磁盘大小
    "itemArr[]_teacherCpuType":
      type: String
      description: 教师机终端CPU型号
    "itemArr[]_teacherMemory":
      type: Long
      description: 教师机终端内存大小
    "itemArr[]_teacherTerminalOsType":
      type: String
      description: 教师机终端操作系统类型
    "itemArr[]_terminalTotalNum":
      type: Integer
      description: 终端总数（学生机+教师机，接口回填）
    "itemArr[]_terminalOnlineNum":
      type: Integer
      description: 在线终端数（接口回填）
    "itemArr[]_desktopTotalNum":
      type: Integer
      description: 云桌面总数
    "itemArr[]_desktopOnlineNum":
      type: Integer
      description: 在线云桌面数
    "itemArr[]_vdiTeacherImageNum":
      type: Integer
      description: 教师机VDI镜像数
    "itemArr[]_vdiStudentImageNum":
      type: Integer
      description: 学生机VDI镜像数
    "itemArr[]_tciTeacherImageNum":
      type: Integer
      description: 教师机TCI镜像数
    "itemArr[]_tciStudentImageNum":
      type: Integer
      description: 学生机TCI镜像数
    "itemArr[]_teacherDesktopState":
      type: CbbCloudDeskState
      description: 教师机云桌面状态
    "itemArr[]_teacherBootManageMode":
      type: CbbTerminalBootManageModeEnums
      description: 教师机终端引导管理模式
    "itemArr[]_terminalNeedUpgrade":
      type: Boolean
      description: 终端是否需要升级
    "itemArr[]_publishAsSpace":
      type: Boolean
      description: 是否作为教学实训空间发布
    "itemArr[]_canTerminalInit":
      type: Boolean
      description: 是否支持终端初始化
    "itemArr[]_terminalGroupId":
      type: UUID
      description: 关联终端组ID
    "itemArr[]_teacherLockStatus":
      type: Boolean
      description: 教师机终端锁定状态
    "itemArr[]_teacherTerminalIp":
      type: String
      description: 教师机绑定的终端IP
    "itemArr[]_deployMode":
      type: String
      description: 终端部署模式
    "itemArr[]_teacherPlatformStatus":
      type: CloudPlatformStatus
      description: 教师机镜像使用的云平台状态
upstream:
- api: 内部调用:space-pa/PlatformAdminDataPermissionAPI
  purpose: 判断管理员是否拥有全部数据权限
- api: 内部调用:rcc/ClassroomAPI
  purpose: 分页查询教室信息
downstream:
- api: POST /rcc/classroom/getInfo|delete|image/*
  purpose: 出参 ViewClassroomInfoEntity.classroomId，教室ID的兜底查询来源
constraints:
- level: PARAM
  field: page
  rule: '@Range(min=0)'
  failure: 负数校验失败
- level: PARAM
  field: limit
  rule: '@Range(min=1, max=2000)'
  failure: 越界校验失败
- level: BUSINESS
  field: 数据权限
  rule: 非全权限管理员仅返回其可见终端组内教室
  failure: 无可见终端组时返回空列表（非错误）
assertions:
  success:
  - scenario: 全权限管理员分页查询
    expect: $.status=="SUCCESS"；$.content.itemArr 非空；$.content.total 非空
  - scenario: 非全权限管理员无可见终端组
    expect: $.status=="SUCCESS"；$.content.itemArr 为空数组
  failure:
  - scenario: limit 超限
    trigger: limit>2000
    expect: status==ERROR（参数校验失败）
cleanup: []
idempotency:
  level: non_idempotent
  note: 纯查询接口，无副作用
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/list

> 分页获取教室信息列表。管理员拥有全部数据权限时直接 classroomAPI.pageQuery；否则查询其可见终端组列表，无任何权限返回空页，有权限则通过 pageQueryBuilderFactory 在 matchArr 中追加 terminalGroupId in 过滤后查询，返回 PageQueryResponse<ViewClassroomInfoEntity>。 ｜ 无特殊权限 ｜ 同步分页查询（PageQuery + 数据权限过滤）

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/list<br>分页获取教室信息列表。管理员拥有全部数据权限时直接 classroomAPI.p<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request/sessionContext)"]
        C2["Step2: adminDataPermissionAPI.isAdminHasAllData"]
        C3["Step3: 否则 adminDataPermissionAPI.listTerminalGr"]
        C4["Step4: terminalGroupIdList 为空 → 返回空 PageQueryRe"]
        C5["Step5: 非空 → pageQueryBuilderFactory.newRequestB"]
        C6["Step6: request.setMatchArr(requestBuilder.build"]
        C1 --> C2
        C7["Step7: return success(pageQueryResponse)"]
        C6 --> C7
        C2 --> C3
        C3 --> C4
        C4 --> C5
        C5 --> C6
    end
    B --> C1
    subgraph 下游消费方
        D1["POST /rcc/classroom/getInfo|delete|image/*"]
    end
    B -->|数据| D1
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rcc/classroom/list |
| Controller | RccClassroomConfigController |
| 方法名 | getClassroomDetailInfoList |
| 权限注解 | 无 |
| 执行方式 | 同步分页查询（PageQuery + 数据权限过滤） |
| 业务含义 | 分页获取教室信息列表。管理员拥有全部数据权限时直接 classroomAPI.pageQuery；否则查询其可见终端组列表，无任何权限返回空页，有权限则通过 pageQueryBuilderFactory 在 matchArr 中追加 terminalGroupId in 过滤后查询，返回 PageQueryResponse<ViewClassroomInfoEntity>。 |

## 入参详情

### ClassroomPageQueryRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| page | Integer | 否 | @Range(min=0)，默认0 | 页码（从0开始） |
| limit | Integer | 否 | @Range(min=1, max=2000)，默认1 | 每页条数 |
| matchArr | Match[] | 否 | @NotNull，默认空数组 | 精确/模糊查询条件数组 |
| sortArr | Sort[] | 否 | @NotNull，默认空数组 | 排序条件数组 |
| customData | String | 否 | @Nullable | 自定义扩展数据 |

## 出参详情

| 返回类型 | DefaultWebResponse（data=PageQueryResponse<ViewClassroomInfoEntity>） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr | ViewClassroomInfoEntity[] | 教室列表项（元素字段见下） |
| total | Integer | 总记录数 |
| classroomId | UUID | 教室ID |
| classroomName | String | 教室名称 |
| classroomState | ClassroomLessonStatusEnum | 教室上课状态 |
| studentType | String | 学生工作模式类型（JSON串，用于派生 studentModeArr） |
| studentModeArr | TerminalTypeEnum[] | 学生工作模式数组 |
| studentStartIp | String | 学生终端起始IP |
| studentEndIp | String | 学生终端结束IP |
| studentTerminalIpSegment | String | 学生终端IP段（由 studentStartIp/studentEndIp 生成） |
| currentLessonId | UUID | 当前上课ID |
| disableNetwork | Boolean | 是否禁网 |
| networkIds | String | 教室关联网络策略ID聚合串（逗号分隔） |
| teacherTerminalId | String | 教师机终端ID |
| teacherIp | String | 教师机IP |
| teacherType | String | 教师机工作模式类型（JSON串，用于派生 teacherModeArr） |
| teacherModeArr | TerminalTypeEnum[] | 教师机工作模式数组 |
| teacherDesktopId | UUID | 教师机云桌面ID |
| teacherDesktopName | String | 教师机云桌面名称 |
| teacherDesktopIp | String | 教师机云桌面IP |
| teacherId | UUID | 教师ID |
| teacherTerminalState | CbbTerminalStateEnums | 教师机终端状态 |
| teacherTerminalModel | String | 教师机终端型号 |
| teacherUpgradeVersion | String | 教师机终端升级版本 |
| teacherHardwareVersion | String | 教师机终端硬件版本 |
| teacherRainOsVersion | String | 教师机终端RainOS版本 |
| teacherSerialNumber | String | 教师机终端序列号 |
| teacherMac | String | 教师机终端MAC |
| teacherDiskSize | Long | 教师机终端磁盘大小 |
| teacherCpuType | String | 教师机终端CPU型号 |
| teacherMemory | Long | 教师机终端内存大小 |
| teacherTerminalOsType | String | 教师机终端操作系统类型 |
| terminalTotalNum | Integer | 终端总数（学生机+教师机，接口回填） |
| terminalOnlineNum | Integer | 在线终端数（接口回填） |
| desktopTotalNum | Integer | 云桌面总数 |
| desktopOnlineNum | Integer | 在线云桌面数 |
| vdiTeacherImageNum | Integer | 教师机VDI镜像数 |
| vdiStudentImageNum | Integer | 学生机VDI镜像数 |
| tciTeacherImageNum | Integer | 教师机TCI镜像数 |
| tciStudentImageNum | Integer | 学生机TCI镜像数 |
| teacherDesktopState | CbbCloudDeskState | 教师机云桌面状态 |
| teacherBootManageMode | CbbTerminalBootManageModeEnums | 教师机终端引导管理模式 |
| terminalNeedUpgrade | Boolean | 终端是否需要升级 |
| publishAsSpace | Boolean | 是否作为教学实训空间发布 |
| canTerminalInit | Boolean | 是否支持终端初始化 |
| terminalGroupId | UUID | 关联终端组ID |
| teacherLockStatus | Boolean | 教师机终端锁定状态 |
| teacherTerminalIp | String | 教师机绑定的终端IP |
| deployMode | String | 终端部署模式 |
| teacherPlatformStatus | CloudPlatformStatus | 教师机镜像使用的云平台状态 |

## 上游前置业务

（无上游数据依赖）
## 内部处理流程

### 处理流程

1. Assert.notNull(request/sessionContext)
2. adminDataPermissionAPI.isAdminHasAllDataPermissions(userId) 为 true → classroomAPI.pageQuery(request) 并返回
3. 否则 adminDataPermissionAPI.listTerminalGroupIdByAdminId(new ListTerminalGroupIdRequest(userId)) 查询可见终端组
4. terminalGroupIdList 为空 → 返回空 PageQueryResponse<ViewClassroomInfoEntity>
5. 非空 → pageQueryBuilderFactory.newRequestBuilder(request).setPageLimit(page, limit)，requestBuilder.in("terminalGroupId", terminalGroupIdList)
6. request.setMatchArr(requestBuilder.build().getMatchArr()) 后 classroomAPI.pageQuery(request)
7. return success(pageQueryResponse)

## 下游消费方

### 消费1：POST /rcc/classroom/getInfo|delete|image/*

出参 ViewClassroomInfoEntity.classroomId，教室ID的兜底查询来源（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | page | @Range(min=0) | 负数校验失败 |
| PARAM | limit | @Range(min=1, max=2000) | 越界校验失败 |
| BUSINESS | 数据权限 | 非全权限管理员仅返回其可见终端组内教室 | 无可见终端组时返回空列表（非错误） |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| page | user_input/from_query | 按业务构造 |
| limit | user_input/from_query | 按业务构造 |
| matchArr | user_input/from_query | 按业务构造 |
| sortArr | user_input/from_query | 按业务构造 |
| customData | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 全权限管理员分页查询 | $.status=="SUCCESS"；$.content.itemArr 非空；$.content.total 非空 |
| 非全权限管理员无可见终端组 | $.status=="SUCCESS"；$.content.itemArr 为空数组 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| limit 超限 | limit>2000 | status==ERROR（参数校验失败） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 纯查询接口，无副作用 |
