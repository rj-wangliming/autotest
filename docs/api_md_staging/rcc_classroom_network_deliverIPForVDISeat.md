---
version: '2.0'
api:
  url: /rcc/classroom/network/deliverIPForVDISeat
  method: POST
  name: 查询教室关联计算集群的空闲VDI桌面起始IP（教室须已绑定计算集群；适用于改网络/加座位等场景，首次分配镜像前不可用）
  controller: RccClassroomNetworkController
  method_ref: getIPForVDIWhenCreateSeat
  permission: 无
  exec_mode: sync
  async: false
  description: 按教室、座位数、网络、集群和平台查询空闲VDI桌面起始IP。前置条件：教室已绑定计算集群与网络策略（classroom_cluster_resources），否则报 rcdc_rcc_classroom_no_find_cluster。首次分配镜像（student/teacher create）前教室未绑定集群，本接口不可用；镜像分配事务内后端会自动计算起始IP，无需本接口前置。
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: query_classroom
  api: POST /rcc/classroom/list
  purpose: 按教室名查询教室ID
  extract:
    classroomId: $.content.itemArr[0].classroomId
  request:
    body:
      matchArr:
      - type: EXACT
        fieldName: classroomName
        valueArr:
        - ${param.classroom_name}
        matchRule: EQ
- name: get_cluster
  api: POST /space/cluster/obtainComputeClusterList
  purpose: 获取计算集群与平台ID
  extract:
    clusterId: $.content.itemArr[0].computerClusterId
    platformId: $.content.itemArr[0].platformId
- name: get_network
  api: POST /space/clouddesktop/deskNetwork/list
  purpose: 获取桌面网络策略ID
  extract:
    networkId: $.content.itemArr[0].id
- name: get_free_vdi_ip
  api: POST /rcc/classroom/network/deliverIPForVDISeat
  purpose: 按教室座位数动态计算可用VDI桌面起始IP
  extract:
    desktopStartIp: $.content.vdiStartIP
    isOverflow: $.content.isOverflow
    shortOfIp: $.content.shortOfIp
  assert:
  - path: $.status
    op: eq
    value: SUCCESS
  - path: $.content.isOverflow
    op: eq
    value: false
  - path: $.content.vdiStartIP
    op: not_empty
request:
  dto: IpForVDISeatWebRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 教室ID
      value: ${prev.query_classroom.output.classroomId}
    number:
      type: Integer
      required: true
      constraint: '@NotNull 非空'
      description: 座位数量（所需IP数）
      value: ${param.number}
    vdiStartIP:
      type: String
      required: false
      constraint: '@Nullable 可空，若填需 @IPv4Address'
      description: VDI开始IP
    networkId:
      type: UUID
      required: false
      constraint: '@Nullable 可空'
      description: 网络策略ID
      value: ${prev.get_network.output.networkId}
    clusterId:
      type: UUID
      required: false
      constraint: '@Nullable 可空'
      description: 计算节点ID
      value: ${prev.get_cluster.output.clusterId}
    platformId:
      type: UUID
      required: false
      constraint: '@Nullable 可空'
      description: 云平台ID
      value: ${prev.get_cluster.output.platformId}
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
  purpose: 无起始IP时为座位分配空闲IP
downstream:
- api: POST /rcc/classroom/network/{student,teacher}/edit
  purpose: 改网络场景下先查询空闲IP区间（教室已绑定集群后）
- api: POST /rcc/classroom/seat/batchCreate
  purpose: 已有集群绑定的教室追加座位时查询起始IP
constraints:
- level: request
  field: classroomId/number
  rule: '@NotNull 非空'
  failure: webmvc 参数校验异常
- level: request
  field: vdiStartIP
  rule: 若填写必须是合法IPv4
  failure: webmvc IPv4 格式校验异常
- level: BUSINESS
  field: classroomId/clusterId
  rule: 教室须已绑定该计算集群（classroom_cluster_resources 存在 classroomId+clusterId+enableTeacher 记录）
  failure: 'rcdc_rcc_classroom_no_find_cluster：教室[{教室名}][学生机/教师机]未绑定计算集群[{集群名}]；首次分配镜像前必触发'
assertions:
  success:
  - scenario: 教室+网络+数量有效
    expect: $.status=="SUCCESS"；$.content.vdiStartIP 非空
  failure:
  - scenario: 教室/网络不存在
    trigger: 教室无对应网络或数量非法
    expect: status==ERROR（BusinessException 抛出）
cleanup: []
idempotency:
  level: non_idempotent
  note: 只读计算，不产生副作用
params:
  required:
  - name: classroom_name
  - name: number
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/network/deliverIPForVDISeat

> 创建教室座位时为VDI座位分配IP，支持从指定起始IP预分配 ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/network/deliverIPForVDISeat<br>创建教室座位时为VDI座位分配IP，支持从指定起始IP预分配<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert webRequest 非空"]
        C2["Step2: getFreeIPIntervalOfSeat：vdiStartIP 为 nul"]
        C3["Step3: vdiStartIP 非空 → buildIpForVDISeatFromSta"]
        C4["Step4: 返回 success(dto)"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
    end
    B --> C1
    subgraph 下游消费方
        D1["/rcc/classroom/seat/create"]
    end
    B -->|数据| D1
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rcc/classroom/network/deliverIPForVDISeat |
| Controller | RccClassroomNetworkController |
| 方法名 | getIPForVDIWhenCreateSeat |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 创建教室座位时为VDI座位分配IP，支持从指定起始IP预分配 |

## 入参详情

### IpForVDISeatWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull 非空 | 教室ID |
| number | Integer | 是 | @NotNull 非空 | 座位数量（所需IP数） |
| vdiStartIP | String | 否 | @Nullable 可空，若填需 @IPv4Address | VDI开始IP |
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
2. getFreeIPIntervalOfSeat：vdiStartIP 为 null → buildIpForVDISeatRequest 调 getFreeIPIntervalForVDISeat
3. vdiStartIP 非空 → buildIpForVDISeatFromStartRequest 调 getFreeIPIntervalForVDISeatFromStart 并回填
4. 返回 success(dto)

## 下游消费方

### 消费1：/rcc/classroom/seat/create

消费方（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | classroomId/number | @NotNull 非空 | webmvc 参数校验异常 |
| request | vdiStartIP | 若填写必须是合法IPv4 | webmvc IPv4 格式校验异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| number | user_input/from_query | 按业务构造 |
| vdiStartIP | user_input/from_query | 按业务构造 |
| networkId | user_input/from_query | 按业务构造 |
| clusterId | user_input/from_query | 按业务构造 |
| platformId | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教室+网络+数量有效 | $.status=="SUCCESS"；$.content.vdiStartIP 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 教室/网络不存在 | 教室无对应网络或数量非法 | status==ERROR（BusinessException 抛出） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | high |
| 说明 | 只读计算，不产生副作用 |
