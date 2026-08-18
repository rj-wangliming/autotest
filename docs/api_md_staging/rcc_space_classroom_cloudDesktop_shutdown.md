---
version: '2.0'
api:
  url: /rcc/space/classroom/cloudDesktop/shutdown
  method: POST
  name: 教学桌面池教室下所有云桌面正常关机。idArr[0] 教室ID → 查询教室云桌面ID（含权限过滤）→ 空则成功返回 → ShutdownDesktopBatc
  controller: RccSpaceController
  method_ref: shutdown
  permission: '@EnableAuthority'
  exec_mode: 批量异步（BatchTask）
  async: true
  description: 教学桌面池教室下所有云桌面正常关机。idArr[0] 教室ID → 查询教室云桌面ID（含权限过滤）→ 空则成功返回 → ShutdownDesktopBatchTaskHandler 批量任务（单台 SINGLE_TASK / 多台 enableParallel，itemName=RCDC_RCC_DESKTOP_SHUTDOWN_ITEM_NAME）。
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
  purpose: 获取计算集群ID与云平台ID（取第一条，无名称过滤）
- name: get_storage_pool
  api: POST /space/storagePool/list
  extract:
    storagePoolId: $.content.items[0].storagePoolId
  purpose: 获取存储池ID（镜像分配用）（取第一条，无名称过滤）
- name: get_network
  api: POST /space/clouddesktop/deskNetwork/list
  extract:
    networkId: $.content.itemArr[0].id
  purpose: 获取网络ID（镜像分配用）（取第一条，无名称过滤）
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
        value: ${prev.create_vdi_strategy.output.vdiStrategyId}
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
      description: 教室ID数组，取 idArr[0]
      value: ${prev.select_classroom_id.output.classroomId}
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
      description: 任务状态
polling:
  api: common_get_msgct_detail_info
  # 公共轮询接口：POST /rco/msgct/msg/detail（消息中心），完整文档见 common_get_msgct_detail_info.md
  method: POST
  params:
    msgrelationid: ${content.taskId}
  optional_when_no_correlation: true
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
- api: 内部调用:rcc/RccDesktopOperateAPI#shutdown
  purpose: 内部调用（非 HTTP 端点）
- api: 内部调用:rcc/RccDesktopOperateAPI#shutdownAutoEdit
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: idArr
  rule: '@NotNull @NotEmpty'
  failure: Assert 失败
- level: BUSINESS
  field: classroomId
  rule: 无桌面直接成功
  failure: 空任务
- level: BUSINESS
  field: classroomTerminalGroupId
  rule: 非超管权限过滤
  failure: 权限外桌面不操作
assertions:
  success:
  - scenario: 教室存在云桌面且未在自动编辑
    expect: 提交正常关机批量任务；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  - scenario: 桌面处于自动编辑状态
    expect: 任务项执行 shutdownAutoEdit 关机；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  failure:
  - scenario: 无桌面
    trigger: 教室下无云桌面
    expect: $.status==SUCCESS（无 taskId）
  - scenario: 关机命令下发失败
    trigger: 桌面状态异常
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
  note: 重复提交重复下发关机命令
params:
  required:
  - name: classroom_name
  - name: classroom_strategy_name
  - name: image_name
  - name: student_image_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/space/classroom/cloudDesktop/shutdown

