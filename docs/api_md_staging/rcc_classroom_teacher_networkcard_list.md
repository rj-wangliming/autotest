---
version: '2.0'
api:
  url: /rcc/classroom/teacher/networkcard/list
  method: POST
  name: 查看教师机终端网卡信息。先校验终端组数据权限，调 classroomAPI.getTeacherNetworkCardList(classroomId) 获取网
  controller: RccClassroomConfigController
  method_ref: getTeacherTerminalNetworkCardList
  permission: 无
  exec_mode: 同步
  async: false
  description: 查看教师机终端网卡信息。先校验终端组数据权限，调 classroomAPI.getTeacherNetworkCardList(classroomId) 获取网卡列表，包装为 PageQueryResponse<CbbTerminalNetworkInfoDTO> 返回。
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
  dto: TeacherSeatDetailInfoRequest（继承 AbstractClassroomSeatDetailInfoRequest）
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull'
      description: 教室ID
      value: ${prev.query_classroom.output.classroomId}
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
    total:
      type: Integer
      description: 网卡总数
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
    "itemArr[]_networkAccessMode":
      type: CbbNetworkModeEnums
      description: 网络接入方式
    "itemArr[]_getIpMode":
      type: CbbGetNetworkModeEnums
      description: IP获取方式（静态/DHCP）
    "itemArr[]_getDnsMode":
      type: CbbGetNetworkModeEnums
      description: DNS获取方式
    "itemArr[]_macAddr":
      type: String
      description: 网卡MAC地址
    "itemArr[]_ip":
      type: String
      description: 网卡IP
    "itemArr[]_subnetMask":
      type: String
      description: 子网掩码
    "itemArr[]_gateway":
      type: String
      description: 网关
    "itemArr[]_mainDns":
      type: String
      description: 首选DNS
    "itemArr[]_secondDns":
      type: String
      description: 备用DNS
    "itemArr[]_ssid":
      type: String
      description: 无线SSID
    "itemArr[]_maxSpeed":
      type: String
      description: 网卡最大速率
    "itemArr[]_product":
      type: String
      description: 网卡产品型号
    "itemArr[]_businessCard":
      type: CbbNetworkCardEnums
      description: 业务网卡标识
    "itemArr[]_businessCardIndex":
      type: Integer
      description: 业务网卡序号
    "itemArr[]_inUse":
      type: Boolean
      description: 是否正在使用
    "itemArr[]_iface":
      type: String
      description: 网卡接口名
    "itemArr[]_wirelessAuthMode":
      type: CbbTerminalWirelessAuthModeEnums
      description: 无线认证方式
upstream:
- api: POST /rcc/classroom/terminal/list
  produces: $.content.itemArr[0].classroomId
  purpose: 教室ID在创建教室(POST /rcc/classroom/create)后经教室终端列表查询获得（ViewClassroomInfoEntity.classroomId）
downstream:
- api: 内部调用:rcc/ClassroomAPI#getTeacherNetworkCardList
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: classroomId
  rule: '@NotNull'
  failure: 缺失校验失败
- level: BUSINESS
  field: classroomId
  rule: 教室存在且有数据权限
  failure: 不存在抛 RCDC_CLASSROOM_NOT_FIND；权限不足抛权限异常
assertions:
  success:
  - scenario: 传入有效教室ID
    expect: $.status=="SUCCESS" 且 $.content.itemArr 非空
  failure:
  - scenario: 教室不存在
    trigger: classroomId 无效
    expect: $.status=="ERROR" 且 $.msgKey=="rcdc_classroom_not_find"
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
# POST /rcc/classroom/teacher/networkcard/list

> 查看教师机终端网卡信息。先校验终端组数据权限，调 classroomAPI.getTeacherNetworkCardList(classroomId) 获取网卡列表，包装为 PageQueryResponse<CbbTerminalNetworkInfoDTO> 返回。 ｜ 无特殊权限 ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/terminal/list"]
    end
    B["POST /rcc/classroom/teacher/networkcard/list<br>查看教师机终端网卡信息。先校验终端组数据权限，调 classroomAPI.ge<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request/sessionContext)"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: classroomAPI.getTeacherNetworkCardList(c"]
        C4["Step4: new PageQueryResponse<>(arr, size) 包装分页"]
        C5["Step5: return success(response)"]
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
| URL | /rcc/classroom/teacher/networkcard/list |
| Controller | RccClassroomConfigController |
| 方法名 | getTeacherTerminalNetworkCardList |
| 权限注解 | 无 |
| 执行方式 | 同步 |
| 业务含义 | 查看教师机终端网卡信息。先校验终端组数据权限，调 classroomAPI.getTeacherNetworkCardList(classroomId) 获取网卡列表，包装为 PageQueryResponse<CbbTerminalNetworkInfoDTO> 返回。 |

## 入参详情

### TeacherSeatDetailInfoRequest（继承 AbstractClassroomSeatDetailInfoRequest）

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull | 教室ID |
| page | Integer | 否 | @Range(min=0)，默认0 | 页码 |
| limit | Integer | 否 | @Range(min=1, max=2000)，默认1 | 每页条数 |
| matchArr | Match[] | 否 | @NotNull，默认空数组 | 查询条件数组 |
| sortArr | Sort[] | 否 | @NotNull，默认空数组 | 排序条件数组 |
| customData | String | 否 | @Nullable | 自定义扩展数据 |

## 出参详情

| 返回类型 | DefaultWebResponse（data=PageQueryResponse<CbbTerminalNetworkInfoDTO>） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr | CbbTerminalNetworkInfoDTO[] | 网卡信息数组（元素字段见下） |
| total | Integer | 网卡总数 |
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

### 前置1：POST /rcc/classroom/terminal/list

教室ID在创建教室(POST /rcc/classroom/create)后经教室终端列表查询获得（ViewClassroomInfoEntity.classroomId）（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull(request/sessionContext)
2. rccPermissionChecker.checkTerminalGroupPermissionByClassroomId([classroomId], sessionContext)
3. classroomAPI.getTeacherNetworkCardList(classroomId) 获取网卡列表
4. new PageQueryResponse<>(arr, size) 包装分页
5. return success(response)

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | classroomId | @NotNull | 缺失校验失败 |
| BUSINESS | classroomId | 教室存在且有数据权限 | 不存在抛 RCDC_CLASSROOM_NOT_FIND；权限不足抛权限异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| page | user_input/from_query | 按业务构造 |
| limit | user_input/from_query | 按业务构造 |
| matchArr | user_input/from_query | 按业务构造 |
| sortArr | user_input/from_query | 按业务构造 |
| customData | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 传入有效教室ID | $.status=="SUCCESS" 且 $.content.itemArr 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 教室不存在 | classroomId 无效 | $.status=="ERROR" 且 $.msgKey=="rcdc_classroom_not_find" |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 纯查询接口，无副作用 |
