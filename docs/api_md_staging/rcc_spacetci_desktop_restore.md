---
version: '2.0'
api:
  url: /rcc/spacetci/desktop/restore
  method: POST
  name: SPACE-TCI桌面批量还原：按镜像与分区选择还原TCI桌面磁盘，向绑定终端下发 shine 还原指令。
  controller: RccSpaceTCIDesktopController
  method_ref: restoreTCIDesktop
  permission: '@EnableAuthority'
  exec_mode: batch
  async: false
  description: SPACE-TCI桌面批量还原：按镜像与分区选择还原TCI桌面磁盘，向绑定终端下发 shine 还原指令。
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
    clusterId: $.content.itemArr[0].clusterId
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
- name: query_desktop
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
  dto: RestoreTCIDesktopRequest
  body:
    deskList:
      type: List<TCIDeskInfo>
      required: true
      constraint: '@NotEmpty 非空'
      description: 待还原TCI桌面信息列表
    deskList[].deskId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: TCI桌面ID
    deskList[].computerName:
      type: String
      required: true
      constraint: '@NotNull 非空'
      description: TCI桌面计算机名
    imageId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 目标镜像模板ID
    partitionArr:
      type: Integer[]
      required: true
      constraint: '@NotEmpty 非空，值为0(系统分区)/1(数据分区)'
      description: 待还原的分区数组
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 教室ID
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
- api: POST /rcc/classroom/terminal/list
  produces: $.content.itemArr[0].classroomId
  purpose: 教室ID在创建教室(POST /rcc/classroom/create)后经教室终端列表查询获得（ViewClassroomInfoEntity.classroomId）
- api: POST /rcc/classroom/desktop/tci/list
  produces: $.content.itemArr[*].desktopId
  purpose: 推断：TCI桌面列表出参desktopId映射到deskList[].deskId（RestoreTCIDesktopRequest.TCIDeskInfo.deskId），字段名为推断
downstream:
- api: 内部调用:RccTerminalOperatorAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: deskList/imageId/partitionArr/classroomI
  rule: 全部非空
  failure: 参数校验失败（@NotEmpty/@NotNull）
- level: PARAM
  field: partitionArr
  rule: 分区值必须为0(系统)或1(数据)且对应磁盘存在
  failure: diskIdMap 中无对应分区时返回空导致磁盘ID为空
- level: BIZ
  field: desktop
  rule: 桌面必须绑定终端（教师机配置或座位绑定）
  failure: RCC_RESTORE_TCI_DESKTOP_FAIL_NOT_FIND_TERMINAL（座位未绑定终端）
- level: BIZ
  field: imageId
  rule: 镜像必须存在
  failure: cbbImageTemplateMgmtAPI.findById 抛异常
assertions:
  success:
  - scenario: 镜像存在、桌面绑定终端且终端返回成功
    expect: 批量任务提交成功，终端返回0，逐台还原成功；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  failure:
  - scenario: 桌面未绑定终端
    trigger: 教师机未配置或座位无终端
    expect: 任务项 batchTaskItemStatus==FAILURE；msgKey==rcc_restore_tci_desktop_fail_not_find_terminal
  - scenario: 终端执行还原失败
    trigger: shine 返回非0码或抛 BusinessException
    expect: 任务项 batchTaskItemStatus==FAILURE；msgKey==rcc_restore_tci_desktop_task_default_fail_log
cleanup: []
prereq_state:
  resource: desktop
  required_state: RUNNING
  achieve_via:
  - api: POST /rcc/classroom/cmrcef/lesson/start
    note: 学生桌面无独立开机接口，只能通过上课批量开机

idempotency:
  level: data_level
  note: 还原会覆盖TCI本地磁盘，重复执行会再次还原；任务级不幂等
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
---
# POST /rcc/spacetci/desktop/restore

