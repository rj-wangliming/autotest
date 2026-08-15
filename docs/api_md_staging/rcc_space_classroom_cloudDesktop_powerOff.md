---
version: '2.0'
api:
  url: /rcc/space/classroom/cloudDesktop/powerOff
  method: POST
  name: 教学桌面池教室下所有云桌面强制关机。入参 idArr[0] 为教室ID；先按 classroomId 查询该教室云桌面ID列表（含终端组数据权限过滤），无桌面则
  controller: RccSpaceController
  method_ref: powerOff
  permission: '@EnableAuthority'
  exec_mode: 批量异步（BatchTask）
  async: true
  description: 教学桌面池教室下所有云桌面强制关机。入参 idArr[0] 为教室ID；先按 classroomId 查询该教室云桌面ID列表（含终端组数据权限过滤），无桌面则直接返回成功；为每个桌面构造 BatchTaskItem（RCDC_RCC_DESKTOP_POWEROFF_ITEM_NAME，distinct 去重），注册 RccPowerOffDesktopBatchTaskHandler 提交批量
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: create_classroom
  api: POST /rcc/classroom/create
  purpose: 创建教室产生 classroomId
  request:
    body:
      classroomName: ${param.classroom_name}
  idempotent: recreate
  delete_api: /rcc/classroom/delete
  delete_param: classroomId
- name: select_classroom_id
  api: POST /rcc/classroom/select
  purpose: 按名称过滤查询教室（searchKeyword=${param.classroom_name}）
  extract:
    classroomId: $.content[0].classroomId
  request:
    body:
      searchKeyword: ${param.classroom_name}
- name: get_strategy
  api: POST /rcc/classroom/strategy/list
  extract:
    strategyId: $.content.itemArr[0].classroomStrategyId
  purpose: 按策略名精确过滤（matchArr.fieldName=classroomStrategyName）
  request:
    body:
      matchArr:
      - type: EXACT
        fieldName: classroomStrategyName
        valueArr:
        - ${param.classroom_strategy_name}
        matchRule: EQ
- name: get_image
  api: POST /rcc/classroom/image/assignImage/yetAssign/list
  extract:
    plusImageId:
      from: $.content.itemArr
      pick: max
      sort_key: cbbImageTemplateDetailDTO.name
      field: cbbImageTemplateDetailDTO.id
  purpose: 按镜像名精确过滤（searchKeyword + matchArr.fieldName=imageName）；同名多版本取模板名最大
  request:
    body:
      searchKeyword: ${param.student_image_name}
      matchArr:
      - type: EXACT
        fieldName: imageName
        valueArr:
        - ${param.image_name}
        matchRule: EQ
- name: get_cluster
  api: POST /space/cluster/obtainComputeClusterList
  extract:
    clusterId: $.content.itemArr[0].computerClusterId
    platformId: $.content.itemArr[0].platformId
  purpose: 获取计算集群ID与云平台ID
- name: get_storage_pool
  api: POST /space/storagePool/list
  extract:
    storagePoolId: $.content.itemArr[0].storagePoolId
  purpose: 获取存储池ID（镜像分配用）
- name: get_network
  api: POST /space/clouddesktop/deskNetwork/list
  extract:
    networkId: $.content.itemArr[0].id
  purpose: 获取网络ID（镜像分配用）
- name: create_seat
  api: POST /rcc/classroom/seat/batchCreate
  purpose: 批量创建座位（异步批任务）；桌面在「分配学生机镜像」时批量创建，座位必须先存在
  idempotent: recreate
  delete_api: /rcc/classroom/seat/delete
  delete_param: seatIdArr
  request:
    body:
      classroomId: ${prev.select_classroom_id.output.classroomId}

- name: assign_student_image
  api: POST /rcc/classroom/image/student/create
  purpose: 分配学生机镜像——首镜像+有座位时批量创建云桌面（桌面在此诞生），轮询批任务完成后桌面存在
  request:
    body:
      crId:
        value: ${prev.select_classroom_id.output.classroomId}
      plusImageId:
        value: ${prev.get_image.output.plusImageId}
      enableHide:
        value: false
      storagePoolIdList:
        value: ${prev.get_storage_pool.output.storagePoolId}
      clusterId:
        value: ${prev.get_cluster.output.clusterId}
      platformId:
        value: ${prev.get_cluster.output.platformId}
      strategyId:
        value: ${prev.get_strategy.output.strategyId}
      networkId:
        value: ${prev.get_network.output.networkId}
  idempotent: recreate
  delete_api: /rcc/classroom/image/student/delete
  delete_param: id
