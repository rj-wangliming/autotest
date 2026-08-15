---
version: '2.0'
api:
  url: /rcc/classroom/desktop/tci/shutdown
  method: POST
  name: 关闭TCI云桌面：权限校验后批量下发TCI桌面关机指令；教师桌面走教室教师机通道，学生桌面走座位通道。
  controller: TCIDesktopOperateController
  method_ref: shutdownTCIDesktop
  permission: '@EnableAuthority'
  exec_mode: batch
  async: false
  description: 关闭TCI云桌面：权限校验后批量下发TCI桌面关机指令；教师桌面走教室教师机通道，学生桌面走座位通道。
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
  purpose: 查询教室列表获取classroomId（ViewClassroomInfoEntity.classroomId）；按教室名精确过滤查询教室列表（matchArr.fieldName=classroomName），取 classroomId
  request:
    body:
      matchArr:
      - type: EXACT
        fieldName: classroomName
        valueArr:
        - ${param.classroom_name}
        matchRule: EQ
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
- name: assign_student_image
  api: POST /rcc/classroom/image/student/create
  purpose: 分配学生机镜像——首镜像+有座位时批量创建云桌面（桌面在此诞生），轮询批任务完成后桌面存在
  request:
    body:
      crId:
        value: ${prev.query_classroom.output.classroomId}
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
- name: query_desktop_arr
  api: POST /rcc/classroom/desktop/list
  purpose: 分配镜像后查询桌面列表，产出 desktopIdArr 供操作步骤 idArr 使用
  extract:
    desktopIdArr: $.content.itemArr[*].desktopId
- name: query_desktop
  api: POST /rcc/classroom/desktop/list
  extract:
    desktopId: $.content.itemArr[0].desktopId
  purpose: 按桌面名过滤（matchArr.fieldName=computerName）
  request:
    body:
      matchArr:
      - type: FUZZY
        fieldNameArr:
        - computerName
        value: ${param.computer_name}
        matchRule: LIKE
request:
  dto: IdArrWebRequest
  body:
    idArr:
      type: UUID[]
      required: true
      constraint: '@NotEmpty 非空'
      description: TCI云桌面ID数组
      value: ${prev.query_desktop_arr.output.desktopIdArr}
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    content:
      type: BatchTaskSubmitResult
      description: 批量任务提交结果
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
- api: POST /rcc/classroom/desktop/list
  produces: $.content.itemArr[*].desktopId
  purpose: 桌面ID数组来自桌面列表查询出参（ViewDesktopResultDTO.desktopId）
downstream:
- api: 内部调用:ClassroomTeacherAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: idArr
  rule: 非空
  failure: 参数校验失败（@NotEmpty）
- level: PERM
  field: session
  rule: 当前用户需有对应终端分组权限
  failure: 权限校验抛异常
- level: BIZ
  field: desktop
  rule: 桌面必须存在教室桌面关联
  failure: getRelationByDeskId 返回 null 时抛 IllegalArgumentException
- level: BIZ
  field: desktop
  rule: 桌面须处于运行中（RUNNING）
  failure: 非运行中桌面关机指令无效；学生桌面无独立开机接口，运行中状态须通过上课（POST /rcc/classroom/cmrcef/lesson/start）间接达成
assertions:
  success:
  - scenario: 单台关机（idArr 长度1）
    expect: status==SUCCESS；content.taskId 非空；content.taskName==RCDC_RCC_TCI_DESKTOP_SHUTDOWN_SINGLE_TASK_NAME；轮询 taskId 终态 batchTaskItemStatus==SUCCESS
  - scenario: 批量关机（idArr 多台）
    expect: status==SUCCESS；content.taskId 非空；content.taskName==RCDC_RCC_TCI_DESKTOP_SHUTDOWN_BATCH_TASK_NAME；任务 enableParallel；逐台 batchTaskItemStatus==SUCCESS
  failure:
  - scenario: 无终端组权限
    trigger: 当前用户非管理员且无对应教室终端组权限
    expect: 请求阶段失败：status==ERROR（权限类 msgKey，checkTerminalGroupPermissionByDeskId 抛出）
  - scenario: 单台桌面不存在
    trigger: idArr 长度1 且 getDeskIDV(id) 查不到 IDV 桌面
    expect: 提交前失败：status==ERROR（BusinessException，任务未提交）
  - scenario: 单台关机失败
    trigger: 终端离线/平台异常（shutdownDesktop 抛 BusinessException）
    expect: 任务已提交：status==SUCCESS；content.taskId 非空；轮询 taskId 终态 batchTaskItemStatus==FAILURE；对应项 msgKey==rcdc_rcc_tci_desktop_shutdown_item_fail_desc（单条任务时 finish msgKey==rcdc_rcc_tci_desktop_shutdown_single_fail）；审计 RCDC_RCC_TCI_DESKTOP_SHUTDOWN_FAIL_LOG
cleanup: []
prereq_state:
  resource: desktop
  required_state: RUNNING
  achieve_via:
  - api: POST /rcc/classroom/cmrcef/lesson/start
    note: 学生桌面无独立开机接口，只能通过上课批量开机

