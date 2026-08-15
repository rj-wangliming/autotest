---
version: '2.0'
api:
  url: /rcc/classroom/seat/edit
  method: POST
  name: 修改座位：校验 VDI 配置与权限后，先执行编辑前校验（提前提示错误），再提交批任务异步执行座位编辑（主机名/模式/网络配置变更）
  controller: RccSeatConfigController
  method_ref: editSeat
  permission: '@EnableAuthority'
  exec_mode: 异步批处理任务（BatchTask，EditSeatBatchTaskHandler，enableParallel 单任务项）
  async: true
  description: 修改座位：校验 VDI 配置与权限后，先执行编辑前校验（提前提示错误），再提交批任务异步执行座位编辑（主机名/模式/网络配置变更）
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
  dto: EditSeatWebRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull'
      description: 教室ID
    seatId:
      type: UUID
      required: true
      constraint: '@NotNull'
      description: 座位ID
    desktopName:
      type: String
      required: true
      constraint: '@NotNull + @Size(max=8)'
      description: 云桌面主机名
    studentModeArr:
      type: TerminalTypeEnum[]
      required: true
      constraint: '@NotNull'
      description: 学生机工作模式数组
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
    idvDesktopIp:
      type: String
      required: false
      constraint: '@Nullable'
      description: IDV 云桌面IP
    idvDesktopMask:
      type: String
      required: false
      constraint: '@Nullable'
      description: IDV 云桌面掩码
    idvDesktopGateway:
      type: String
      required: false
      constraint: '@Nullable'
      description: IDV 云桌面网关
    idvDesktopDns:
      type: String
      required: false
      constraint: '@Nullable'
      description: IDV 云桌面DNS
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    taskStatus:
      type: String
      description: 批任务初始状态
    taskId:
      type: UUID
      description: 提交成功的批处理任务标识
polling:
  api: common_get_msgct_detail_info
  method: POST
  params:
    msgrelationid: ${content.taskId}
  interval_ms: 2000
  timeout_ms: 120000
  terminal_states:
    success:
    - SUCCESS
    failure:
    - FAILURE
    - PARTIAL_SUCCESS
upstream:
- api: POST /rcc/classroom/terminal/list
  produces: $.content.itemArr[0].classroomId
  purpose: 教室ID在创建教室(POST /rcc/classroom/create)后经教室终端列表查询获得（ViewClassroomInfoEntity.classroomId）
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
  field: seatId
  rule: '@NotNull'
  failure: 为空参数校验失败
- level: PARAM
  field: desktopName
  rule: '@NotNull + @Size(max=8)'
  failure: 为空/超长参数校验失败
- level: PARAM
  field: studentModeArr
  rule: '@NotNull'
  failure: 为空参数校验失败
- level: BIZ
  field: VDI配置组
  rule: vdiDesktopIp/networkId/clusterId/platformId 成对出现
  failure: 不完整抛 RCDC_RCC_VDI_CLOUD_DESKTOP_CONFIG_ERROR
- level: BIZ
  field: seatId
  rule: 座位必须存在
  failure: RCDC_RCC_SEAT_NOT_FOUND
- level: BIZ
  field: seat状态
  rule: 上课中/运行中不可编辑
  failure: RCDC_RCC_SEAT_IN_LESSON / RCDC_RCC_SEAT_IN_RUNNING
- level: BIZ
  field: desktopName/vdiDesktopIp
  rule: 不可与其它桌面冲突
  failure: RCDC_RCC_SEAT_DESKTOP_NAME_DUPLICATE / RCDC_RCC_SEAT_DESKTOP
assertions:
  success:
  - scenario: 教室空闲且配置合法
    expect: $.status=="SUCCESS" 且 $.content.taskId 非空；批任务执行编辑并审计成功；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  failure:
  - scenario: 座位上课中/运行中
    trigger: checkForEditSeat 预校验抛错
    expect: $.status=="ERROR" 且 $.msgKey∈["rcdc_rcc_seat_in_lesson","rcdc_rcc_seat_in_running"]；无任务提交
  - scenario: 主机名/IP冲突
    trigger: 预校验抛冲突错误
    expect: $.status=="ERROR" 且 $.msgKey∈["rcdc_rcc_seat_desktop_name_duplicate","rcdc_rcc_desktop_network_ip_conflict_with_desktop"]（以实际预校验 key 为准）
  - scenario: VDI配置不完整
    trigger: checkVdiCloudDesktopConfigError
    expect: $.status=="ERROR" 且 $.msgKey=="rcdc_rcc_vdi_cloud_desktop_config_error"