- name: query_desktop
  api: POST /rcc/classroom/desktop/list
  purpose: 分配镜像后查询桌面列表，产出 desktopIdArr 供操作步骤 idArr 使用
  extract:
    desktopIdArr: $.content.itemArr[*].desktopId
request:
  dto: IdArrWebRequest
  body:
    idArr:
      type: UUID[]
      required: true
      constraint: '@NotNull @NotEmpty'
      description: 教室ID数组，取 idArr[0] 作为目标教室
      value: ${prev.query_desktop.output.desktopIdArr}
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
      description: 批量任务ID
    taskStatus:
      type: String
      description: 任务状态（PENDING/RUNNING 等）
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
- api: POST /rcc/classroom/create
  produces: $.content.classroomId
  purpose: 教室ID（IdArrWebRequest），来源为教室创建返回
downstream:
- api: 内部调用:rcc/RccDesktopOperateAPI#powerOff
  purpose: 内部调用（非 HTTP 端点）
- api: 内部调用:rcc/RccDesktopMgmtAPI#getDesktopById
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: idArr
  rule: '@NotNull @NotEmpty，不能为空'
  failure: Assert 失败抛 IllegalArgumentException
- level: BUSINESS
  field: classroomId
  rule: 教室下无云桌面时直接成功
  failure: 无桌面返回空任务
- level: BUSINESS
  field: classroomTerminalGroupId
  rule: 非超管只对权限内终端组的教室桌面操作
  failure: 权限外桌面不纳入任务
assertions:
  success:
  - scenario: 教室下存在多台云桌面
    expect: 提交批量强制关机任务，返回 BatchTaskSubmitResult；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  - scenario: 教室下仅1台桌面
    expect: 提交单任务（SINGLE_TASK 命名），返回 BatchTaskSubmitResult；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  failure:
  - scenario: 教室下无云桌面
    trigger: idArr[0] 教室无桌面
    expect: $.status==SUCCESS（无 taskId）
  - scenario: 桌面已关机/不存在
    trigger: 任务执行时桌面状态异常
    expect: 轮询 content.taskId 至终态 batchTaskItemStatus∈["FAILURE"]
cleanup: []
prereq_state:
  resource: desktop
  required_state: RUNNING
  achieve_via:
  - api: POST /rcc/classroom/cmrcef/lesson/start
    note: 学生桌面无独立开机接口，只能通过上课批量开机

idempotency:
  level: data_level
  note: 每次调用都会重新下发强制关机命令，重复提交产生重复命令与重复审计日志
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/space/classroom/cloudDesktop/powerOff

> 教学桌面池教室下所有云桌面强制关机。入参 idArr[0] 为教室ID；先按 classroomId 查询该教室云桌面ID列表（含终端组数据权限过滤），无桌面则直接返回成功；为每个桌面构造 BatchTaskItem（RCDC_RCC_DESKTOP_POWEROFF_ITEM_NAME，distinct 去重），注册 RccPowerOffDesktopBatchTaskHandler 提交批量任务；1台桌面走单任务命名（RCDC_RCC_DESKTOP_POWEROFF_SINGLE_TASK_NAME/DESC），多台 enableParallel 批量任务（BATCH_TASK_NAME/DESC）。 ｜ @EnableAuthority ｜ 批量异步（BatchTask）

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create"]
    end
    B["POST /rcc/space/classroom/cloudDesktop/powerOff<br>教学桌面池教室下所有云桌面强制关机。入参 idArr[0] 为教室ID；先按 c<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(classroomId/builder/sessi"]
        C2["Step2: newRequestBuilderForTop1000()，requestBui"]
        C3["Step3: 云桌面数组为空直接返回 DefaultWebResponse.success()"]
        C4["Step4: 为每个桌面ID构造 DefaultBatchTaskItem（distinct "]
        C5["Step5: 构造 RccPowerOffDesktopBatchTaskHandler 并注"]
        C6["Step6: executePowerOffTask：单台走 SINGLE_TASK（取桌面名"]
        C1 --> C2
        C7["Step7: 返回 BatchTaskSubmitResult"]
        C6 --> C7
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
| URL | /rcc/space/classroom/cloudDesktop/powerOff |
| Controller | RccSpaceController |
| 方法名 | powerOff |
| 权限注解 | @EnableAuthority |
| 执行方式 | 批量异步（BatchTask） |
| 业务含义 | 教学桌面池教室下所有云桌面强制关机。入参 idArr[0] 为教室ID；先按 classroomId 查询该教室云桌面ID列表（含终端组数据权限过滤），无桌面则直接返回成功；为每个桌面构造 BatchTaskItem（RCDC_RCC_DESKTOP_POWEROFF_ITEM_NAME，distinct 去重），注册 RccPowerOffDesktopBatchTaskHandler 提交批量任务；1台桌面走单任务命名（RCDC_RCC_DESKTOP_POWEROFF_SINGLE_TASK_NAME/DESC），多台 enableParallel 批量任务（BATCH_TASK_NAME/DESC）。 |

