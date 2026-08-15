---
version: '2.0'
api:
  url: /rcc/classroom/seat/networkcard/list
  method: POST
  name: 查看座位终端的网卡信息列表，按座位ID校验权限后分页返回
  controller: RccSeatManageController
  method_ref: getSeatNetworkCardList
  permission: 无
  exec_mode: 同步（分页查询）
  async: false
  description: 查看座位终端的网卡信息列表，按座位ID校验权限后分页返回
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
  dto: StudentSeatDetailInfoRequest
  body:
    seatId:
      type: UUID
      required: true
      constraint: '@NotNull'
      description: 座位ID
    page:
      type: Integer
      required: false
      constraint: '@Range(min=0)'
      description: 页码（继承）
    limit:
      type: Integer
      required: false
      constraint: '@Range(min=1,max=2000)'
      description: 每页条数（继承）
    matchArr:
      type: Match[]
      required: false
      constraint: '@NotNull'
      description: 匹配条件（继承）
    sortArr:
      type: Sort[]
      required: false
      constraint: '@NotNull'
      description: 排序条件（继承）
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
      description: 网卡条数
    itemArr:
      type: CbbTerminalNetworkInfoDTO[]
      description: 网卡信息数组（元素字段见下）
    networkAccessMode:
      type: CbbNetworkModeEnums
      description: 网络接入方式
    getIpMode:
      type: CbbGetNetworkModeEnums
      description: IP获取方式（静态/DHCP）
    getDnsMode:
      type: CbbGetNetworkModeEnums
      description: DNS获取方式
    macAddr:
      type: String
      description: 网卡MAC地址
    ip:
      type: String
      description: 网卡IP
    subnetMask:
      type: String
      description: 子网掩码
    gateway:
      type: String
      description: 网关
    mainDns:
      type: String
      description: 首选DNS
    secondDns:
      type: String
      description: 备用DNS
    ssid:
      type: String
      description: 无线SSID
    maxSpeed:
      type: String
      description: 网卡最大速率
    product:
      type: String
      description: 网卡产品型号
    businessCard:
      type: CbbNetworkCardEnums
      description: 业务网卡标识
    businessCardIndex:
      type: Integer
      description: 业务网卡序号
    inUse:
      type: Boolean
      description: 是否正在使用
    iface:
      type: String
      description: 网卡接口名
    wirelessAuthMode:
      type: CbbTerminalWirelessAuthModeEnums
      description: 无线认证方式
upstream:
- api: POST /rcc/classroom/seat/list
  produces: $.content.itemArr[0].id
  purpose: 座位ID来自座位列表查询出参（SeatInfoDTO.id），座位由/rcc/classroom/seat/batchCreate创建
downstream: []
constraints:
- level: PARAM
  field: seatId
  rule: '@NotNull'
  failure: 为空时参数校验失败
- level: PERM
  field: seatId
  rule: 座位所在教室终端组权限
  failure: 无权限抛业务异常
- level: PARAM
  field: limit
  rule: '@Range(min=1,max=2000)'
  failure: 越界参数校验失败
assertions:
  success:
  - scenario: 传入有效座位ID
    expect: $.status=="SUCCESS" 且 $.content.itemArr 非空
  failure:
  - scenario: seatId 为空
    trigger: 请求缺参
    expect: $.status=="ERROR"（参数校验失败，Assert.notNull）
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
# POST /rcc/classroom/seat/networkcard/list

> 查看座位终端的网卡信息列表，按座位ID校验权限后分页返回 ｜ 无特殊权限 ｜ 同步（分页查询）

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/seat/list"]
    end
    B["POST /rcc/classroom/seat/networkcard/list<br>查看座位终端的网卡信息列表，按座位ID校验权限后分页返回<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull 校验 request/sessionContext"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: seatAPI.getTerminalNetworkList(seatId) 查"]
        C4["Step4: 构造 PageQueryResponse 返回"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
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
| URL | /rcc/classroom/seat/networkcard/list |
| Controller | RccSeatManageController |
| 方法名 | getSeatNetworkCardList |
| 权限注解 | 无 |
| 执行方式 | 同步（分页查询） |
| 业务含义 | 查看座位终端的网卡信息列表，按座位ID校验权限后分页返回 |

## 入参详情

### StudentSeatDetailInfoRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| seatId | UUID | 是 | @NotNull | 座位ID |
| page | Integer | 否 | @Range(min=0) | 页码（继承） |
| limit | Integer | 否 | @Range(min=1,max=2000) | 每页条数（继承） |
| matchArr | Match[] | 否 | @NotNull | 匹配条件（继承） |
| sortArr | Sort[] | 否 | @NotNull | 排序条件（继承） |

## 出参详情

| 返回类型 | DefaultWebResponse（data=PageQueryResponse<CbbTerminalNetworkInfoDTO>） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr | CbbTerminalNetworkInfoDTO[] | 网卡信息数组（元素字段见下） |
| total | Integer | 网卡条数 |
| networkAccessMode | CbbNetworkModeEnums | 网络接入方式 |
| getIpMode | CbbGetNetworkModeEnums | IP获取方式（静态/DHCP） |
| getDnsMode | CbbGetNetworkModeEnums | DNS获取方式 |
| macAddr | String | 网卡MAC地址 |
| ip | String | 网卡IP |
| subnetMask | String | 子网掩码 |
| gateway | String | 网关 |
| mainDns | String | 首选DNS |
| secondDns | String | 备用DNS |
| ssid | String | 无线SSID |
| maxSpeed | String | 网卡最大速率 |
| product | String | 网卡产品型号 |
| businessCard | CbbNetworkCardEnums | 业务网卡标识 |
| businessCardIndex | Integer | 业务网卡序号 |
| inUse | Boolean | 是否正在使用 |
| iface | String | 网卡接口名 |
| wirelessAuthMode | CbbTerminalWirelessAuthModeEnums | 无线认证方式 |

## 上游前置业务

### 前置1：POST /rcc/classroom/seat/list

座位ID来自座位列表查询出参（SeatInfoDTO.id），座位由/rcc/classroom/seat/batchCreate创建（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull 校验 request/sessionContext
2. rccPermissionChecker.checkTerminalGroupPermissionBySeatId(seatId) 校验权限
3. seatAPI.getTerminalNetworkList(seatId) 查询网卡列表
4. 构造 PageQueryResponse 返回

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | seatId | @NotNull | 为空时参数校验失败 |
| PERM | seatId | 座位所在教室终端组权限 | 无权限抛业务异常 |
| PARAM | limit | @Range(min=1,max=2000) | 越界参数校验失败 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| seatId | user_input/from_query | 按业务构造 |
| page | user_input/from_query | 按业务构造 |
| limit | user_input/from_query | 按业务构造 |
| matchArr | user_input/from_query | 按业务构造 |
| sortArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 传入有效座位ID | $.status=="SUCCESS" 且 $.content.itemArr 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| seatId 为空 | 请求缺参 | $.status=="ERROR"（参数校验失败，Assert.notNull） |
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
