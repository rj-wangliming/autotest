---
version: '2.0'
api:
  url: /rcc/classroom/seat/list
  method: POST
  name: 分页查询教室座位列表，支持按教室/禁网状态/终端状态/终端平台/终端引导管理方式等精确过滤与排序，并按数据权限过滤
  controller: RccSeatConfigController
  method_ref: getSeatList
  permission: 无
  exec_mode: 同步分页查询（PageSearch + 数据权限过滤）
  async: false
  description: 分页查询教室座位列表，支持按教室/禁网状态/终端状态/终端平台/终端引导管理方式等精确过滤与排序，并按数据权限过滤
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: create_classroom
  api: POST /rcc/classroom/create
  purpose: 创建教室（异步批处理任务，出参BatchTaskSubmitResult）
  request:
    body:
      classroomName: ${param.classroom_name}
  idempotent: recreate
  delete_api: /rcc/classroom/delete
  delete_param: classroomId
- name: query_classroom
  api: POST /rcc/classroom/select
  extract:
    classroomId: $.content[0].classroomId
  purpose: 按教室名精确过滤（matchArr.fieldName=classroomName）
  request:
    body:
      matchArr:
      - type: EXACT
        fieldName: classroomName
        valueArr:
        - ${param.classroom_name}
        matchRule: EQ
request:
  dto: PageWebRequest（转换为 SeatPageSearchRequest）
  body:
    page:
      type: Integer
      required: false
      description: 分页页码与每页条数（page）
    limit:
      type: Integer
      required: false
      description: 分页页码与每页条数（limit）
    exactMatchArr[].name:
      type: String
      required: false
      constraint: 支持字段
      description: classroomId / disableNetwork / desktopState(忽略) / terminalState / terminalPlatfo
    exactMatchArr[].valueArr:
      type: String[]
      required: false
      constraint: 过滤值
      description: 对应字段的取值数组
    sortArr:
      type: Sort[]
      required: false
      constraint: 排序
      description: 支持 QUERY_ID(id) 等排序字段
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    total:
      type: Integer
      description: 符合条件记录数
    itemArr:
      type: SeatInfoDTO[]
      description: 座位信息数组（元素字段见下）
    id:
      type: UUID
      description: 座位ID
    classroomId:
      type: UUID
      description: 教室ID
    classroomName:
      type: String
      description: 教室名称
    desktopName:
      type: String
      description: 云桌面主机名
    studentModeArr:
      type: TerminalTypeEnum[]
      description: 学生机工作模式（PC/VDI/IDV/VOI等）
    terminalModeArr:
      type: TerminalTypeEnum[]
      description: 终端工作模式
    imageTemplateName:
      type: String
      description: 镜像模板名称
    vdiDesktopId:
      type: UUID
      description: VDI桌面ID
    vdiDesktopIp:
      type: String
      description: VDI桌面IP
    vdiDesktopGateway:
      type: String
      description: VDI桌面网关
    vdiDesktopMask:
      type: String
      description: VDI桌面掩码
    vdiDesktopDnsPrimary:
      type: String
      description: VDI桌面首选DNS
    vdiDesktopDnsSecondary:
      type: String
      description: VDI桌面备用DNS
    idvDesktopId:
      type: UUID
      description: IDV桌面ID
    idvDesktopIp:
      type: String
      description: IDV桌面IP
    idvDesktopGateway:
      type: String
      description: IDV桌面网关
    idvDesktopMask:
      type: String
      description: IDV桌面掩码
    idvDesktopDns:
      type: String
      description: IDV桌面DNS
    idvDesktopState:
      type: CbbCloudDeskState
      description: IDV桌面状态
    seatNum:
      type: Integer
      description: 座位号
    disableNetwork:
      type: Boolean
      description: 是否禁网
    terminalId:
      type: String
      description: 终端ID
    terminalName:
      type: String
      description: 终端名称
    terminalRainOsVersion:
      type: String
      description: 终端RainOS版本
    terminalHardwareVersion:
      type: String
      description: 终端硬件版本
    terminalUpgradeVersion:
      type: String
      description: 终端升级版本
    terminalMac:
      type: String
      description: 终端MAC
    terminalIp:
      type: String
      description: 终端IP
    terminalCpu:
      type: String
      description: 终端CPU型号
    terminalMemory:
      type: Long
      description: 终端内存大小
    terminalProductModel:
      type: String
      description: 终端产品型号
    terminalSerialNum:
      type: String
      description: 终端序列号
    terminalPlatform:
      type: CbbTerminalPlatformEnums
      description: 终端平台
    terminalState:
      type: CbbTerminalStateEnums
      description: 终端状态
    desktopState:
      type: CbbCloudDeskState
      description: 桌面状态
    classroomState:
      type: ClassroomLessonStatusEnum
      description: 教室状态
    terminalType:
      type: String
      description: 终端类型
    productId:
      type: String
      description: 产品ID
    terminalStartMode:
      type: CbbTerminalStartMode
      description: 终端启动模式
    terminalResolution:
      type: String
      description: 终端分辨率
    isTerminalLocked:
      type: Boolean
      description: 终端是否锁定
    lastOnlineTime:
      type: Date
      description: 最后上线时间
    seatDownloadState:
      type: SeatDownloadStateEnum
      description: 座位下载状态
    vdiDesktopState:
      type: CbbCloudDeskState
      description: VDI桌面状态
    bootManageMode:
      type: CbbTerminalBootManageModeEnums
      description: 终端引导管理模式
    seatStatus:
      type: SeatStateEnums
      description: 座位状态
    vdiLocalDiskId:
      type: UUID
      description: VDI本地磁盘ID
    terminalNeedUpgrade:
      type: Boolean
      description: 终端是否需要升级
    deployMode:
      type: String
      description: 部署模式
    canTerminalInit:
      type: Boolean
      description: 是否支持终端初始化
    softwareVersion:
      type: String
      description: 软件版本
    sourceIp:
      type: String
      description: 来源IP
    platformStatus:
      type: CloudPlatformStatus
      description: 云平台状态