## 入参详情

### IdArrWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| idArr | UUID[] | 是 | @NotNull @NotEmpty | 教室ID数组，取 idArr[0] 作为目标教室 |

## 出参详情

| 返回类型 | DefaultWebResponse（data=BatchTaskSubmitResult） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| taskId | UUID | 批量任务ID |
| taskStatus | String | 任务状态（PENDING/RUNNING 等） |

## 上游前置业务

### 前置1：POST /rcc/classroom/create

教室ID（IdArrWebRequest），来源为教室创建返回（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：RccPowerOffDesktopBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | desktopMgmtAPI.getDesktopById(itemId) 查询桌面并取名称 |
| 2 | 构造 ShutdownDesktopDTO{desktopId, shutdownByAdmin=true} |
| 3 | desktopOperateAPI.powerOff(shutdownDesktopDTO) 下发强制关机命令 |
| 4 | 成功：auditLogAPI.recordLog(RCDC_RCC_DESKTOP_POWEROFF_SUC_LOG) |
| 5 | 失败：recordLog(RCDC_RCC_DESKTOP_POWEROFF_FAIL_LOG)，返回 FAILURE 任务项 |
| 6 | onFinish：单台 RCDC_RCC_DESKTOP_POWEROFF_SINGLE_SUC/FAIL，多台 RCDC_RCC_DESKTOP_POWEROFF_BATCH_RESULT |

### 处理流程

1. Assert.notNull(classroomId/builder/sessionContext)
2. newRequestBuilderForTop1000()，requestBuilder.eq(classroomId, idArr[0])，getSpaceClassroomDesktopIds 查询教室云桌面ID数组
3. 云桌面数组为空直接返回 DefaultWebResponse.success()
4. 为每个桌面ID构造 DefaultBatchTaskItem（distinct 去重，itemName=RCDC_RCC_DESKTOP_POWEROFF_ITEM_NAME）
5. 构造 RccPowerOffDesktopBatchTaskHandler 并注入 desktopOperateAPI/desktopMgmtAPI
6. executePowerOffTask：单台走 SINGLE_TASK（取桌面名做 desc），多台 enableParallel 批量任务
7. 返回 BatchTaskSubmitResult

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | idArr | @NotNull @NotEmpty，不能为空 | Assert 失败抛 IllegalArgumentException |
| BUSINESS | classroomId | 教室下无云桌面时直接成功 | 无桌面返回空任务 |
| BUSINESS | classroomTerminalGroupId | 非超管只对权限内终端组的教室桌面操作 | 权限外桌面不纳入任务 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| idArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

> ⚠️ 断言以 HTTP 响应为准（status + msgKey / BatchTaskSubmitResult），非服务端审计日志。

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教室下存在多台云桌面 | 提交批量强制关机任务，返回 BatchTaskSubmitResult |
| 教室下仅1台桌面 | 提交单任务（SINGLE_TASK 命名），返回 BatchTaskSubmitResult |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 教室下无云桌面 | idArr[0] 教室无桌面 | $.status==SUCCESS（无 taskId） |
| 桌面已关机/不存在 | 任务执行时桌面状态异常 | 轮询 content.taskId 至终态 batchTaskItemStatus∈["FAILURE"] |
## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | LOW |
| 说明 | 每次调用都会重新下发强制关机命令，重复提交产生重复命令与重复审计日志 |