> 教学桌面池教室下所有云桌面正常关机。idArr[0] 教室ID → 查询教室云桌面ID（含权限过滤）→ 空则成功返回 → ShutdownDesktopBatchTaskHandler 批量任务（单台 SINGLE_TASK / 多台 enableParallel，itemName=RCDC_RCC_DESKTOP_SHUTDOWN_ITEM_NAME）。 ｜ @EnableAuthority ｜ 批量异步（BatchTask）

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create"]
    end
    B["POST /rcc/space/classroom/cloudDesktop/shutdown<br>教学桌面池教室下所有云桌面正常关机。idArr[0] 教室ID → 查询教室云桌<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(classroomId/builder/sessi"]
        C2["Step2: newRequestBuilderForTop1000() + eq(class"]
        C3["Step3: 空则返回 DefaultWebResponse.success()"]
        C4["Step4: 构造 DefaultBatchTaskItem（itemName=RCDC_RC"]
        C5["Step5: 构造 ShutdownDesktopBatchTaskHandler 注入 de"]
        C6["Step6: executeShutdownBatchTask：单台 SINGLE_TASK "]
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
| URL | /rcc/space/classroom/cloudDesktop/shutdown |
| Controller | RccSpaceController |
| 方法名 | shutdown |
| 权限注解 | @EnableAuthority |
| 执行方式 | 批量异步（BatchTask） |
| 业务含义 | 教学桌面池教室下所有云桌面正常关机。idArr[0] 教室ID → 查询教室云桌面ID（含权限过滤）→ 空则成功返回 → ShutdownDesktopBatchTaskHandler 批量任务（单台 SINGLE_TASK / 多台 enableParallel，itemName=RCDC_RCC_DESKTOP_SHUTDOWN_ITEM_NAME）。 |

## 入参详情

### IdArrWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| idArr | UUID[] | 是 | @NotNull @NotEmpty | 教室ID数组，取 idArr[0] |

## 出参详情

| 返回类型 | DefaultWebResponse（data=BatchTaskSubmitResult） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| taskId | UUID | 批量任务ID |
| taskStatus | String | 任务状态 |

## 上游前置业务

### 前置1：POST /rcc/classroom/create

教室ID（IdArrWebRequest），来源为教室创建返回（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：ShutdownDesktopBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | desktopMgmtAPI.getDesktopById(itemId) 取桌面名 |
| 2 | desktopMgmtAPI.getTerminalIdWhenDeskInAutoEdit(desktopId)：若桌面处于自动编辑，则 desktopOperateAPI.shutdownAutoEdit(ShutdownAutoEditDesktopDTO{desktopId, terminalId}) |
| 3 | 否则 desktopOperateAPI.shutdown(ShutdownDesktopDTO{desktopId, shutdownByAdmin=true}) 正常关机 |
| 4 | 成功：auditLogAPI.recordLog(RCDC_RCC_DESKTOP_SHUTDOWN_SUC_LOG) |
| 5 | 失败：recordLog(RCDC_RCC_DESKTOP_SHUTDOWN_FAIL_LOG)，返回 FAILURE |
| 6 | onFinish：单台 RCDC_RCC_DESKTOP_SHUTDOWN_SINGLE_SUC/FAIL，多台 RCDC_RCC_DESKTOP_SHUTDOWN_BATCH_RESULT |

### 处理流程

1. Assert.notNull(classroomId/builder/sessionContext)
2. newRequestBuilderForTop1000() + eq(classroomId, idArr[0])，getSpaceClassroomDesktopIds 获取桌面ID
3. 空则返回 DefaultWebResponse.success()
4. 构造 DefaultBatchTaskItem（itemName=RCDC_RCC_DESKTOP_SHUTDOWN_ITEM_NAME）
5. 构造 ShutdownDesktopBatchTaskHandler 注入 desktopOperateAPI/desktopMgmtAPI/desktopDiskMgmtAPI
6. executeShutdownBatchTask：单台 SINGLE_TASK 命名，多台 enableParallel 批量任务
7. 返回 BatchTaskSubmitResult

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | idArr | @NotNull @NotEmpty | Assert 失败 |
| BUSINESS | classroomId | 无桌面直接成功 | 空任务 |
| BUSINESS | classroomTerminalGroupId | 非超管权限过滤 | 权限外桌面不操作 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| idArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

> ⚠️ 断言以 HTTP 响应为准（status + msgKey / BatchTaskSubmitResult），非服务端审计日志。

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教室存在云桌面且未在自动编辑 | 提交正常关机批量任务 |
| 桌面处于自动编辑状态 | 任务项执行 shutdownAutoEdit 关机 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 无桌面 | 教室下无云桌面 | $.status==SUCCESS（无 taskId） |
| 关机命令下发失败 | 桌面状态异常 | 轮询 content.taskId 至终态 batchTaskItemStatus∈["FAILURE"] |
## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | LOW |
| 说明 | 重复提交重复下发关机命令 |