upstream:
- api: POST /rcc/classroom/terminal/list
  produces: $.content.itemArr[0].classroomId
  purpose: 推断：教室ID作为分页查询过滤条件，字段名为推断
downstream: []
constraints:
- level: PARAM
  field: exactMatchArr
  rule: exactMatchArr 不可为 null
  failure: exactMatchConvert 内部 Assert.notNull
- level: PERM
  field: classroomId
  rule: 查询教室的数据权限
  failure: 无权限教室的记录被过滤/抛权限异常
- level: PARAM
  field: terminalState
  rule: 取值须为 CbbTerminalStateEnums
  failure: 非法值转换后置 null
assertions:
  success:
  - scenario: 传入带教室过滤的分页请求
    expect: $.status=="SUCCESS" 且 $.content.itemArr 非空（已做数据权限过滤）
  failure:
  - scenario: exactMatchArr 为 null
    trigger: exactMatchConvert 触发
    expect: $.status=="ERROR"（Assert 抛 IllegalArgumentException）
  - scenario: 无数据权限
    trigger: 非超管查询无权限教室
    expect: $.status=="SUCCESS"（数据权限过滤后无权限教室记录不返回）
cleanup: []
idempotency:
  level: non_idempotent
  note: 纯查询，无副作用
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/seat/list

