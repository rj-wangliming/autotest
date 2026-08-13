---
version: '2.0'
api:
  url: /rcc/classroom/network/deliverIPForVDISeatEdit
  method: POST
  name: 批量设置/编辑座位时为VDI座位分配IP（enableTeacher=false），支持从指定起始IP预分配
  controller: RccClassroomNetworkController
  method_ref: getIPForVDIWhenEditSeat
  permission: 无
  exec_mode: sync
  async: false
  description: 批量设置/编辑座位时为VDI座位分配IP（enableTeacher=false），支持从指定起始IP预分配
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: listClassroom
  api: POST /rcc/classroom/list
  purpose: 查询教室ID；按教室名精确过滤分页查询教室（matchArr.fieldName=classroomName），取 classroomId
  extract:
    classroomId: $.content.itemArr[0].classroomId
  request:
    body:
      matchArr:
      - fieldName: classroomName
        matchType: EQUAL
        value: ${param.classroom_name}
- name: listSeat
  api: POST /rcc/classroom/seat/list
  purpose: 按座位桌面名过滤（exactMatchArr.name=desktopName）
  extract:
    seatId: $.content.itemArr[0].id
  request:
    body:
      exactMatchArr:
      - name: desktopName
        valueArr:
        - ${param.desktop_name}
request:
  dto: IpForVDISeatEditWebRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 教室ID
    number:
      type: Integer
      required: true
      constraint: '@NotNull 非空'
      description: 座位数量（所需IP数）
    seatIdArr:
      type: UUID[]
      required: true
      constraint: '@NotEmpty 非空'
      description: 座位ID数组
    vdiStartIP:
      type: String
      required: false
      constraint: '@Nullable 可空，若填需 @IPv4Address'
      description: VDI网络开始IP
    networkId:
      type: UUID
      required: false
      constraint: '@Nullable 可空'
      description: 网络策略ID
    clusterId:
      type: UUID
      required: false
      constraint: '@Nullable 可空'
      description: 计算节点ID
    platformId:
      type: UUID
      required: false
      constraint: '@Nullable 可空'
      description: 云平台ID
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    vdiStartIP:
      type: String
      description: 分配起始IP
    usedIPSegmentList:
      type: List<IpIntervalDTO>
      description: 已使用IP段列表
    isOverflow:
      type: Boolean
      description: IP是否溢出
    shortOfIp:
      type: Long
      description: 缺少的IP数量
upstream:
- api: 内部调用:RccVDIIpDeliverAPI
  purpose: 编辑场景无起始IP时为指定座位分配空闲IP
downstream: []
constraints:
- level: request
  field: classroomId/number
  rule: '@NotNull 非空'
  failure: webmvc 参数校验异常
- level: request
  field: seatIdArr
  rule: '@NotEmpty 非空'
  failure: webmvc 参数校验异常
- level: request
  field: vdiStartIP
  rule: 若填写必须是合法IPv4
  failure: webmvc IPv4 格式校验异常
assertions:
  success:
  - scenario: 座位+网络+数量有效
    expect: $.status=="SUCCESS"；$.content.vdiStartIP 非空
  failure:
  - scenario: 座位/网络无效
    trigger: 座位不存在或网络策略缺失
    expect: status==ERROR（BusinessException 抛出）
cleanup: []
idempotency:
  level: non_idempotent
  note: 只读计算，不产生副作用
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
  - name: desktop_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/network/deliverIPForVDISeatEdit

> 批量设置/编辑座位时为VDI座位分配IP（enableTeacher=false），支持从指定起始IP预分配 ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/network/deliverIPForVDISeatEdit<br>批量设置/编辑座位时为VDI座位分配IP（enableTeacher=false<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert webRequest 非空"]
        C2["Step2: getFreeIPIntervalOfSeatEdit：vdiStartIP 为"]
        C3["Step3: vdiStartIP 非空 → buildIpForVDISeatEditFro"]
        C4["Step4: 返回 success(dto)"]
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
| URL | /rcc/classroom/network/deliverIPForVDISeatEdit |
| Controller | RccClassroomNetworkController |
| 方法名 | getIPForVDIWhenEditSeat |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 批量设置/编辑座位时为VDI座位分配IP（enableTeacher=false），支持从指定起始IP预分配 |

## 入参详情

### IpForVDISeatEditWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull 非空 | 教室ID |
| number | Integer | 是 | @NotNull 非空 | 座位数量（所需IP数） |
| seatIdArr | UUID[] | 是 | @NotEmpty 非空 | 座位ID数组 |
| vdiStartIP | String | 否 | @Nullable 可空，若填需 @IPv4Address | VDI网络开始IP |
| networkId | UUID | 否 | @Nullable 可空 | 网络策略ID |
| clusterId | UUID | 否 | @Nullable 可空 | 计算节点ID |
| platformId | UUID | 否 | @Nullable 可空 | 云平台ID |

## 出参详情

| 返回类型 | DefaultWebResponse<VDIDeliverIpInfoDTO> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| vdiStartIP | String | 分配起始IP |
| usedIPSegmentList | List<IpIntervalDTO> | 已使用IP段列表 |
| isOverflow | Boolean | IP是否溢出 |
| shortOfIp | Long | 缺少的IP数量 |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 处理流程

1. Assert webRequest 非空
2. getFreeIPIntervalOfSeatEdit：vdiStartIP 为 null → buildIpForVDISeatEditRequest(enableTeacher=false) 调 getFreeIpIntervalForEditVDI
3. vdiStartIP 非空 → buildIpForVDISeatEditFromStartRequest 调 getFreeIpIntervalForEditVDIFromStart 并回填
4. 返回 success(dto)

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | classroomId/number | @NotNull 非空 | webmvc 参数校验异常 |
| request | seatIdArr | @NotEmpty 非空 | webmvc 参数校验异常 |
| request | vdiStartIP | 若填写必须是合法IPv4 | webmvc IPv4 格式校验异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| number | user_input/from_query | 按业务构造 |
| seatIdArr | user_input/from_query | 按业务构造 |
| vdiStartIP | user_input/from_query | 按业务构造 |
| networkId | user_input/from_query | 按业务构造 |
| clusterId | user_input/from_query | 按业务构造 |
| platformId | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 座位+网络+数量有效 | $.status=="SUCCESS"；$.content.vdiStartIP 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 座位/网络无效 | 座位不存在或网络策略缺失 | status==ERROR（BusinessException 抛出） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | high |
| 说明 | 只读计算，不产生副作用 |
