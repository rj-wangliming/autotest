---
version: '2.0'
api:
  url: /rcc/classroom/desktop/restart
  method: POST
  name: 重启课堂云桌面：对指定VDI桌面批量下发重启指令。
  controller: RccClassroomDesktopController
  method_ref: restart
  permission: '@EnableAuthority'
  exec_mode: batch
  async: false
  description: 重启课堂云桌面：对指定VDI桌面批量下发重启指令。
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
  api: POST /rcc/classroom/select
  extract:
    classroomId: $.content[0].classroomId
  purpose: 查询教室列表获取classroomId（ViewClassroomInfoEntity.classroomId）；按教室名精确过滤查询教室列表（matchArr.fieldName=classroomName），取 classroomId
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
  purpose: 批量创建座位（异步批处理任务）；若教室已分配学生镜像，新座位随建桌面
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
- name: get_vdi_disk_storage
  api: POST /rcc/classroom/getClassroomVdiDiskStorage
  extract:
    vdiDiskStorageId: $.content.vdiDiskStorageId
  purpose: 查询教室VDI数据盘存储池ID（分配学生镜像用）
  request:
    body:
      classroomId: ${prev.query_classroom.output.classroomId}
      clusterId: ${prev.get_cluster.output.clusterId}
      platformId: ${prev.get_cluster.output.platformId}
      enableTeacher: false
- name: assign_student_image
  api: POST /rcc/classroom/image/student/create
  purpose: 给学生机教室分配课程镜像（桌面存在的必要条件）。桌面诞生规则：已分配镜像时新建座位随座位建桌面；座位已存在时首镜像分配批量建桌面；未分配镜像则教室无桌面
  request:
    body:
      crId: ${prev.query_classroom.output.classroomId}
      plusImageId: ${prev.get_image.output.plusImageId}
      enableHide: false
      storagePoolIdList: ${prev.get_storage_pool.output.storagePoolId}
      clusterId: ${prev.get_cluster.output.clusterId}
      platformId: ${prev.get_cluster.output.platformId}
      strategyId: ${prev.get_strategy.output.strategyId}
      networkId: ${prev.get_network.output.networkId}
      desktopStartIp: ${param.student_start_ip}
      vdiDiskStorageId: ${prev.get_vdi_disk_storage.output.vdiDiskStorageId}
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
      description: 云桌面ID数组
      value: ${param.id_arr}
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
- api: 内部调用:RccDesktopOperateAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: idArr
  rule: 非空
  failure: 参数校验失败（@NotEmpty）
- level: BIZ
  field: desktop
  rule: 桌面必须存在
  failure: 单项失败 rcdc_rcc_desktop_restart_item_fail_desc
- level: BIZ
  field: desktop
  rule: 桌面须处于运行中（RUNNING）
  failure: 非运行中桌面重启无效；学生桌面无独立开机接口，运行中状态须通过上课（POST /rcc/classroom/cmrcef/lesson/start）间接达成
assertions:
  success:
  - scenario: 桌面存在且可重启
    expect: 批量任务提交成功，逐台重启成功；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  failure:
  - scenario: 桌面不存在或重启异常
    trigger: 桌面已删除或平台异常
    expect: $.status=="SUCCESS"；content.taskId 非空；轮询终态对应项 batchTaskItemStatus==FAILURE；对应项 msgKey==rcdc_rcc_desktop_restart_item_fail_desc（单条任务时 finish msgKey==rcdc_rcc_desktop_restart_single_fail）；rcdc_rcc_desktop_restart_fail_log 仅为审计日志 key，不是响应 msgKey
cleanup: []
prereq_state:
  resource: desktop
  required_state: RUNNING
  achieve_via:
  - api: POST /rcc/classroom/cmrcef/lesson/start
    note: 学生桌面无独立开机接口，只能通过上课批量开机

idempotency:
  level: data_level
  note: 重启是有状态操作，重复执行会反复重启桌面；任务级不幂等
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
  - name: desktop_name
    desc: ''
    used_by: 见 setup/request
  - name: computer_name
    desc: ''
    used_by: setup/request
  - name: student_image_name
    desc: ''
    used_by: setup（分配学生镜像按名查询）
  - name: image_name
    desc: ''
    used_by: setup（分配学生镜像按名精确过滤）
  - name: student_start_ip
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
    used_by: setup（分配学生镜像 desktopStartIp）
---
# POST /rcc/classroom/desktop/restart

> 重启课堂云桌面：对指定VDI桌面批量下发重启指令。 ｜ @EnableAuthority ｜ batch

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/desktop/list"]
    end
    B["POST /rcc/classroom/desktop/restart<br>重启课堂云桌面：对指定VDI桌面批量下发重启指令。<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: 断言 request 与 builder 非空"]
        C2["Step2: 取 idArr 构建任务项迭代器"]
        C3["Step3: 创建 RestartDesktopBatchTaskHandler 注入 des"]
        C4["Step4: 单条查询桌面计算机名设置单任务描述，多条 enableParallel"]
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
| URL | /rcc/classroom/desktop/restart |
| Controller | RccClassroomDesktopController |
| 方法名 | restart |
| 权限注解 | @EnableAuthority |
| 执行方式 | batch |
| 业务含义 | 重启课堂云桌面：对指定VDI桌面批量下发重启指令。 |

## 入参详情

### IdArrWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| idArr | UUID[] | 是 | @NotEmpty 非空 | 云桌面ID数组 |

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

### 批量处理器：RestartDesktopBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | desktopMgmtAPI.getDesktopById(desktopId) 取桌面名 |
| 2 | desktopOperateAPI.restart(desktopId) 执行重启 |
| 3 | 成功记 RCDC_RCC_DESKTOP_RESTART_SUC_LOG，失败记 FAIL_LOG 并返回 FAILURE 项 |

### 处理流程

1. 断言 request 与 builder 非空
2. 取 idArr 构建任务项迭代器
3. 创建 RestartDesktopBatchTaskHandler 注入 desktopOperateAPI/desktopMgmtAPI
4. 单条查询桌面计算机名设置单任务描述，多条 enableParallel
5. 提交批量任务返回结果

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | idArr | 非空 | 参数校验失败（@NotEmpty） |
| BIZ | desktop | 桌面必须存在 | 单项失败 rcdc_rcc_desktop_restart_item_fail_desc |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| idArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 桌面存在且可重启 | 批量任务提交成功，逐台重启成功；轮询 content.taskId 至终态 batchTaskItemStatus∈["SUCCESS"] |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 桌面不存在或重启异常 | 桌面已删除或平台异常 | $.status=="SUCCESS"；content.taskId 非空；轮询终态对应项 batchTaskItemStatus==FAILURE；对应项 msgKey==rcdc_rcc_desktop_restart_item_fail_desc（单条任务时 finish msgKey==rcdc_rcc_desktop_restart_single_fail）；rcdc_rcc_desktop_restart_fail_log 仅为审计日志 key，不是响应 msgKey |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | low |
| 说明 | 重启是有状态操作，重复执行会反复重启桌面；任务级不幂等 |
