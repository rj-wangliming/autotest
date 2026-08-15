---
version: '2.0'
api:
  url: /rcc/classroom/seat/checkStudentDesktopIpDuplicate
  method: POST
  name: 校验云桌面IP是否与现有桌面冲突；与其它桌面冲突返回 hasDuplication=true（附错误信息），与网络内未知资源冲突也返回冲突但成功响应
  controller: RccSeatConfigController
  method_ref: checkStudentDesktopIpDuplicate
  permission: 无
  exec_mode: 同步
  async: false
  description: 校验云桌面IP是否与现有桌面冲突；与其它桌面冲突返回 hasDuplication=true（附错误信息），与网络内未知资源冲突也返回冲突但成功响应
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
  dto: CheckDesktopIpRequest
  body:
    seatId:
      type: UUID
      required: false
      constraint: '@Nullable'
      description: 座位ID（编辑时排除自身）
    studentModeArr:
      type: TerminalTypeEnum[]
      required: true
      constraint: '@NotNull'
      description: 学生机工作模式
    vdiDesktopIp:
      type: String
      required: false
      constraint: '@Nullable'
      description: VDI 云桌面IP
    networkId:
      type: UUID
      required: false
      constraint: '@Nullable'
      description: VDI 网络策略ID
    clusterId:
      type: UUID
      required: false
      constraint: '@Nullable'
      description: 计算节点ID
    platformId:
      type: UUID
      required: false
      constraint: '@Nullable'
      description: 云平台ID
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    hasDuplication:
      type: Boolean
      description: 是否冲突，false 无冲突 / true 有冲突
    errorMsg:
      type: String
      description: 冲突提示信息（与桌面IP冲突时，仅 ResponseHasDuplicateDTO 场景返回）
upstream:
- api: POST /rcc/classroom/seat/list
  produces: $.content.itemArr[0].id
  purpose: 座位ID来自座位列表查询出参（SeatInfoDTO.id），座位由/rcc/classroom/seat/batchCreate创建
- api: POST /rcc/classroom/image/getAssignedClusterAndNetwork
  produces: $.content.networkId
  purpose: 推断：VDI网络ID来源，字段名为推断
- api: POST /space/cluster/obtainComputeClusterList
  produces: $.content.itemArr[0].id
  purpose: 推断：计算集群ID来源，字段名为推断
- api: POST /space/platform/list
  produces: $.content.itemArr[0].id
  purpose: 推断：云平台ID来源，字段名为推断
downstream: []
constraints:
- level: PARAM
  field: studentModeArr
  rule: '@NotNull'
  failure: 为空参数校验失败
- level: BIZ
  field: vdiDesktopIp
  rule: IP 不可与已有桌面/网络内资源冲突
  failure: 冲突以 hasDuplication=true 成功响应返回，不视为接口错误
assertions:
  success:
  - scenario: IP 可用
    expect: $.status=="SUCCESS" 且 $.content.hasDuplication==false
  failure:
  - scenario: IP 与现有桌面冲突
    trigger: 抛 RCDC_RCC_DESKTOP_NETWORK_IP_CONFLICT_WITH_DESKTOP
    expect: $.status=="SUCCESS" 且 $.content.hasDuplication==true 且 $.content.errorMsg 非空
  - scenario: IP 与未知资源冲突（座位IP重复）
    trigger: 抛 RCDC_RCC_SEAT_DESKTOP_IP_DUPLICATE
    expect: $.status=="SUCCESS" 且 $.content.hasDuplication==true
  - scenario: 其它校验异常
    trigger: 其它 BusinessException
    expect: $.status=="ERROR" 且 $.msgKey=="rcdc_rcc_module_operate_fail"
cleanup: []
idempotency:
  level: non_idempotent
  note: 纯校验查询，无副作用
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
  - name: desktop_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/seat/checkStudentDesktopIpDuplicate