idempotency:
  level: data_level
  note: 关机为有状态操作，任务级不幂等
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
  - name: desktop_name
    desc: ''
    used_by: 见 setup/request
  - name: computer_name
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
    used_by: setup/request
---
# POST /rcc/classroom/desktop/tci/shutdown

> 关闭TCI云桌面：权限校验后批量下发TCI桌面关机指令；教师桌面走教室教师机通道，学生桌面走座位通道。 ｜ @EnableAuthority ｜ batch

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/desktop/list"]
    end
    B["POST /rcc/classroom/desktop/tci/shutdown<br>关闭TCI云桌面：权限校验后批量下发TCI桌面关机指令；教师桌面走教室教师机通道<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: 断言 request/builder/session 非空"]
        C2["Step2: 权限校验（idArr）"]
        C3["Step3: 构建任务项迭代器，applicationContext.getBean(Shut"]
        C4["Step4: 单条查询计算机名设置单任务描述，多条 enableParallel"]
        C5["Step5: 提交批量任务返回结果"]
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
| URL | /rcc/classroom/desktop/tci/shutdown |
| Controller | TCIDesktopOperateController |
| 方法名 | shutdownTCIDesktop |
| 权限注解 | @EnableAuthority |
| 执行方式 | batch |
| 业务含义 | 关闭TCI云桌面：权限校验后批量下发TCI桌面关机指令；教师桌面走教室教师机通道，学生桌面走座位通道。 |

## 入参详情

### IdArrWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| idArr | UUID[] | 是 | @NotEmpty 非空 | TCI云桌面ID数组 |

## 出参详情

| 返回类型 | DefaultWebResponse |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| content | BatchTaskSubmitResult | 批量任务提交结果 |

## 上游前置业务

### 前置1：POST /rcc/classroom/desktop/list

桌面ID数组来自桌面列表查询出参（ViewDesktopResultDTO.desktopId）（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：ShutdownTCIDesktopBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | desktopMgmtAPI.getDeskIDV(desktopId) 取桌面名 |
| 2 | shutdownDesktop：classroomDesktopRelationService.getRelationByDeskId（null则抛IllegalArgumentException） |
| 3 | enableTeacher=true：classroomTeacherAPI.shutdownTeacherTCIDesktop(classroomId) |
| 4 | 否则：seatAPI.shutdownTCIDesktop(desktopId) |
| 5 | 成功记 RCDC_RCC_TCI_DESKTOP_SHUTDOWN_SUC_LOG，失败记 FAIL_LOG 并返回 FAILURE 项 |

### 处理流程

1. 断言 request/builder/session 非空
2. 权限校验（idArr）
3. 构建任务项迭代器，applicationContext.getBean(ShutdownTCIDesktopBatchTaskHandler)
4. 单条查询计算机名设置单任务描述，多条 enableParallel
5. 提交批量任务返回结果

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | idArr | 非空 | 参数校验失败（@NotEmpty） |
| PERM | session | 当前用户需有对应终端分组权限 | 权限校验抛异常 |
| BIZ | desktop | 桌面必须存在教室桌面关联 | getRelationByDeskId 返回 null 时抛 IllegalArgumentException |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| idArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

> 断言以 HTTP 响应为准（status + content.taskId + taskName），任务结果通过轮询 content.taskId 获取。依据源码：TCIDesktopOperateController.shutdownTCIDesktop(#135) → executeShutdownBatchTask(#151)；ShutdownTCIDesktopBatchTaskHandler.processItem(#72)。

### 成功场景（HTTP 响应级）

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 单台关机 | idArr 长度=1 | status==SUCCESS；content.taskId 非空；content.taskName==RCDC_RCC_TCI_DESKTOP_SHUTDOWN_SINGLE_TASK_NAME（先 getDeskIDV 查计算机名设任务描述）；轮询终态 batchTaskItemStatus==SUCCESS |
| 批量关机 | idArr 长度>1 | status==SUCCESS；content.taskId 非空；content.taskName==RCDC_RCC_TCI_DESKTOP_SHUTDOWN_BATCH_TASK_NAME；任务 enableParallel；逐台 batchTaskItemStatus==SUCCESS |

### 失败场景（HTTP 响应级）

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 无终端组权限 | 非管理员且无对应教室终端组权限 | 请求阶段拒绝：status==ERROR（checkTerminalGroupPermissionByDeskId 抛出权限类异常） |
| 单台桌面不存在 | idArr 长度=1 且 getDeskIDV(id) 查无此 IDV 桌面 | 提交前失败：status==ERROR（BusinessException，任务未提交，无 taskId） |
| 单台关机指令失败 | 终端离线/平台异常（shutdownDesktop 抛 BusinessException） | 任务已提交：status==SUCCESS；content.taskId 非空；轮询 taskId 终态 batchTaskItemStatus==FAILURE；对应项 msgKey==rcdc_rcc_tci_desktop_shutdown_item_fail_desc（单条任务时 finish msgKey==rcdc_rcc_tci_desktop_shutdown_single_fail）；审计记录 RCDC_RCC_TCI_DESKTOP_SHUTDOWN_FAIL_LOG |
| 参数校验 | idArr 为空 | status==ERROR（参数校验 @NotEmpty） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | low |
| 说明 | 关机为有状态操作，任务级不幂等 |