cleanup: []
idempotency:
  level: data_level
  note: 重复提交按相同配置编辑无实际变化，但每次都会重新下发编辑命令
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
# POST /rcc/classroom/seat/edit

> 修改座位：校验 VDI 配置与权限后，先执行编辑前校验（提前提示错误），再提交批任务异步执行座位编辑（主机名/模式/网络配置变更） ｜ @EnableAuthority ｜ 异步批处理任务（BatchTask，EditSeatBatchTaskHandler，enableParallel 单任务项）

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/terminal/list"]
        A2["POST /rcc/classroom/seat/list"]
        A3["POST /rcc/classroom/image/getAssignedClusterAndNetwork"]
        A4["POST /space/cluster/obtainComputeClusterList"]
        A5["POST /space/platform/list"]
    end
    B["POST /rcc/classroom/seat/edit<br>修改座位：校验 VDI 配置与权限后，先执行编辑前校验（提前提示错误），再提交批<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    A2 -->|数据| B
    A3 -->|数据| B
    A4 -->|数据| B
    A5 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull 校验 request/builder/sessio"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: request.checkVdiCloudDesktopConfigError("]
        C4["Step4: classroomAPI.getClassroomName(classroomI"]
        C5["Step5: request.buildEditSeatDTO() 构造 EditSeatDT"]
        C6["Step6: seatAPI.checkForEditSeat(editSeatDTO) 编辑"]
        C1 --> C2
        C7["Step7: 构造 EditSeatBatchTaskItem 与 EditSeatBatch"]
        C8["Step8: builder.setTaskName(RCDC_RCC_SEAT_OPERAT"]
        C9["Step9: 返回 DefaultWebResponse.success(result)"]
        C6 --> C7
        C7 --> C8
        C8 --> C9
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
| URL | /rcc/classroom/seat/edit |
| Controller | RccSeatConfigController |
| 方法名 | editSeat |
| 权限注解 | @EnableAuthority |
| 执行方式 | 异步批处理任务（BatchTask，EditSeatBatchTaskHandler，enableParallel 单任务项） |
| 业务含义 | 修改座位：校验 VDI 配置与权限后，先执行编辑前校验（提前提示错误），再提交批任务异步执行座位编辑（主机名/模式/网络配置变更） |

## 入参详情

### EditSeatWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull | 教室ID |
| seatId | UUID | 是 | @NotNull | 座位ID |
| desktopName | String | 是 | @NotNull + @Size(max=8) | 云桌面主机名 |
| studentModeArr | TerminalTypeEnum[] | 是 | @NotNull | 学生机工作模式数组 |
| vdiDesktopIp | String | 否 | @Nullable | VDI 云桌面IP |
| networkId | UUID | 否 | @Nullable | VDI 网络策略ID |
| clusterId | UUID | 否 | @Nullable | 计算节点ID |
| platformId | UUID | 否 | @Nullable | 云平台ID |
| idvDesktopIp | String | 否 | @Nullable | IDV 云桌面IP |
| idvDesktopMask | String | 否 | @Nullable | IDV 云桌面掩码 |
| idvDesktopGateway | String | 否 | @Nullable | IDV 云桌面网关 |
| idvDesktopDns | String | 否 | @Nullable | IDV 云桌面DNS |

## 出参详情

| 返回类型 | DefaultWebResponse（data=BatchTaskSubmitResult） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| taskId | UUID | 提交成功的批处理任务标识 |
| taskStatus | String | 批任务初始状态 |

## 上游前置业务

### 前置1：POST /rcc/classroom/terminal/list

教室ID在创建教室(POST /rcc/classroom/create)后经教室终端列表查询获得（ViewClassroomInfoEntity.classroomId）（由 field_map 契约映射）

### 前置2：POST /rcc/classroom/seat/list

座位ID来自座位列表查询出参（SeatInfoDTO.id），座位由/rcc/classroom/seat/batchCreate创建（由 field_map 契约映射）

### 前置3：POST /rcc/classroom/image/getAssignedClusterAndNetwork