> 校验云桌面IP是否与现有桌面冲突；与其它桌面冲突返回 hasDuplication=true（附错误信息），与网络内未知资源冲突也返回冲突但成功响应 ｜ 无特殊权限 ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/seat/list"]
        A2["POST /rcc/classroom/image/getAssignedClusterAndNetwork"]
        A3["POST /space/cluster/obtainComputeClusterList"]
        A4["POST /space/platform/list"]
    end
    B["POST /rcc/classroom/seat/checkStudentDesktopIpDuplicate<br>校验云桌面IP是否与现有桌面冲突；与其它桌面冲突返回 hasDuplicatio<br>权限: 无"]
    A1 -->|数据| B
    A2 -->|数据| B
    A3 -->|数据| B
    A4 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: try：Assert.notNull 校验 request/sessionCon"]
        C2["Step2: request.buildCheckDesktopIpDTO() 构造 DTO"]
        C3["Step3: seatAPI.checkDesktopIpDuplicate(dto)，无异常"]
        C4["Step4: catch：key=RCDC_RCC_DESKTOP_NETWORK_IP_CO"]
        C5["Step5: key=RCDC_RCC_SEAT_DESKTOP_IP_DUPLICATE →"]
        C6["Step6: 其他 → 返回 fail(RCDC_RCC_MODULE_OPERATE_FAI"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
        C4 --> C5
        C5 --> C6
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
| URL | /rcc/classroom/seat/checkStudentDesktopIpDuplicate |
| Controller | RccSeatConfigController |
| 方法名 | checkStudentDesktopIpDuplicate |
| 权限注解 | 无 |
| 执行方式 | 同步 |
| 业务含义 | 校验云桌面IP是否与现有桌面冲突；与其它桌面冲突返回 hasDuplication=true（附错误信息），与网络内未知资源冲突也返回冲突但成功响应 |

## 入参详情

### CheckDesktopIpRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| seatId | UUID | 否 | @Nullable | 座位ID（编辑时排除自身） |
| studentModeArr | TerminalTypeEnum[] | 是 | @NotNull | 学生机工作模式 |
| vdiDesktopIp | String | 否 | @Nullable | VDI 云桌面IP |
| networkId | UUID | 否 | @Nullable | VDI 网络策略ID |
| clusterId | UUID | 否 | @Nullable | 计算节点ID |
| platformId | UUID | 否 | @Nullable | 云平台ID |

## 出参详情

| 返回类型 | DefaultWebResponse（data=CheckDuplicateResponse 或 ResponseHasDuplicateDTO） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| hasDuplication | Boolean | 是否冲突，false 无冲突 / true 有冲突 |
| errorMsg | String | 冲突提示信息（与桌面IP冲突时，仅 ResponseHasDuplicateDTO 场景返回） |

## 上游前置业务

### 前置1：POST /rcc/classroom/seat/list

座位ID来自座位列表查询出参（SeatInfoDTO.id），座位由/rcc/classroom/seat/batchCreate创建（由 field_map 契约映射）

### 前置2：POST /rcc/classroom/image/getAssignedClusterAndNetwork

推断：VDI网络ID来源，字段名为推断（由 field_map 契约映射）

### 前置3：POST /space/cluster/obtainComputeClusterList

推断：计算集群ID来源，字段名为推断（由 field_map 契约映射）

### 前置4：POST /space/platform/list

推断：云平台ID来源，字段名为推断（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. try：Assert.notNull 校验 request/sessionContext
2. request.buildCheckDesktopIpDTO() 构造 DTO
3. seatAPI.checkDesktopIpDuplicate(dto)，无异常返回 success(new CheckDuplicateResponse())（false）
4. catch：key=RCDC_RCC_DESKTOP_NETWORK_IP_CONFLICT_WITH_DESKTOP → 构造 ResponseHasDuplicateDTO{hasDuplication=true, errorMsg=e.getI18nMessage()} 返回 success
5. key=RCDC_RCC_SEAT_DESKTOP_IP_DUPLICATE → 返回 success(new CheckDuplicateResponse(true))
6. 其他 → 返回 fail(RCDC_RCC_MODULE_OPERATE_FAIL)

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | studentModeArr | @NotNull | 为空参数校验失败 |
| BIZ | vdiDesktopIp | IP 不可与已有桌面/网络内资源冲突 | 冲突以 hasDuplication=true 成功响应返回，不视为接口错误 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| seatId | user_input/from_query | 按业务构造 |
| studentModeArr | user_input/from_query | 按业务构造 |
| vdiDesktopIp | user_input/from_query | 按业务构造 |
| networkId | user_input/from_query | 按业务构造 |
| clusterId | user_input/from_query | 按业务构造 |
| platformId | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| IP 可用 | $.status=="SUCCESS" 且 $.content.hasDuplication==false |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| IP 与现有桌面冲突 | 抛 RCDC_RCC_DESKTOP_NETWORK_IP_CONFLICT_WITH_DESKTOP | $.status=="SUCCESS" 且 $.content.hasDuplication==true 且 $.content.errorMsg 非空 |
| IP 与未知资源冲突（座位IP重复） | 抛 RCDC_RCC_SEAT_DESKTOP_IP_DUPLICATE | $.status=="SUCCESS" 且 $.content.hasDuplication==true |
| 其它校验异常 | 其它 BusinessException | $.status=="ERROR" 且 $.msgKey=="rcdc_rcc_module_operate_fail" |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 纯校验查询，无副作用 |
