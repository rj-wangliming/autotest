---
version: '2.0'
api:
  url: /rcc/classroom/network/deliverIPForVDIClassroom
  method: POST
  name: 为VDI教室分配IP：按网络策略+数量计算空闲IP区间，支持从指定起始IP顺序预分配
  controller: RccClassroomNetworkController
  method_ref: deliverIPForVDIClassroom
  permission: 无
  exec_mode: sync
  async: false
  description: 为VDI教室分配IP：按网络策略+数量计算空闲IP区间，支持从指定起始IP顺序预分配
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: createClassroom
  api: POST /rcc/classroom/create
  purpose: 创建教室（VDI）
  request:
    body:
      classroomName: ${param.classroom_name}
  idempotent: recreate
  delete_api: /rcc/classroom/delete
  delete_param: classroomId
request:
  dto: IpForVDIClassroomWebRequest
  body:
    networkId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 网络策略ID
      value: ${param.network_id}
    number:
      type: Integer
      required: true
      constraint: '@NotNull 非空'
      description: 所需IP数目
      value: ${param.number}
    vdiStartIP:
      type: String
      required: false
      constraint: '@Nullable 可空，若填需 @IPv4Address 合法IPv4'
      description: 预分配起始IP
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
      description: IP是否溢出（不足）
    shortOfIp:
      type: Long
      description: 缺少的IP数量
    networkId:
      type: UUID
      description: 网络策略ID
    clusterId:
      type: UUID
      description: 计算集群ID
    platformId:
      type: UUID
      description: 云平台ID
upstream:
- api: 内部调用:RccVDIIpDeliverAPI
  purpose: 无起始IP时按网络+数量计算空闲IP区间
downstream:
- api: POST /rcc/classroom/create
  purpose: 推断：出参 VDIDeliverIpInfoDTO.vdiStartIP 供教室创建 POST /rcc/classroom/createom/create
constraints:
- level: request
  field: networkId/number
  rule: '@NotNull 非空'
  failure: webmvc 参数校验异常
- level: request
  field: vdiStartIP
  rule: 若填写必须是合法IPv4地址
  failure: webmvc IPv4 格式校验异常
assertions:
  success:
  - scenario: 不指定起始IP
    expect: $.status==SUCCESS；$.content.vdiStartIP/usedIPSegmentList 等 IP 区间字段
  - scenario: 指定起始IP
    expect: $.status==SUCCESS；$.content.vdiStartIP 非空且 usedIPSegmentList 返回分配区间
  failure:
  - scenario: IP不足
    trigger: 网络策略下空闲IP数量不足
    expect: 返回 isOverflow=true/shortOfIp>0 或底层抛 BusinessException
cleanup: []
idempotency:
  level: non_idempotent
  note: 只读计算分配结果，不落库不改变状态，重复调用结果一致
params:
  required:
  - name: classroom_name
  - name: network_id
  - name: number
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/network/deliverIPForVDIClassroom

> 为VDI教室分配IP：按网络策略+数量计算空闲IP区间，支持从指定起始IP顺序预分配 ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/network/deliverIPForVDIClassroom<br>为VDI教室分配IP：按网络策略+数量计算空闲IP区间，支持从指定起始IP顺序预<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert webRequest 非空"]
        C2["Step2: getFreeIPInterval：vdiStartIP 为 null → ge"]
        C3["Step3: vdiStartIP 非空 → getFreeIPIntervalForVDIC"]
        C4["Step4: 返回 success(dto)"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
    end
    B --> C1
    subgraph 下游消费方
        D1["/rcc/classroom/create"]
    end
    B -->|数据| D1
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rcc/classroom/network/deliverIPForVDIClassroom |
| Controller | RccClassroomNetworkController |
| 方法名 | deliverIPForVDIClassroom |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 为VDI教室分配IP：按网络策略+数量计算空闲IP区间，支持从指定起始IP顺序预分配 |

## 入参详情

### IpForVDIClassroomWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| networkId | UUID | 是 | @NotNull 非空 | 网络策略ID |
| number | Integer | 是 | @NotNull 非空 | 所需IP数目 |
| vdiStartIP | String | 否 | @Nullable 可空，若填需 @IPv4Address 合法IPv4 | 预分配起始IP |

## 出参详情

| 返回类型 | DefaultWebResponse<VDIDeliverIpInfoDTO> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| vdiStartIP | String | 分配起始IP |
| usedIPSegmentList | List<IpIntervalDTO> | 已使用IP段列表 |
| isOverflow | Boolean | IP是否溢出（不足） |
| shortOfIp | Long | 缺少的IP数量 |
| networkId | UUID | 网络策略ID |
| clusterId | UUID | 计算集群ID |
| platformId | UUID | 云平台ID |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 处理流程

1. Assert webRequest 非空
2. getFreeIPInterval：vdiStartIP 为 null → getFreeIPIntervalForVDIClassroom(networkId, number)
3. vdiStartIP 非空 → getFreeIPIntervalForVDIClassroomFromStart(networkId, number, vdiStartIP) 并回填 dto.vdiStartIP
4. 返回 success(dto)

## 下游消费方

### 消费1：/rcc/classroom/create

消费方（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | networkId/number | @NotNull 非空 | webmvc 参数校验异常 |
| request | vdiStartIP | 若填写必须是合法IPv4地址 | webmvc IPv4 格式校验异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| networkId | user_input/from_query | 按业务构造 |
| number | user_input/from_query | 按业务构造 |
| vdiStartIP | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 不指定起始IP | 返回系统计算的空间空闲IP区间 |
| 指定起始IP | 返回从起始IP开始分配并回填 vdiStartIP 的结果 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| IP不足 | 网络策略下空闲IP数量不足 | 返回 isOverflow=true/shortOfIp>0 或底层抛 BusinessException |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | high |
| 说明 | 只读计算分配结果，不落库不改变状态，重复调用结果一致 |