推断：VDI网络ID来源，字段名为推断（由 field_map 契约映射）

### 前置4：POST /space/cluster/obtainComputeClusterList

推断：计算集群ID来源，字段名为推断（由 field_map 契约映射）

### 前置5：POST /space/platform/list

推断：云平台ID来源，字段名为推断（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：EditSeatBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | 从 EditSeatBatchTaskItem 取 EditSeatDTO |
| 2 | seatAPI.editSeat(editSeatDTO) 执行编辑 |
| 3 | 成功：auditLogAPI.recordLog(RCDC_RCC_SEAT_OPERATE_EDIT_SINGLE_SUC_LOG) 返回 SUCCESS |
| 4 | BusinessException：recordLog(EDIT_SINGLE_FAIL_LOG) 返回 FAILURE |

### 处理流程

1. Assert.notNull 校验 request/builder/sessionContext
2. rccPermissionChecker.checkTerminalGroupPermissionByClassroomId 校验权限
3. request.checkVdiCloudDesktopConfigError() 校验 VDI 配置成对
4. classroomAPI.getClassroomName(classroomId) 取教室名
5. request.buildEditSeatDTO() 构造 EditSeatDTO
6. seatAPI.checkForEditSeat(editSeatDTO) 编辑前预校验
7. 构造 EditSeatBatchTaskItem 与 EditSeatBatchTaskHandler（注入 classroomName）
8. builder.setTaskName(RCDC_RCC_SEAT_OPERATE_EDIT_SINGLE_TASK_NAME).enableParallel().registerHandler().start()
9. 返回 DefaultWebResponse.success(result)

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | seatId | @NotNull | 为空参数校验失败 |
| PARAM | desktopName | @NotNull + @Size(max=8) | 为空/超长参数校验失败 |
| PARAM | studentModeArr | @NotNull | 为空参数校验失败 |
| BIZ | VDI配置组 | vdiDesktopIp/networkId/clusterId/platformId 成对出现 | 不完整抛 RCDC_RCC_VDI_CLOUD_DESKTOP_CONFIG_ERROR |
| BIZ | seatId | 座位必须存在 | RCDC_RCC_SEAT_NOT_FOUND |
| BIZ | seat状态 | 上课中/运行中不可编辑 | RCDC_RCC_SEAT_IN_LESSON / RCDC_RCC_SEAT_IN_RUNNING |
| BIZ | desktopName/vdiDesktopIp | 不可与其它桌面冲突 | RCDC_RCC_SEAT_DESKTOP_NAME_DUPLICATE / RCDC_RCC_SEAT_DESKTOP_IP_DUPLICATE |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| seatId | user_input/from_query | 按业务构造 |
| desktopName | user_input/from_query | 按业务构造 |
| studentModeArr | user_input/from_query | 按业务构造 |
| vdiDesktopIp | user_input/from_query | 按业务构造 |
| networkId | user_input/from_query | 按业务构造 |
| clusterId | user_input/from_query | 按业务构造 |
| platformId | user_input/from_query | 按业务构造 |
| idvDesktopIp | user_input/from_query | 按业务构造 |
| idvDesktopMask | user_input/from_query | 按业务构造 |
| idvDesktopGateway | user_input/from_query | 按业务构造 |
| idvDesktopDns | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教室空闲且配置合法 | $.status=="SUCCESS" 且 $.content.taskId 非空；批任务执行编辑并审计成功；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"] |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 座位上课中/运行中 | checkForEditSeat 预校验抛错 | $.status=="ERROR" 且 $.msgKey∈["rcdc_rcc_seat_in_lesson","rcdc_rcc_seat_in_running"]；无任务提交 |
| 主机名/IP冲突 | 预校验抛冲突错误 | $.status=="ERROR" 且 $.msgKey∈["rcdc_rcc_seat_desktop_name_duplicate","rcdc_rcc_desktop_network_ip_conflict_with_desktop"]（以实际预校验 key 为准） |
| VDI配置不完整 | checkVdiCloudDesktopConfigError | $.status=="ERROR" 且 $.msgKey=="rcdc_rcc_vdi_cloud_desktop_config_error" |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | LOW |
| 说明 | 重复提交按相同配置编辑无实际变化，但每次都会重新下发编辑命令 |
