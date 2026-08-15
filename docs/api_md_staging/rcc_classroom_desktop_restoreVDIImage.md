---
version: '2.0'
api:
  url: /rcc/classroom/desktop/restoreVDIImage
  method: POST
  name: VDI课堂云桌面批量还原：校验桌面角色一致、必须为个性桌面且处于关闭状态后，按指定镜像批量还原桌面系统盘。
  controller: RccClassroomDesktopController
  method_ref: restoreVDIImage
  permission: '@EnableAuthority'
  exec_mode: batch
  async: false
  description: VDI课堂云桌面批量还原：校验桌面角色一致、必须为个性桌面且处于关闭状态后，按指定镜像批量还原桌面系统盘。
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
  dto: RccRestoreVDIImageWebRequest
  body:
    imageId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 目标镜像模板ID
      value: ${prev.get_image.output.plusImageId}
    desktopIdList:
      type: List<UUID>
      required: true
      constraint: '@NotEmpty 非空'
      description: 待还原的桌面ID列表
      value: ${prev.query_desktop.output.desktopId}
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
      description: 批量任务提交结果（还原由后台异步执行）
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
- api: POST /rcc/classroom/image/list
  produces: $.content.itemArr[0].imageId
  purpose: 推断：镜像ID来源，字段名为推断
- api: POST /rcc/classroom/desktop/list
  produces: $.content.itemArr[*].desktopId
  purpose: 推断：待还原桌面ID列表来自桌面列表查询出参（ViewDesktopResultDTO.desktopId）
downstream:
- api: 内部调用:RccDesktopOperateAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: imageId
  rule: 非空
  failure: 参数校验失败（@NotNull）
- level: PARAM
  field: desktopIdList
  rule: 非空
  failure: 参数校验失败（@NotEmpty）
- level: BIZ
  field: desktopList
  rule: 所有桌面必须同为教师机或学生机角色且角色一致
  failure: RCDC_CLOUDDESKTOP_DESK_ROLE_ERROR（桌面角色不一致）
- level: BIZ
  field: desktopList
  rule: 桌面必须为个性桌面（PERSONAL）
  failure: RCDC_CLOUDDESKTOP_HAVE_NOT_PERSONAL_DESKTOP（存在非个性桌面）
- level: STATE
  field: desktop
  rule: 桌面必须处于关闭（CLOSE）状态
  failure: RCDC_CLOUDDESKTOP_DESKINFO_NOT_CLOSE_STATE_RESTORE_FORBID（非关
- level: BIZ
  field: desktopList
  rule: 桌面详情或角色不能为空
  failure: RCDC_CLOUDDESKTOP_INFO_IS_EMPTY
assertions:
  success:
  - scenario: 全部桌面为同角色个性桌面且关闭
    expect: 批量任务提交成功，逐台还原成功；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  failure:
  - scenario: 存在桌面非关闭状态
    trigger: 任一桌面状态非 CLOSE
    expect: status==ERROR；msgKey==rcdc-clouddesktop_deskinfo_not_close_state_restore_forbid
  - scenario: 存在非个性桌面
    trigger: desktopPattern 非 PERSONAL
    expect: status==ERROR；msgKey==rcdc-clouddesktop_have_not_personal_desktop
  - scenario: 桌面角色不一致
    trigger: 桌面角色与首台不一致或为空
    expect: status==ERROR；msgKey∈{rcdc-clouddesktop_desk_role_error, rcdc-clouddesktop_info_is_empty}
cleanup: []
idempotency:
  level: data_level
  note: 还原会覆盖桌面系统盘数据，重复执行会再次还原；执行前必须确认桌面为关闭状态
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
# POST /rcc/classroom/desktop/restoreVDIImage