> 分页查询教室座位列表，支持按教室/禁网状态/终端状态/终端平台/终端引导管理方式等精确过滤与排序，并按数据权限过滤 ｜ 无特殊权限 ｜ 同步分页查询（PageSearch + 数据权限过滤）

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/terminal/list"]
    end
    B["POST /rcc/classroom/seat/list<br>分页查询教室座位列表，支持按教室/禁网状态/终端状态/终端平台/终端引导管理方式<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull 校验 request/sessionContext"]
        C2["Step2: new SeatPageSearchRequest(request) 转换分页请"]
        C3["Step3: rccPermissionChecker.checkTerminalGroupP"]
        C4["Step4: seatAPI.pageQuery(apiRequest, SeatPageQu"]
        C5["Step5: 返回 DefaultWebResponse.success(pageRespon"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
        C4 --> C5
    end
    B --> C1
    subgraph 下游消费方
        D1["POST /rcc/classroom/seat/delete、/edit、/disk/list、/networkcard/list、/terminal/wake"]
        D2["POST /rcc/classroom/seat/terminal/restart、/shutdown、/kickout、/init、/unlock、/collectLog"]
        D3["POST /rcc/classroom/desktop/shutdown、/restart等"]
    end
    B -->|数据| D1
    B -->|数据| D2
    B -->|数据| D3
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rcc/classroom/seat/list |
| Controller | RccSeatConfigController |
| 方法名 | getSeatList |
| 权限注解 | 无 |
| 执行方式 | 同步分页查询（PageSearch + 数据权限过滤） |
| 业务含义 | 分页查询教室座位列表，支持按教室/禁网状态/终端状态/终端平台/终端引导管理方式等精确过滤与排序，并按数据权限过滤 |

## 入参详情

### PageWebRequest（转换为 SeatPageSearchRequest）

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| exactMatchArr[].name | String | 否 | 支持字段 | classroomId / disableNetwork / desktopState(忽略) / terminalState / terminalPlatform / terminalBootManageMode |
| exactMatchArr[].valueArr | String[] | 否 | 过滤值 | 对应字段的取值数组 |
| sortArr | Sort[] | 否 | 排序 | 支持 QUERY_ID(id) 等排序字段 |
| limit | Integer | 否 |  | 分页页码与每页条数（limit） |
| page | Integer | 否 |  | 分页页码与每页条数（page） |## 出参详情

| 返回类型 | DefaultWebResponse（data=DefaultPageResponse<SeatInfoDTO>） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr | SeatInfoDTO[] | 座位信息数组（元素字段见下） |
| total | Integer | 符合条件记录数 |
| id | UUID | 座位ID |
| classroomId | UUID | 教室ID |
| classroomName | String | 教室名称 |
| desktopName | String | 云桌面主机名 |
| studentModeArr | TerminalTypeEnum[] | 学生机工作模式（PC/VDI/IDV/VOI等） |
| terminalModeArr | TerminalTypeEnum[] | 终端工作模式 |
| imageTemplateName | String | 镜像模板名称 |
| vdiDesktopId | UUID | VDI桌面ID |
| vdiDesktopIp | String | VDI桌面IP |
| vdiDesktopGateway | String | VDI桌面网关 |
| vdiDesktopMask | String | VDI桌面掩码 |
| vdiDesktopDnsPrimary | String | VDI桌面首选DNS |
| vdiDesktopDnsSecondary | String | VDI桌面备用DNS |
| idvDesktopId | UUID | IDV桌面ID |
| idvDesktopIp | String | IDV桌面IP |
| idvDesktopGateway | String | IDV桌面网关 |
| idvDesktopMask | String | IDV桌面掩码 |
| idvDesktopDns | String | IDV桌面DNS |
| idvDesktopState | CbbCloudDeskState | IDV桌面状态 |
| seatNum | Integer | 座位号 |
| disableNetwork | Boolean | 是否禁网 |
| terminalId | String | 终端ID |
| terminalName | String | 终端名称 |
| terminalRainOsVersion | String | 终端RainOS版本 |
| terminalHardwareVersion | String | 终端硬件版本 |
| terminalUpgradeVersion | String | 终端升级版本 |
| terminalMac | String | 终端MAC |
| terminalIp | String | 终端IP |
| terminalCpu | String | 终端CPU型号 |
| terminalMemory | Long | 终端内存大小 |
| terminalProductModel | String | 终端产品型号 |
| terminalSerialNum | String | 终端序列号 |
| terminalPlatform | CbbTerminalPlatformEnums | 终端平台 |
| terminalState | CbbTerminalStateEnums | 终端状态 |
| desktopState | CbbCloudDeskState | 桌面状态 |
| classroomState | ClassroomLessonStatusEnum | 教室状态 |
| terminalType | String | 终端类型 |
| productId | String | 产品ID |
| terminalStartMode | CbbTerminalStartMode | 终端启动模式 |
| terminalResolution | String | 终端分辨率 |
| isTerminalLocked | Boolean | 终端是否锁定 |
| lastOnlineTime | Date | 最后上线时间 |
| seatDownloadState | SeatDownloadStateEnum | 座位下载状态 |
| vdiDesktopState | CbbCloudDeskState | VDI桌面状态 |
| bootManageMode | CbbTerminalBootManageModeEnums | 终端引导管理模式 |
| seatStatus | SeatStateEnums | 座位状态 |
| vdiLocalDiskId | UUID | VDI本地磁盘ID |
| terminalNeedUpgrade | Boolean | 终端是否需要升级 |
| deployMode | String | 部署模式 |
| canTerminalInit | Boolean | 是否支持终端初始化 |
| softwareVersion | String | 软件版本 |
| sourceIp | String | 来源IP |
| platformStatus | CloudPlatformStatus | 云平台状态 |

## 上游前置业务

### 前置1：POST /rcc/classroom/terminal/list

推断：教室ID作为分页查询过滤条件，字段名为推断（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull 校验 request/sessionContext
2. new SeatPageSearchRequest(request) 转换分页请求（exactMatchConvert/sortConditionConvert）
3. rccPermissionChecker.checkTerminalGroupPermissionByQueryRequest(apiRequest, sessionContext) 按查询教室做数据权限过滤
4. seatAPI.pageQuery(apiRequest, SeatPageQueryTypeEnum.QUERY_BY_CLASSROOM) 分页查询
5. 返回 DefaultWebResponse.success(pageResponse)

## 下游消费方

### 消费1：POST /rcc/classroom/seat/delete、/edit、/disk/list、/networkcard/list、/terminal/wake

座位列表出参SeatInfoDTO.id（由 field_map 契约映射）

### 消费2：POST /rcc/classroom/seat/terminal/restart、/shutdown、/kickout、/init、/unlock、/collectLog

座位列表出参SeatInfoDTO.terminalId（由 field_map 契约映射）

### 消费3：POST /rcc/classroom/desktop/shutdown、/restart等

座位列表出参SeatInfoDTO.vdiDesktopId（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | exactMatchArr | exactMatchArr 不可为 null | exactMatchConvert 内部 Assert.notNull |
| PERM | classroomId | 查询教室的数据权限 | 无权限教室的记录被过滤/抛权限异常 |
| PARAM | terminalState | 取值须为 CbbTerminalStateEnums | 非法值转换后置 null |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| page/limit | user_input/from_query | 按业务构造 |
| exactMatchArr[].name | user_input/from_query | 按业务构造 |
| exactMatchArr[].valueArr | user_input/from_query | 按业务构造 |
| sortArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 传入带教室过滤的分页请求 | $.status=="SUCCESS" 且 $.content.itemArr 非空（已做数据权限过滤） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| exactMatchArr 为 null | exactMatchConvert 触发 | $.status=="ERROR"（Assert 抛 IllegalArgumentException） |
| 无数据权限 | 非超管查询无权限教室 | $.status=="SUCCESS"（数据权限过滤后无权限教室记录不返回） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 纯查询，无副作用 |
