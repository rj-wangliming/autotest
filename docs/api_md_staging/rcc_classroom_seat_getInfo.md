---
version: '2.0'
api:
  url: /rcc/classroom/seat/getInfo
  method: POST
  name: 获取座位详情（含桌面、终端、教室等完整信息），先校验座位所在教室权限
  controller: RccSeatConfigController
  method_ref: getSeatInfo
  permission: 无
  exec_mode: 同步
  async: false
  description: 获取座位详情（含桌面、终端、教室等完整信息），先校验座位所在教室权限
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
  api: POST /rcc/classroom/terminal/list
  extract:
    classroomId: $.content.itemArr[0].classroomId
  purpose: 按教室名精确过滤（matchArr.fieldName=classroomName）
  request:
    body:
      matchArr:
      - type: EXACT
        fieldName: classroomName
        valueArr:
        - ${param.classroom_name}
        matchRule: EQ
- name: create_seat
  api: POST /rcc/classroom/seat/batchCreate
  purpose: 批量创建座位（异步批处理任务）
  request:
    body:
      classroomId:
        value: ${prev.query_classroom.output.classroomId}
      desktopPreName:
        value: ${param.desktopPreName}
      desktopNameStartNum:
        value: ${param.desktopNameStartNum}
      seatNum:
        value: ${param.seatNum}
      studentModeArr:
        value: [VDI]
  idempotent: recreate
  delete_api: /rcc/classroom/seat/delete
  delete_param: seatIdArr
- name: query_seat
  api: POST /rcc/classroom/seat/list
  extract:
    seatId: $.content.itemArr[0].id
    terminalId: $.content.itemArr[0].terminalId
  purpose: 按座位桌面名过滤（exactMatchArr.name=desktopName）
  request:
    body:
      exactMatchArr:
      - name: desktopName
        valueArr:
        - ${param.desktop_name}
request:
  dto: SeatIdRequest
  body:
    seatId:
      type: UUID
      required: true
      constraint: '@NotNull'
      description: 座位ID
      value: ${prev.query_seat.output.seatId}
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
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
- api: POST /rcc/classroom/seat/list
  produces: $.content.itemArr[0].id
  purpose: 座位ID来自座位列表查询出参（SeatInfoDTO.id），座位由/rcc/classroom/seat/batchCreate创建
downstream: []
constraints:
- level: PARAM
  field: seatId
  rule: '@NotNull'
  failure: 为空参数校验失败
- level: PERM
  field: seatId
  rule: 座位所在教室终端组权限
  failure: 座位存在时无权限抛业务异常
- level: BIZ
  field: seatId
  rule: 座位必须存在
  failure: getSeatInfo 抛错返回 fail
assertions:
  success:
  - scenario: 传入有效座位ID且有权限
    expect: $.status=="SUCCESS" 且 $.content.id 非空
  failure:
  - scenario: 座位不存在
    trigger: getSeatInfo 抛错
    expect: $.status=="ERROR" 且 $.msgKey=="rcdc_rcc_module_operate_fail"
  - scenario: 无权限
    trigger: 权限校验抛错
    expect: $.status=="ERROR"（数据权限校验失败）
cleanup: []
idempotency:
  level: non_idempotent
  note: 纯查询，无副作用
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
  - name: desktop_name
  - name: desktopNameStartNum
    desc: ''
    used_by: 见 setup/request
  - name: desktopPreName
    desc: ''
    used_by: 见 setup/request
  - name: seatNum
    desc: ''
    used_by: 见 setup/request
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/seat/getInfo

> 获取座位详情（含桌面、终端、教室等完整信息），先校验座位所在教室权限 ｜ 无特殊权限 ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/seat/list"]
    end
    B["POST /rcc/classroom/seat/getInfo<br>获取座位详情（含桌面、终端、教室等完整信息），先校验座位所在教室权限<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: try：Assert.notNull 校验 request/sessionCon"]
        C2["Step2: seatAPI.getSeatInfo(seatId) 查询座位详情"]
        C3["Step3: 座位非空时 rccPermissionChecker.checkTerminal"]
        C4["Step4: 返回 DefaultWebResponse.success(seatInfo)"]
        C5["Step5: catch BusinessException：返回 fail(RCDC_RCC"]
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
| URL | /rcc/classroom/seat/getInfo |
| Controller | RccSeatConfigController |
| 方法名 | getSeatInfo |
| 权限注解 | 无 |
| 执行方式 | 同步 |
| 业务含义 | 获取座位详情（含桌面、终端、教室等完整信息），先校验座位所在教室权限 |

## 入参详情

### SeatIdRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| seatId | UUID | 是 | @NotNull | 座位ID |

## 出参详情

| 返回类型 | DefaultWebResponse（data=SeatInfoDTO） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 座位ID |
| classroomId | UUID | 教室ID |
| classroomName | String | 教室名称 |
| desktopName | String | 云桌面主机名 |
| studentModeArr | TerminalTypeEnum[] | 学生机工作模式 |
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

### 前置1：POST /rcc/classroom/seat/list

座位ID来自座位列表查询出参（SeatInfoDTO.id），座位由/rcc/classroom/seat/batchCreate创建（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. try：Assert.notNull 校验 request/sessionContext
2. seatAPI.getSeatInfo(seatId) 查询座位详情
3. 座位非空时 rccPermissionChecker.checkTerminalGroupPermissionByClassroomId(seatInfo.getClassroomId) 校验权限
4. 返回 DefaultWebResponse.success(seatInfo)
5. catch BusinessException：返回 fail(RCDC_RCC_MODULE_OPERATE_FAIL, e.getI18nMessage())

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | seatId | @NotNull | 为空参数校验失败 |
| PERM | seatId | 座位所在教室终端组权限 | 座位存在时无权限抛业务异常 |
| BIZ | seatId | 座位必须存在 | getSeatInfo 抛错返回 fail |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| seatId | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 传入有效座位ID且有权限 | $.status=="SUCCESS" 且 $.content.id 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 座位不存在 | getSeatInfo 抛错 | $.status=="ERROR" 且 $.msgKey=="rcdc_rcc_module_operate_fail" |
| 无权限 | 权限校验抛错 | $.status=="ERROR"（数据权限校验失败） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 纯查询，无副作用 |