> VDI课堂云桌面批量还原：校验桌面角色一致、必须为个性桌面且处于关闭状态后，按指定镜像批量还原桌面系统盘。 ｜ @EnableAuthority ｜ batch

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/image/list"]
        A2["POST /rcc/classroom/desktop/list"]
    end
    B["POST /rcc/classroom/desktop/restoreVDIImage<br>VDI课堂云桌面批量还原：校验桌面角色一致、必须为个性桌面且处于关闭状态后，按指<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    A2 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: 断言 request/builder/session 非空"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: desktopMgmtAPI.getDesktopPatternList 获取桌"]
        C4["Step4: checkRequestParam：角色一致（checkDesktopRole）"]
        C5["Step5: applicationContext.getBean(RccRestoreVDI"]
        C6["Step6: enableParallel 提交批量任务返回结果"]
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
| URL | /rcc/classroom/desktop/restoreVDIImage |
| Controller | RccClassroomDesktopController |
| 方法名 | restoreVDIImage |
| 权限注解 | @EnableAuthority |
| 执行方式 | batch |
| 业务含义 | VDI课堂云桌面批量还原：校验桌面角色一致、必须为个性桌面且处于关闭状态后，按指定镜像批量还原桌面系统盘。 |

## 入参详情

### RccRestoreVDIImageWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| imageId | UUID | 是 | @NotNull 非空 | 目标镜像模板ID |
| desktopIdList | List<UUID> | 是 | @NotEmpty 非空 | 待还原的桌面ID列表 |

## 出参详情

| 返回类型 | DefaultWebResponse |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| content | BatchTaskSubmitResult | 批量任务提交结果（还原由后台异步执行） |

## 上游前置业务

### 前置1：POST /rcc/classroom/image/list

推断：镜像ID来源，字段名为推断（由 field_map 契约映射）

### 前置2：POST /rcc/classroom/desktop/list

推断：待还原桌面ID列表来自桌面列表查询出参（ViewDesktopResultDTO.desktopId）（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：RccRestoreVDIDesktopHandler

| 步骤 | 说明 |
|---|---|
| 1 | getHandlerParam 构造 RestoreDesktopDTO{desktopId, imageId} |
| 2 | desktopMgmtAPI.getDesktopById 取桌面名 |
| 3 | desktopOperateAPI.restoreVDIDesktop(param) 执行还原 |
| 4 | 成功记 RCDC_RCC_DESKTOP_REVERT_SUC_LOG，失败记 FAIL_LOG 并返回 FAILURE 项 |

### 处理流程

1. 断言 request/builder/session 非空
2. rccPermissionChecker.checkTerminalGroupPermissionByDeskId(desktopIdList, session) 权限校验
3. desktopMgmtAPI.getDesktopPatternList 获取桌面详情列表
4. checkRequestParam：角色一致（checkDesktopRole）、个性桌面（checkDesktopPattern）、关闭状态（checkDesktopStatus）
5. applicationContext.getBean(RccRestoreVDIDesktopHandler) 构建批量处理器
6. enableParallel 提交批量任务返回结果

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | imageId | 非空 | 参数校验失败（@NotNull） |
| PARAM | desktopIdList | 非空 | 参数校验失败（@NotEmpty） |
| BIZ | desktopList | 所有桌面必须同为教师机或学生机角色且角色一致 | RCDC_CLOUDDESKTOP_DESK_ROLE_ERROR（桌面角色不一致） |
| BIZ | desktopList | 桌面必须为个性桌面（PERSONAL） | RCDC_CLOUDDESKTOP_HAVE_NOT_PERSONAL_DESKTOP（存在非个性桌面） |
| STATE | desktop | 桌面必须处于关闭（CLOSE）状态 | RCDC_CLOUDDESKTOP_DESKINFO_NOT_CLOSE_STATE_RESTORE_FORBID（非关闭状态禁止还原） |
| BIZ | desktopList | 桌面详情或角色不能为空 | RCDC_CLOUDDESKTOP_INFO_IS_EMPTY |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| imageId | user_input/from_query | 按业务构造 |
| desktopIdList | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 全部桌面为同角色个性桌面且关闭 | 批量任务提交成功，逐台还原成功；轮询 content.taskId 至终态 batchTaskItemStatus∈["SUCCESS"] |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 存在桌面非关闭状态 | 任一桌面状态非 CLOSE | status==ERROR；msgKey==rcdc-clouddesktop_deskinfo_not_close_state_restore_forbid |
| 存在非个性桌面 | desktopPattern 非 PERSONAL | status==ERROR；msgKey==rcdc-clouddesktop_have_not_personal_desktop |
| 桌面角色不一致 | 桌面角色与首台不一致或为空 | status==ERROR；msgKey∈{rcdc-clouddesktop_desk_role_error, rcdc-clouddesktop_info_is_empty} |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | low |
| 说明 | 还原会覆盖桌面系统盘数据，重复执行会再次还原；执行前必须确认桌面为关闭状态 |
