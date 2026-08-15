---
version: '2.0'
api:
  url: /rcc/classroom/network/disable
  method: POST
  name: 教室批量禁网：先同步设置教室级网络状态并通知CMR，再对教室下所有座位提交禁网批处理任务
  controller: RccClassroomManageController
  method_ref: batchDisableNetwork
  permission: '@EnableAuthority'
  exec_mode: async_batch
  async: false
  description: 教室批量禁网：先同步设置教室级网络状态并通知CMR，再对教室下所有座位提交禁网批处理任务
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: createClassroom
  api: POST /rcc/classroom/create
  purpose: 创建教室
  extract:
    classroomName: ${param.classroom_name}
  request:
    body:
      classroomName: ${param.classroom_name}
  idempotent: recreate
  delete_api: /rcc/classroom/delete
  delete_param: classroomId
- name: listClassroom
  api: POST /rcc/classroom/list
  purpose: 查询教室ID；按教室名精确过滤分页查询教室（matchArr.fieldName=classroomName），取 classroomId
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
request:
  dto: BatchDisableNetworkRequest
  body:
    classroomIdArr:
      type: UUID[]
      required: true
      constraint: '@NotEmpty 非空'
      description: 教室ID列表
    disableNetwork:
      type: Boolean
      required: true
      constraint: '@NotNull 非空'
      description: true=禁网，false=解禁/恢复网络
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    taskId:
      type: UUID
      description: 无座位时为空，有座位时为禁网批处理任务ID
upstream:
- api: 内部调用:ClassroomAPI
  purpose: 设置教室级网络禁用/启用状态
- api: 内部调用:CmrClientAPI
  purpose: 通知CMR教室信息变更
- api: 内部调用:SeatAPI
  purpose: 取教室下全部座位ID
- api: 内部调用:PlatformRcoGlobalParameterAPI
  purpose: 读取 rcc_operate_network_thread_number 并发线程数参数
downstream:
- api: 内部调用:CmrClientAPI
  purpose: 内部调用（非 HTTP 端点）
- api: 内部调用:SeatAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: request
  field: classroomIdArr
  rule: '@NotEmpty 非空'
  failure: webmvc 参数校验异常
- level: request
  field: disableNetwork
  rule: '@NotNull 非空'
  failure: webmvc 参数校验异常
- level: business
  field: classroomIdArr
  rule: 管理员需具备所有目标教室的终端组数据权限
  failure: rccPermissionChecker 抛出权限异常
assertions:
  success:
  - scenario: 教室无座位
    expect: $.status=="SUCCESS"；$.msgKey==RCDC_RCC_MODULE_OPERATE_SUCCESS
  - scenario: 教室有座位
    expect: $.status=="SUCCESS"；$.content.taskId 非空（批处理任务已提交）
  failure:
  - scenario: 无终端组权限
    trigger: 任一教室不在管理员权限范围
    expect: status==ERROR；msgKey==RCDC_SAPCE_DATA_PERMISSION_DENIED
  - scenario: 个别座位下发失败
    trigger: 座位终端离线
    expect: $.status=="SUCCESS"；轮询终态任务结果 PARTIAL_SUCCESS/FAILURE
cleanup: []
idempotency:
  level: data_level
  note: 批处理逐座位执行且无防重，重复提交会重复下发禁网指令；教室级状态重复设置幂等
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/network/disable

> 教室批量禁网：先同步设置教室级网络状态并通知CMR，再对教室下所有座位提交禁网批处理任务 ｜ @EnableAuthority ｜ async_batch

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/network/disable<br>教室批量禁网：先同步设置教室级网络状态并通知CMR，再对教室下所有座位提交禁网批<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert request/builder/sessionContext 非空"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: doBatchDisableNetwork：对每个教室 classroomAPI"]
        C4["Step4: seatAPI.getSeatIdArr(classroomIdList) 取座"]
        C5["Step5: 按 NetStateEnum.DISABLE_NETWORK/ENABLE_NE"]
        C6["Step6: 构造 DisableSeatNetworkBatchTaskHandler 或 "]
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
| URL | /rcc/classroom/network/disable |
| Controller | RccClassroomManageController |
| 方法名 | batchDisableNetwork |
| 权限注解 | @EnableAuthority |
| 执行方式 | async_batch |
| 业务含义 | 教室批量禁网：先同步设置教室级网络状态并通知CMR，再对教室下所有座位提交禁网批处理任务 |

## 入参详情

### BatchDisableNetworkRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomIdArr | UUID[] | 是 | @NotEmpty 非空 | 教室ID列表 |
| disableNetwork | Boolean | 是 | @NotNull 非空 | true=禁网，false=解禁/恢复网络 |

## 出参详情

| 返回类型 | DefaultWebResponse<BatchTaskSubmitResult|SuccessResultResponse> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| taskId | UUID | 无座位时为空，有座位时为禁网批处理任务ID |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 批量处理器：DisableSeatNetworkBatchTaskHandler / EnableSeatNetworkBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | processItem 逐座位 seatAPI.disableSingleSeatNetwork(seatId, DISABLE/ENABLE_NETWORK) 并记录成功/失败审计 |
| 2 | onFinish 调 seatAPI.refreshDeskInfo(classroomId) 刷新桌面信息，返回成功/失败/部分成功 |

### 处理流程

1. Assert request/builder/sessionContext 非空
2. rccPermissionChecker.checkTerminalGroupPermissionByClassroomId(classroomIdArr, sessionContext) 校验终端组权限
3. doBatchDisableNetwork：对每个教室 classroomAPI.disableClassroomNetwork(netStateEnum, classroomId) + cmrClientAPI.notifyClassroomInfoChange + 记录禁网/解禁审计日志
4. seatAPI.getSeatIdArr(classroomIdList) 取座位；空则直接返回 RCDC_RCC_MODULE_OPERATE_SUCCESS
5. 按 NetStateEnum.DISABLE_NETWORK/ENABLE_NETWORK 分别走 getBatchDisableDefaultWebResponse / getBatchEnableDefaultWebResponse
6. 构造 DisableSeatNetworkBatchTaskHandler 或 EnableSeatNetworkBatchTaskHandler，enableParallel + enablePerformanceMode(线程数) 提交批处理

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | classroomIdArr | @NotEmpty 非空 | webmvc 参数校验异常 |
| request | disableNetwork | @NotNull 非空 | webmvc 参数校验异常 |
| business | classroomIdArr | 管理员需具备所有目标教室的终端组数据权限 | rccPermissionChecker 抛出权限异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomIdArr | user_input/from_query | 按业务构造 |
| disableNetwork | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教室无座位 | $.status=="SUCCESS"；$.msgKey==RCDC_RCC_MODULE_OPERATE_SUCCESS |
| 教室有座位 | $.status=="SUCCESS"；$.content.taskId 非空（批处理任务已提交） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 无终端组权限 | 任一教室不在管理员权限范围 | status==ERROR；msgKey==RCDC_SAPCE_DATA_PERMISSION_DENIED |
| 个别座位下发失败 | 座位终端离线 | $.status=="SUCCESS"；轮询终态任务结果 PARTIAL_SUCCESS/FAILURE |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | low |
| 说明 | 批处理逐座位执行且无防重，重复提交会重复下发禁网指令；教室级状态重复设置幂等 |
