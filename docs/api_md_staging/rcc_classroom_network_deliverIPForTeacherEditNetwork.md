---
version: '2.0'
api:
  url: /rcc/classroom/network/deliverIPForTeacherEditNetwork
  method: POST
  name: 教师机编辑网络策略时为其分配IP（num=1, enableTeacher=true），支持从指定起始IP预分配
  controller: RccClassroomNetworkController
  method_ref: deliverIPForTeacherEditNetwork
  permission: 无
  exec_mode: sync
  async: false
  description: 教师机编辑网络策略时为其分配IP（num=1, enableTeacher=true），支持从指定起始IP预分配
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
request:
  dto: GetIpForVDITeacherEditNetworkWebRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 教室ID
    clusterId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 计算集群ID
    platformId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 云平台ID
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
- api: 内部调用:ClassroomTeacherAPI
  purpose: 按教室ID取教师座位ID
- api: 内部调用:RccVDIIpDeliverAPI
  purpose: 无起始IP时为教师座位分配IP
downstream: []
constraints:
- level: request
  field: classroomId/clusterId/platformId
  rule: '@NotNull 非空'
  failure: webmvc 参数校验异常
- level: request
  field: vdiStartIP
  rule: 若填写必须是合法IPv4
  failure: webmvc IPv4 格式校验异常
assertions:
  success:
  - scenario: 教室教师机存在且网络有效
    expect: $.status=="SUCCESS"；$.content.vdiStartIP 非空
  failure:
  - scenario: 教师不存在
    trigger: classroomTeacherAPI.getTeacherId 返回空/异常
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
---
# POST /rcc/classroom/network/deliverIPForTeacherEditNetwork

> 教师机编辑网络策略时为其分配IP（num=1, enableTeacher=true），支持从指定起始IP预分配 ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/network/deliverIPForTeacherEditNetwork<br>教师机编辑网络策略时为其分配IP（num=1, enableTeacher=tr<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert webRequest 非空"]
        C2["Step2: classroomTeacherAPI.getTeacherId(classro"]
        C3["Step3: 无起始IP：构造 IpForVDISeatEditRequest{classro"]
        C4["Step4: 有起始IP：构造 IpForVDISeatEditFromStartReques"]
        C5["Step5: 返回 success(dto)"]
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
| URL | /rcc/classroom/network/deliverIPForTeacherEditNetwork |
| Controller | RccClassroomNetworkController |
| 方法名 | deliverIPForTeacherEditNetwork |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 教师机编辑网络策略时为其分配IP（num=1, enableTeacher=true），支持从指定起始IP预分配 |

## 入参详情

### GetIpForVDITeacherEditNetworkWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull 非空 | 教室ID |
| clusterId | UUID | 是 | @NotNull 非空 | 计算集群ID |
| platformId | UUID | 是 | @NotNull 非空 | 云平台ID |
| vdiStartIP | String | 否 | @Nullable 可空，若填需 @IPv4Address | VDI网络开始IP |
| networkId | UUID | 否 | @Nullable 可空 | 网络策略ID |

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
2. classroomTeacherAPI.getTeacherId(classroomId) 取教师ID
3. 无起始IP：构造 IpForVDISeatEditRequest{classroomId, networkId, num=1, seatIdArr=[teacherId], enableTeacher=true, clusterId, platformId} → getFreeIpIntervalForEditVDI
4. 有起始IP：构造 IpForVDISeatEditFromStartRequest 并 setVdiStartIP → getFreeIpIntervalForEditVDIFromStart 并回填
5. 返回 success(dto)

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | classroomId/clusterId/platformId | @NotNull 非空 | webmvc 参数校验异常 |
| request | vdiStartIP | 若填写必须是合法IPv4 | webmvc IPv4 格式校验异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| clusterId | user_input/from_query | 按业务构造 |
| platformId | user_input/from_query | 按业务构造 |
| vdiStartIP | user_input/from_query | 按业务构造 |
| networkId | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教室教师机存在且网络有效 | $.status=="SUCCESS"；$.content.vdiStartIP 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 教师不存在 | classroomTeacherAPI.getTeacherId 返回空/异常 | status==ERROR（BusinessException 抛出） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | high |
| 说明 | 只读计算，不产生副作用 |