> SPACE-TCI桌面批量还原：按镜像与分区选择还原TCI桌面磁盘，向绑定终端下发 shine 还原指令。 ｜ @EnableAuthority ｜ batch

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/image/list"]
        A2["POST /rcc/classroom/terminal/list"]
        A3["POST /rcc/classroom/desktop/tci/list"]
    end
    B["POST /rcc/spacetci/desktop/restore<br>SPACE-TCI桌面批量还原：按镜像与分区选择还原TCI桌面磁盘，向绑定终端下<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    A2 -->|数据| B
    A3 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: 断言 request 与 builder 非空"]
        C2["Step2: cbbImageTemplateMgmtAPI.findById(imageId"]
        C3["Step3: classroomAPI.getClassroomName(classroomI"]
        C4["Step4: resolveDiskIdList：getIdvImageDiskList 按分"]
        C5["Step5: resolvePartitionDescribe 生成分区描述文本"]
        C6["Step6: 构建 RestoreTCIDesktopBatchTaskHandler（注入 "]
        C1 --> C2
        C7["Step7: enableParallel 提交批量任务返回结果"]
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
| URL | /rcc/spacetci/desktop/restore |
| Controller | RccSpaceTCIDesktopController |
| 方法名 | restoreTCIDesktop |
| 权限注解 | @EnableAuthority |
| 执行方式 | batch |
| 业务含义 | SPACE-TCI桌面批量还原：按镜像与分区选择还原TCI桌面磁盘，向绑定终端下发 shine 还原指令。 |

## 入参详情

### RestoreTCIDesktopRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| deskList | List<TCIDeskInfo> | 是 | @NotEmpty 非空 | 待还原TCI桌面信息列表 |
| deskList[].deskId | UUID | 是 | @NotNull 非空 | TCI桌面ID |
| deskList[].computerName | String | 是 | @NotNull 非空 | TCI桌面计算机名 |
| imageId | UUID | 是 | @NotNull 非空 | 目标镜像模板ID |
| partitionArr | Integer[] | 是 | @NotEmpty 非空，值为0(系统分区)/1(数据分区) | 待还原的分区数组 |
| classroomId | UUID | 是 | @NotNull 非空 | 教室ID |

## 出参详情

| 返回类型 | DefaultWebResponse |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| content | BatchTaskSubmitResult | 批量任务提交结果（还原由后台异步执行） |

## 上游前置业务

### 前置1：POST /rcc/classroom/image/list

推断：镜像ID来源，字段名为推断（由 field_map 契约映射）

### 前置2：POST /rcc/classroom/terminal/list

教室ID在创建教室(POST /rcc/classroom/create)后经教室终端列表查询获得（ViewClassroomInfoEntity.classroomId）（由 field_map 契约映射）

### 前置3：POST /rcc/classroom/desktop/tci/list

推断：TCI桌面列表出参desktopId映射到deskList[].deskId（RestoreTCIDesktopRequest.TCIDeskInfo.deskId），字段名为推断（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：RestoreTCIDesktopBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | 取桌面名（deskIdNameMap） |
| 2 | getBindTerminalId：enableTeacher则取 classroomTeacherAPI.getTeacherByClassroomId 的 teacherTerminalId，否则 seatAPI.getSeatInfo 的 terminalId |
| 3 | 终端ID为空：记 RCC_RESTORE_TCI_DESKTOP_FAIL_NOT_FIND_TERMINAL 并返回 FAILURE |
| 4 | 构造 RccRestoreTCIDesktopDTO{imageId, diskIdList} |
| 5 | rccTerminalOperatorAPI.notifyTerminalRestoreTCIDesktop(terminalId, dto) 向终端下发 shine 还原指令 |
| 6 | 返回码0：记 RCC_RESTORE_TCI_DESKTOP_TASK_SUCCESS 成功；否则记默认失败日志并返回 FAILURE |

### 处理流程

1. 断言 request 与 builder 非空
2. cbbImageTemplateMgmtAPI.findById(imageId) 校验镜像存在并取镜像信息
3. classroomAPI.getClassroomName(classroomId) 取教室名
4. resolveDiskIdList：getIdvImageDiskList 按分区号（0系统/1数据）映射出磁盘ID列表
5. resolvePartitionDescribe 生成分区描述文本
6. 构建 RestoreTCIDesktopBatchTaskHandler（注入 classroomTeacherAPI/seatAPI/classroomDesktopRelationAPI/rccTerminalOperatorAPI/auditLogAPI）
7. enableParallel 提交批量任务返回结果

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | deskList/imageId/partitionArr/classroomId | 全部非空 | 参数校验失败（@NotEmpty/@NotNull） |
| PARAM | partitionArr | 分区值必须为0(系统)或1(数据)且对应磁盘存在 | diskIdMap 中无对应分区时返回空导致磁盘ID为空 |
| BIZ | desktop | 桌面必须绑定终端（教师机配置或座位绑定） | RCC_RESTORE_TCI_DESKTOP_FAIL_NOT_FIND_TERMINAL（座位未绑定终端） |
| BIZ | imageId | 镜像必须存在 | cbbImageTemplateMgmtAPI.findById 抛异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| deskList | user_input/from_query | 按业务构造 |
| deskList[].deskId | user_input/from_query | 按业务构造 |
| deskList[].computerName | user_input/from_query | 按业务构造 |
| imageId | user_input/from_query | 按业务构造 |
| partitionArr | user_input/from_query | 按业务构造 |
| classroomId | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 镜像存在、桌面绑定终端且终端返回成功 | 批量任务提交成功，终端返回0，逐台还原成功 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 桌面未绑定终端 | 教师机未配置或座位无终端 | 单项失败 rcc_restore_tci_desktop_fail_not_find_terminal |
| 终端执行还原失败 | shine 返回非0码或抛 BusinessException | 单项失败 rcc_restore_tci_desktop_task_default_fail_log / fail_log |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | low |
| 说明 | 还原会覆盖TCI本地磁盘，重复执行会再次还原；任务级不幂等 |
