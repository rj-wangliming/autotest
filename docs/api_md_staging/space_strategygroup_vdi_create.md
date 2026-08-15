---
version: '2.0'
api:
  url: /space/strategygroup/vdi/create
  method: POST
  name: 创建VDI策略组
  controller: SpaceDeskStrategyGroupVDIController.java
  method_ref: create
  permission: '@EnableAuthority'
  exec_mode: async_taskflow
  async: true
  return_type: WebResponse<SpaceDeskStrategyGroupVDI>
  description: 创建VDI课程云桌面策略组，含CPU/内存/vGPU/学生账号等配置，平台层+本地层同时创建
setup:
- name: query_usb_types
  api: /space/deskStrategy/getSupportUsbTyp
  method: POST
  permission: user_session
  request:
    body: {}
  extract:
  - var: usbTypeIdArr
    from: response
    jsonpath: $.content[*].id
  assert:
  - path: $.status
    op: eq
    value: SUCCESS
- name: query_vgpu_options
  api: /space/deskStrategy/vgpu/list
  method: POST
  permission: user_session
  request:
    body: {}
  extract:
  - var: vgpuType
    from: response
    jsonpath: $.content[0].vgpuType
  - var: vgpuExtraInfo
    from: response
    jsonpath: $.content[0].vgpuExtraInfo
  purpose: 取第一条（无名称过滤）
- name: query_agreement_templates
  api: /space/deskStrategy/agreement/template/list
  method: POST
  permission: user_session
  request:
    body:
      protocolType:
        value: EST
  extract:
  - var: agreementTemplateId
    from: response
    jsonpath: $.content[0].templateId
  purpose: 取第一条（无名称过滤）
request:
  body:
    name:
      type: String
      required: true
      example: d2
      value: ${param.strategy_name}
    strategyType:
      type: String
      required: true
      example: VDI
      value: VDI
    note:
      type: String
      required: false
      example: ''
    desktopType:
      type: String
      required: false
      example: RECOVERABLE
    cpu:
      type: Integer
      required: true
      example: 2
      value: ${param.cpu}
    memory:
      type: Integer
      required: true
      example: 2048
      value: ${param.memory}
    systemDisk:
      type: Integer
      required: false
      example: 40
    enableNested:
      type: Boolean
      required: false
      example: false
    enableHa:
      type: Boolean
      required: false
      example: false
    enableInternet:
      type: Boolean
      required: true
      example: true
      value: 'true'
    enablePersonalConfig:
      type: Boolean
      required: true
      example: false
      value: 'false'
    openUsbReadOnly:
      type: Boolean
      required: false
      example: false
    keyboardEmulationType:
      type: String
      required: false
      example: PS2
    enablePeripheral:
      type: Boolean
      required: false
      example: true
    usbTypeIdArr:
      type: list
      required: false
      description: 数组（示例 1 项）
    enableClipboard:
      type: Boolean
      required: false
      example: true
    pcToAppTransfer:
      type: Boolean
      required: false
      example: true
    localToRemoteCopyChar:
      type: dict
      required: false
      description: 嵌套对象（见正文说明）
    localToRemoteEnableCopyFile:
      type: list
      required: false
      description: 数组（示例 1 项）
    appToPcTransfer:
      type: Boolean
      required: false
      example: true
    remoteToLocalCopyChar:
      type: dict
      required: false
      description: 嵌套对象（见正文说明）
    remoteToLocalEnableCopyFile:
      type: list
      required: false
      description: 数组（示例 1 项）
    diskMappingType:
      type: String
      required: false
      example: CLOSED
    netDiskMappingType:
      type: String
      required: false
      example: CLOSED
    cdRomMappingType:
      type: String
      required: false
      example: CLOSED
    usbStorageDeviceMappingMode:
      type: String
      required: false
      example: CLOSED
    forbidCatchScreen:
      type: Boolean
      required: false
      example: false
    needHideFloatBar:
      type: Boolean
      required: false
      example: false
    enableShowLocalDisk:
      type: Boolean
      required: false
      example: true
    powerPlan:
      type: String
      required: false
      example: SLEEP
    powerPlanTimeSwitch:
      type: Integer
      required: false
      example: 0
    estIdleOverTime:
      type: Integer
      required: false
      example: 0
    enableAdaptiveResolution:
      type: Boolean
      required: false
      example: true
    enableDoubleScreen:
      type: Boolean
      required: false
      example: false
    enableGpu:
      type: Boolean
      required: false
      example: false
    enableSoftwareDecode:
      type: Boolean
      required: false
      example: true
    agreementAgencyLimitMode:
      type: String
      required: false
      example: NO_LIMIT
    enableWebClient:
      type: Boolean
      required: false
      example: true
    estProtocolType:
      type: String
      required: false
      example: EST
    vgpuType:
      type: String
      required: false
      example: QXL
    vgpuExtraInfo:
      type: Object
      required: false
      constraint: '@Nullable'
      description: vGPU 配置信息（model/parentGpuModel/vgpuModelType/memory/graphicsMemorySize）
    deskCreateMode:
      type: String
      required: false
      constraint: '@Nullable'
      description: 云桌面创建方式（LINK_CLONE/FULL_CLONE/OTHER）
    haPriority:
      type: Integer
      required: false
      constraint: '@Nullable @Range(0,10)'
      description: 配置HA优先级（VDI生效）
    shutDownDeleteSystemDisk:
      type: Boolean
      required: false
      constraint: '@Nullable'
      description: VDI还原类型桌面关机后是否删除系统盘
    state:
      type: SpaceStrategyGroupState
      required: false
      constraint: '@Nullable'
      description: 策略状态
    deskPersonalConfigStrategyType:
      type: CbbDeskPersonalConfigStrategyType
      required: false
      constraint: '@Nullable'
      description: 浮动个性配置类型
    personalConfigDiskSize:
      type: Integer
      required: false
      constraint: '@Nullable @Range(1,2048)'
      description: 浮动个性盘大小
    studentAccountPreName:
      type: String
      required: false
      constraint: '@Nullable @Size(1,15)'
      description: 学生端账号前缀（归属space）
    studentAccountPassword:
      type: String
      required: false
      constraint: '@Nullable'
      description: 学生端密码（归属space）
    enableStudentAccount:
      type: Boolean
      required: false
      example: false
    agreementInfo:
      type: dict
      required: false
      description: 嵌套对象（见正文说明）
    computerName:
      type: String
      required: false
      example: listen
    personalDisk:
      type: Integer
      required: false
      example: 0
    enableOpenDesktopRedirect:
      type: Boolean
      required: false
      example: false
    desktopOccupyDriveArr:
      type: list
      required: false
      description: 数组（示例 0 项）
    enableHyperVisorImprove:
      type: Boolean
      required: false
      example: true
    watermarkInfo:
      type: dict
      required: false
      description: 嵌套对象（见正文说明）
    pattern:
      type: String
      required: true
      example: RECOVERABLE
      value: RECOVERABLE
    systemSize:
      type: Integer
      required: true
      example: 40
      value: ${param.systemSize}
    clipBoardSupportTypeArr:
      type: list
      required: false
      description: 数组（示例 2 项）
    powerPlanTime:
      type: Integer
      required: false
      example: 0
    business:
      type: String
      required: true
      example: RCC
      value: RCC
    platformStrategyGroup:
      type: PlatformStrategyGroup
      required: true
      description: 平台策略组数据，含 strategyGroupFacadeStr（JSON字符串，内部 vdi 节点见「VDI 策略嵌套参数」节）
      nested:
        strategyGroupFacadeStr:
          type: String(JSON)
          required: true
          description: 嵌套VDI策略JSON字符串（vdi 节点 19 字段）
      generated_by: config_generator
response:
  wrapper:
    status:
      type: String
      assert_op: eq
      values:
      - SUCCESS
      - ERROR
    message:
      type: String
    msgKey:
      type: String
      assert_op: eq
    msgArgArr:
      type: String[]
    content:
      type: Object
  body:
    id:
      type: UUID
      assert_op: not_empty
      description: 创建的策略组ID
    name:
      type: String
      assert_op: eq
      assert_value: ${name}
      description: 策略组名称
    state:
      type: String
      description: 状态
    creatorId:
      type: UUID
      description: 创建者ID
    creatorName:
      type: String
      description: 创建者名称
    platformStrategyGroup:
      type: PlatformStrategyGroup
      description: 平台策略组数据（含id）
      nested:
        id:
          type: UUID
          assert_op: not_empty
          description: 平台策略组ID（用于清理/关联）
polling:
  api: /space/strategygroup/vdi/detail
  method: POST
  params:
    id: ${content.id}
  interval_ms: 2000
  timeout_ms: 120000
  terminal_states:
    success:
    - SUCCESS
    failure:
    - ERROR
  success_when:
  - path: $.status
    op: eq
    value: SUCCESS
  - path: $.content.state
    op: eq
    value: AVAILABLE
upstream:
- api: 管理员登录
  produces:
  - authToken
  - sessionId
  purpose: '@EnableAuthority 前置'
- api: /space/deskStrategy/getSupportUsbTyp
  produces:
  - usbTypeIdArr
  purpose: 获取支持的USB外设类型列表
- api: /space/deskStrategy/vgpu/list
  produces:
  - vgpuType
  - vgpuExtraInfo
  purpose: 获取vGPU相关选项
- api: /space/deskStrategy/agreement/template/list
  produces:
  - agreementTemplateId
  purpose: 获取协议配置模板列表
downstream:
- kind: http
  api: /space/strategygroup/vdi/detail
  verify: true
  purpose: 查看策略详情（也用作 polling）
- kind: http
  api: /space/strategygroup/vdi/list
  verify: true
  purpose: 策略列表查询
- kind: http
  api: /space/strategygroup/vdi/edit
  verify: false
  purpose: 编辑策略
- kind: http
  api: /space/strategygroup/vdi/delete
  verify: false
  purpose: 删除策略（cleanup 用）
- kind: http
  api: /rcc/classroom/image/teacher/create
  verify: false
  purpose: 分配镜像引用策略（原文档路径 /rcc/classroomImage/assign 已修正）
- kind: http
  api: /rcc/classroom/image/student/create
  verify: false
  purpose: 学生镜像分配
- kind: spi
  impl: RccCreateDesktopHelper
  method: findById(strategyId)
  verify: true
  purpose: 创建桌面读取策略
- kind: spi
  impl: RccDesktopVDIOperateServiceImpl
  method: updateDesktopImageAndAdvanceConfig
  verify: true
  purpose: 桌面启停读取策略
flow:
- step: 1
  name: Phase1 Controller层
  detail: SpaceDeskStrategyGroupVDIController.create → 解密学生密码 → super.defaultCreate
- step: 2
  name: Phase2 校验层
  detail: validateNameDuplication（本地+平台双重查重）→ validStrategy（CPU/内存范围）→ vGPU校验
- step: 3
  name: Phase3 Taskflow创建（4步+undo）
  detail: CreatePlatformStrategyGroupProcessor（推平台）→ CreatePlatformStrategyGroupRelatedProcessor（平台关联）→ CreateLocalStrategyGroupProcessor（本地入库，VDI/USB/嵌套JSON随strategyGroupFacadeStr）→ AddStrategyGroupDataPermissionProcessor（数据权限）
constraints:
- level: dto
  field: name
  rule: not_blank
  failure: 名称不能为空
  generate_case: true
- level: dto
  field: name
  rule: unique_local_platform
  detail: 本地DB + 平台双重查重
  failure: 本地62100317 / 平台62100220
  generate_case: true
- level: dto
  field: cpu
  rule: range
  range:
  - 1
  - 64
  failure: '62100331'
  generate_case: true
- level: dto
  field: memory
  rule: range
  range:
  - 1024
  - 262144
  failure: '62100332'
  generate_case: true
- level: dto
  field: systemSize
  rule: range
  range:
  - 20
  - 1024
  failure: checkVDIParamAvailable
  generate_case: true
- level: dto
  field: strategyType
  rule: enum
  values:
  - VDI
  failure: 必须为VDI
- level: service
  field: preName
  rule: pattern
  pattern: ^[a-zA-Z-z0-9]*[a-zA-Z-z]+[a-zA-Z-z0-9\-]*$
  detail: enableStudentAccount=true 时校验，≤15位
  failure: 62100304/62100305
  generate_case: true
- level: service
  field: password
  rule: length
  detail: 解密后≤16位，正则 ^[A-Za-z0-9...]+$
  failure: '62100325'
  generate_case: true
value_strategy:
  name:
    strategy: random_uuid
    prefix: VDI策略-
    note: 保证名称唯一（本地+平台双重查重）
  cpu:
    strategy: fixed_value
    value: 2
  memory:
    strategy: fixed_value
    value: 4096
  systemSize:
    strategy: fixed_value
    value: 40
  pattern:
    strategy: enum_value
    value: RECOVERABLE
  strategyType:
    strategy: enum_value
    value: VDI
  vgpuType:
    strategy: from_setup
    var: vgpuType
    note: setup.query_vgpu_options 提取；QXL 表示无 vGPU
  usbTypeIdArr:
    strategy: from_setup
    var: usbTypeIdArr
    note: setup.query_usb_types 提取
  platformStrategyGroup:
    strategy: constructed
    note: strategyGroupFacadeStr 为嵌套JSON，按 VDI 策略模板构造
assertions:
  success:
  - scenario: 创建基础VDI策略
    setup_hint: name唯一，CPU/内存合法，无vGPU
    expect:
    - path: $.status
      op: eq
      value: SUCCESS
    - path: $.content.id
      op: not_empty
  - scenario: 创建带vGPU策略
    setup_hint: vgpuType非QXL，vgpuExtraInfo有效
    expect:
    - path: $.status
      op: eq
      value: SUCCESS
    - path: $.content.platformStrategyGroup.id
      op: not_empty
  - scenario: 创建带学生账号策略
    setup_hint: enableStudentAccount=true，账号密码格式正确
    expect:
    - path: $.status
      op: eq
      value: SUCCESS
  failure:
  - scenario: 策略名重复（本地）
    trigger: name 在本地DB已存在
    expect:
    - path: $.status
      op: eq
      value: ERROR
    - path: $.msgKey
      op: contains
      value: '62100317'
  - scenario: 策略名重复（平台）
    trigger: name 在平台已存在
    expect:
    - path: $.status
      op: eq
      value: ERROR
    - path: $.msgKey
      op: contains
      value: '62100220'
  - scenario: CPU超范围
    trigger: cpu<1 或 cpu>64
    expect:
    - path: $.status
      op: eq
      value: ERROR
    - path: $.msgKey
      op: contains
      value: '62100331'
  - scenario: 内存超范围
    trigger: memory<1024 或 memory>262144
    expect:
    - path: $.status
      op: eq
      value: ERROR
    - path: $.msgKey
      op: contains
      value: '62100332'
cleanup:
- name: delete_vdi_strategy
  api: /space/strategygroup/vdi/delete
  method: POST
  permission: '@EnableAuthority'
  request:
    body:
      idArr:
      - ${content.id}
  condition: ${content.id} is not null
  pre_check:
    api: /space/strategygroup/vdi/detail
    assert:
    - path: $.content.state
      op: eq
      value: AVAILABLE
  on_failure: log_and_continue
  note: 若策略被镜像引用（validateBindByImage 抛62100324），需先解除镜像关联或删除镜像再重试
idempotency:
  level: non_idempotent
  lock: none
  duplicate_behavior: throws
  detail: 重复创建同名/同ID报错；Taskflow 每步带 undo 但 DeleteTaskflow 不支持 undo
  retry_policy: 失败后需人工检查残留（平台侧已建但本地未建等），清理后再重试
params:
  required:
  - name: strategy_name
    desc: VDI 策略名称（唯一）
    used_by: request.body.name
  - name: cpu
    desc: CPU 核数（@Range 1-64，可=参数生成器按规则表生成）
    used_by: request.body.cpu
  - name: memory
    desc: 内存 MB（@Range 1024-262144）
    used_by: request.body.memory
  - name: systemSize
    desc: 系统盘 GB（@Range 0-2048，≥镜像要求）
    used_by: request.body.systemSize
---
# POST /space/strategygroup/vdi/create

> 创建VDI课程云桌面策略组，包含CPU/内存/vGPU/学生账号等配置，同时在平台层和本地层创建记录 ｜ @EnableAuthority ｜ 异步Taskflow（4步处理器，每步带undo）

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["管理员登录<br>→ 产出 authToken/sessionId"]
        A2["POST /space/deskStrategy/getSupportUsbTyp<br>获取支持的USB外设类型列表<br>→ 产出 usbTypeIdArr (UUID数组)"]
        A3["POST /space/deskStrategy/vgpu/list<br>获取vGPU相关选项<br>→ 产出 vgpuType + vgpuExtraInfo 选项"]
        A4["POST /space/deskStrategy/agreement/template/list<br>获取协议配置模板列表<br>→ 产出 agreementInfo.*.templateId"]
    end
    B["POST /space/strategygroup/vdi/create<br>创建课程云桌面策略<br>入参: name(必填)/cpu(必填)/memory(必填)<br>入参: systemSize(必填)/pattern(必填)<br>入参: strategyType(必填,VDI/VOI)<br>入参: platformStrategyGroup(必填,含strategyGroupFacadeStr)<br>入参: usbTypeIdArr(来自getSupportUsbTyp)<br>入参: vgpuType/vgpuExtraInfo(来自vgpu/list)<br>入参: agreementInfo(含templateId来自模板列表)<br>入参: enableInternet/enablePersonalConfig<br>入参: 全部53个顶层参数<br>权限: @EnableAuthority<br>返回: DefaultWebResponse"]
    A1 -->|authToken| B
    A2 -->|usbTypeIdArr| B
    A3 -->|vgpuType/vgpuExtraInfo| B
    A4 -->|agreementInfo.templateId| B
    subgraph 内部处理流程
        C1["Phase1: Controller层<br>SpaceDeskStrategyGroupVDIController.create<br>接收参数,调用service"]
        C2["Phase2: 校验层<br>validateNameDuplication 名称查重（本地+平台双重）<br>参数合法性校验"]
        C3["Phase3: Taskflow创建(4步+undo)<br>Step1: CreatePlatformStrategyGroupProcessor 创建平台策略组<br>Step2: CreatePlatformStrategyGroupRelatedProcessor 创建平台关联<br>Step3: CreateLocalStrategyGroupProcessor 本地入库(含VDI/USB/嵌套JSON,随strategyGroupFacadeStr)<br>Step4: AddStrategyGroupDataPermissionProcessor 添加数据权限"]
        C1 --> C2 --> C3
    end
    B --> C1
    subgraph 下游消费方
        D1["POST /space/strategygroup/vdi/detail<br>查看策略详情"]
        D2["POST /space/strategygroup/vdi/list<br>策略列表查询"]
        D3["POST /space/strategygroup/vdi/edit<br>编辑策略"]
        D4["POST /space/strategygroup/vdi/delete<br>删除策略"]
        D5["POST /rcc/classroom/image/teacher/create、/student/create<br>分配镜像引用策略"]
        D6["SPI: RccCreateDesktopHelper<br>创建桌面读取策略"]
        D7["SPI: RccDesktopVDIOperateServiceImpl<br>桌面启停读取策略"]
    end
    B -->|策略ID| D1
    B -->|策略ID| D2
    B -->|策略ID| D3
    B -->|策略ID| D4
    B -->|策略ID| D5
    B -->|SPI| D6
    B -->|SPI| D7
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /space/strategygroup/vdi/create |
| Controller | SpaceDeskStrategyGroupVDIController.java |
| 方法名 | create |
| 权限注解 | @EnableAuthority |
| 返回值 | WebResponse（创建的SpaceDeskStrategyGroupVDI） |
| 执行方式 | 异步Taskflow（4步处理器，每步带undo） |
| 业务含义 | 创建VDI课程云桌面策略组，包含CPU/内存/vGPU/学生账号等配置，同时在平台层和本地层创建记录 |
| 数据表 | t_space_vdi_lesson_strategy（本地） + 平台策略组表 |

## 入参详情

> **本表以实际请求 JSON 为准**（真实线上请求体，53 个顶层字段 + platformStrategyGroup）。字段同时出现在顶层与 `strategyGroupFacadeStr.vdi` 节点时，顶层为请求主字段，vdi 节点见下方「VDI 策略嵌套参数」节（19 字段，为镜像子集）。

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| name | String | 是 | | 示例: d2 |
| strategyType | String | 是 | | 示例: VDI |
| note | String | 否 | | 示例:  |
| desktopType | String | 否 | | 示例: RECOVERABLE |
| cpu | Integer | 是 | | 示例: 2 |
| memory | Integer | 是 | | 示例: 2048 |
| systemDisk | Integer | 否 | | 示例: 40 |
| enableNested | Boolean | 否 | | 示例: False |
| enableHa | Boolean | 否 | | 示例: False |
| enableInternet | Boolean | 是 | | 示例: True |
| enablePersonalConfig | Boolean | 是 | | 示例: False |
| openUsbReadOnly | Boolean | 否 | | 示例: False |
| keyboardEmulationType | String | 否 | | 示例: PS2 |
| enablePeripheral | Boolean | 否 | | 示例: True |
| usbTypeIdArr | list | 否 | | 数组（示例 1 项，如外设UUID列表） |
| enableClipboard | Boolean | 否 | | 示例: True |
| pcToAppTransfer | Boolean | 否 | | 示例: True |
| localToRemoteCopyChar | dict | 否 | | 嵌套对象（见对应说明） |
| localToRemoteEnableCopyFile | list | 否 | | 数组（示例 1 项，如外设UUID列表） |
| appToPcTransfer | Boolean | 否 | | 示例: True |
| remoteToLocalCopyChar | dict | 否 | | 嵌套对象（见对应说明） |
| remoteToLocalEnableCopyFile | list | 否 | | 数组（示例 1 项，如外设UUID列表） |
| diskMappingType | String | 否 | | 示例: CLOSED |
| netDiskMappingType | String | 否 | | 示例: CLOSED |
| cdRomMappingType | String | 否 | | 示例: CLOSED |
| usbStorageDeviceMappingMode | String | 否 | | 示例: CLOSED |
| forbidCatchScreen | Boolean | 否 | | 示例: False |
| needHideFloatBar | Boolean | 否 | | 示例: False |
| enableShowLocalDisk | Boolean | 否 | | 示例: True |
| powerPlan | String | 否 | | 示例: SLEEP |
| powerPlanTimeSwitch | Integer | 否 | | 示例: 0 |
| estIdleOverTime | Integer | 否 | | 示例: 0 |
| enableAdaptiveResolution | Boolean | 否 | | 示例: True |
| enableDoubleScreen | Boolean | 否 | | 示例: False |
| enableGpu | Boolean | 否 | | 示例: False |
| enableSoftwareDecode | Boolean | 否 | | 示例: True |
| agreementAgencyLimitMode | String | 否 | | 示例: NO_LIMIT |
| enableWebClient | Boolean | 否 | | 示例: True |
| estProtocolType | String | 否 | | 示例: EST |
| vgpuType | String | 否 | | 示例: QXL |
| enableStudentAccount | Boolean | 否 | | 示例: False |
| agreementInfo | dict | 否 | | 嵌套对象（见对应说明） |
| computerName | String | 否 | | 示例: listen |
| personalDisk | Integer | 否 | | 示例: 0 |
| enableOpenDesktopRedirect | Boolean | 否 | | 示例: False |
| desktopOccupyDriveArr | list | 否 | | 数组（示例 0 项，如外设UUID列表） |
| enableHyperVisorImprove | Boolean | 否 | | 示例: True |
| watermarkInfo | dict | 否 | | 嵌套对象（见对应说明） |
| pattern | String | 是 | | 示例: RECOVERABLE |
| systemSize | Integer | 是 | | 示例: 40 |
| clipBoardSupportTypeArr | list | 否 | | 数组（示例 2 项，如外设UUID列表） |
| powerPlanTime | Integer | 否 | | 示例: 0 |
| business | String | 是 | | 示例: RCC |
| platformStrategyGroup | PlatformStrategyGroup | 是 | @NotNull | 平台策略组数据，含 strategyGroupFacadeStr（JSON字符串） |
## VDI 策略嵌套参数（platformStrategyGroup.strategyGroupFacadeStr → vdi）

> **本小节以实际请求 JSON 为准**：`strategyGroupFacadeStr` 反序列化后的 `vdi` 节点共 **19 个字段**（真实线上请求）。
>
> **反序列化目标**：`strategyGroupFacadeStr` → `StrategyGroupFacadeDTO`（外部依赖）→ `vdi` 字段类型为 **`VDIStrategyDTO`**（证据：SpaceDeskStrategyGroupVDIAPIImpl.java:103-105 `JSON.parseObject(..., StrategyGroupFacadeDTO.class); return getVdi()`；TestDataFactory.java:84 `setVdi(new VDIStrategyDTO())`）。⚠️ 注意不是 `VDIDeskStrategyDTO`（rcdc-space-module 另一套课程策略 DTO，8 个真实 vdi 字段在其中不存在）。
>
> **键名规则**：真实请求 JSON 全部字段为 camelCase（如 `usbTypeIdArr`、`enableClipboard`），自动化构造请求体必须用 camelCase 键名，服务端 Jackson/fastjson 才能正确映射。

### 外设/USB映射参数

| 参数名 | 类型 | 实际值 | 说明 |
|---|---|---|---|
| enablePeripheral | bool | true | 真实请求示例值 |
| usbTypeIdArr | list | 数组(1项) | 真实请求示例值 |
| openUsbReadOnly | bool | false | 真实请求示例值 |
| usbStorageDeviceMappingMode | str | 'CLOSED' | 真实请求示例值 |
| diskMappingType | str | 'CLOSED' | 真实请求示例值 |

### 剪贴板映射参数

| 参数名 | 类型 | 实际值 | 说明 |
|---|---|---|---|
| enableClipboard | bool | true | 真实请求示例值 |
| clipBoardSupportTypeArr | list | 数组(2项) | 真实请求示例值 |

### 磁盘/光驱映射参数

| 参数名 | 类型 | 实际值 | 说明 |
|---|---|---|---|
| netDiskMappingType | str | 'CLOSED' | 真实请求示例值 |
| cdRomMappingType | str | 'CLOSED' | 真实请求示例值 |

### 截屏/电源/超时参数

| 参数名 | 类型 | 实际值 | 说明 |
|---|---|---|---|
| forbidCatchScreen | bool | false | 真实请求示例值 |
| powerPlan | str | 'SLEEP' | 真实请求示例值 |
| powerPlanTime | int | 0 | 真实请求示例值 |
| estIdleOverTime | int | 0 | 真实请求示例值 |

### 水印配置参数

| 参数名 | 类型 | 实际值 | 说明 |
|---|---|---|---|
| enableWatermark | bool | false | 真实请求示例值 |

### 网关接入限制参数

| 参数名 | 类型 | 实际值 | 说明 |
|---|---|---|---|
| agreementAgencyLimitMode | str | 'NO_LIMIT' | 真实请求示例值 |
| agreementAgencyInfo | dict | 嵌套对象 | 真实请求示例值 |

### 协议/Web客户端参数

| 参数名 | 类型 | 实际值 | 说明 |
|---|---|---|---|
| enableWebClient | bool | true | 真实请求示例值 |
| estProtocolType | str | 'EST' | 真实请求示例值 |
| agreementInfo | dict | 嵌套对象 | 真实请求示例值 |
## 出参详情

### 外层响应（CommonWebResponse 包装）

| 字段 | 类型 | 说明 |
|---|---|---|
| status | String | SUCCESS / ERROR |
| msgKey | String | 错误消息key（成功时为空） |
| msgArgArr | String[] | 消息参数数组 |
| message | String | 提示消息 |
| content | SpaceDeskStrategyGroupVDI | 创建的策略组对象（含入参回显+服务端填充字段） |

### content 业务字段（SpaceDeskStrategyGroupVDI）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 自动生成或使用传入ID（断言非空） |
| state | SpaceStrategyGroupState | 服务端设为AVAILABLE |
| stateAvailable | Boolean | state==AVAILABLE时为true（计算属性） |
| creatorId | UUID | 从SessionContext获取 |
| creatorName | String | 从SessionContext获取 |
| createTime | Long | 创建时间戳 |
| updateTime | Long | 更新时间戳 |
| platformStrategyGroup.id | UUID | 设为策略组ID（清理/关联用） |
| platformStrategyGroup.strategyType | DeskVirtualizationType | 设为VDI |
| platformStrategyGroup.creatorName | String | 设为创建者名 |
| platformStrategyGroup.name | String | 设为策略组名 |

## 上游前置业务

### 前置1：管理员登录

产出：SessionContext（creatorId、creatorName） 说明：@EnableAuthority需要管理员权限，SessionContext在Controller层注入

### 前置2：POST /space/deskStrategy/getSupportUsbTyp — 获取USB外设类型列表

产出：usbTypeIdArr（UUID数组，标识允许的USB外设类型） 说明：usbTypeIdArr参数的可选值来自此接口，包含摄像头/存储/打印机/输入设备/音频/手机/网卡/蓝牙等类型

### 前置3：POST /space/deskStrategy/vgpu/list — 获取vGPU相关选项

产出：vgpuType枚举值 + vgpuExtraInfo配置选项（model/parentGpuModel/vgpuModelType/graphicsMemorySize/memory） 说明：当vgpuType非QXL时，vgpuExtraInfo必填且值需从此接口获取的可用选项中选择

### 前置4：POST /space/deskStrategy/agreement/template/list — 获取协议配置模板列表

产出：agreementInfo.wanEstConfig.templateId + agreementInfo.lanEstConfig.templateId 说明：协议配置agreementInfo中的templateId（如templateId=1局域网、templateId=2广域网）从此接口获取，framerate/bitrate/quality等参数为用户自定义 本接口不需要classroomId/clusterId/storagePoolId/networkId等桌面池相关ID（这些属于/rcc/space/publish桌面池创建接口的前置，不属于策略创建）。上游仅需管理员登录 + 上述3个查询接口获取参数可选值。

### 前置状态要求



## 内部处理流程（Taskflow 4 处理器 + undo）

### Phase 1：Controller层

断言入参非空 解密studentAccountPassword（如非空）：AesUtil.descrypt(encryptedPassword, adminRedLine) 断言解密后密码长度&lt;=16 设置creatorId和creatorName 调用super.defaultCreate()

### Phase 2：校验层

名称查重（本地）：validateNameDuplication查询本地DB 名称查重（平台）：platformStrategyAPI.checkDeskStrategyExist(name, id) CPU范围校验：1-64，超出抛62100331 内存范围校验：1024-262144MB，超出抛62100332 学生账号校验（如enableStudentAccount=true）：studentAccountPreName非空且&lt;=15位且正则匹配 studentAccountPassword&lt;=16位且正则匹配 VGPU校验（如vgpuType非QXL）：resolveVgpuInfo解析VGPU信息 validateVgpu校验GPU配置

### Phase 3：Taskflow创建（4步，每步带undo）

创建平台策略组：platformStrategyGroupAPI.create()转换为StrategyGroupFacadeDTO 校验VDI策略 平台查重 调用strategyGroupFacadeAPI.create() undo：删除平台策略组 创建子系统资源关系：platformSubSysResRelationAPI.addOrUpdate()SPACE拥有STRATEGY_GROUP资源 undo：幂等删除关系（存在则删） 保存本地策略组：repository.create()DTO转Entity，设置createTime/updateTime 保存到t_space_vdi_lesson_strategy表 undo：删除本地实体 创建数据权限：adminDataPermissionAPI.create()关联管理员到策略组 undo：删除数据权限

## 下游消费方

### 消费1：POST /space/strategygroup/vdi/detail — 查看策略详情

说明：返回策略完整信息，studentAccountPassword重新AES加密返回

### 消费2：POST /space/strategygroup/vdi/list — 策略列表

说明：分页查询，返回ViewRccDeskStrategyDTO（含策略名、类型、CPU、内存等摘要字段）

### 消费3：POST /space/strategygroup/vdi/edit — 编辑策略

说明：编辑前校验状态为AVAILABLE、无运行中桌面、不能修改pattern/strategyType/systemSize降级

### 消费4：POST /space/strategygroup/vdi/delete — 删除策略

说明：删除前校验无关联镜像（validateBindByImage），有则抛62100324

### 消费5：POST /rcc/classroom/image/teacher/create — 分配镜像引用策略

说明：分配教室镜像时验证策略兼容性（原 /rcc/classroomImage/assign 路径不存在，画板与正文已一致修正）

### 消费6：RccCreateDesktopHelper — 创建桌面读取策略

说明：通过findByStrategy()读取策略配置，按CPU/内存/vGPU创建VDI桌面

### 消费7：RccDesktopVDIOperateServiceImpl — 桌面启停读取策略

说明：桌面启动/关闭/重启操作中读取策略配置

## 分层接口参数约束

> ⚠️ 源码核实：Controller `create()` 无 `@Valid` 注解（仅 `Assert.notNull`），DTO 上的 `@NotNull`/`@Range`/`@Nullable` 实际**不生效**。以下按真实生效的校验分层：

| 层级 | 参数 | 规则 | 说明/失败结果 |
|---|---|---|---|
| controller | spaceStrategyGroup | not_null | `Assert.notNull` #102，失败抛 IllegalArgumentException |
| service | name | 本地+平台双重查重 | `validateNameDuplication`，失败 62100317/62100220 |
| service | cpu | range 1-64 | `checkVDIParamAvailable` 校验，失败 62100331 |
| service | memory | range 1024-262144 | `checkVDIParamAvailable` 校验，失败 62100332 |
| service | systemSize | **创建期无校验** | 20/1024 常量仅用于变更时防降级比对（validStrategyChange）；创建不校验 |
| service | preName | 正则 ≤15位 | enableStudentAccount=true 时校验，失败 62100304/62100305 |
| service | personalConfigDiskSize | **创建期无校验** | DTO @Range(1-2048) 因无 @Valid 不生效 |
| service | haPriority | **创建期无校验** | DTO @Range(0-10) 因无 @Valid 不生效 |

## 参数取值策略

| 参数名 | 取值策略 | 取值方式 | 示例值 |
|---|---|---|---|
| id | random_uuid | UUID.randomUUID()，或前端传入 | 自动生成 |
| name | user_input | 用户指定，需唯一 | "VDI策略01" |
| pattern | enum_value | 从CbbCloudDeskPattern枚举选择 | RECOVERABLE |
| strategyType | fixed_value | 固定为VDI | VDI |
| enablePersonalConfig | user_input | 布尔值 | false |
| systemSize | user_input | 范围0-2048 | 50 |
| cpu | user_input | 范围1-64 | 4 |
| memory | user_input | 范围1024-262144(MB) | 4096 |
| vgpuType | from_query | POST /space/deskStrategy/vgpu/list 获取可用vGPU类型列表 | QXL |
| vgpuExtraInfo | from_query | POST /space/deskStrategy/vgpu/list 获取vGPU配置(model/graphicsMemorySize等)，vgpuType非QXL时必填 | {model,graphicsMemorySize,memory} |
| usbTypeIdArr | from_query | POST /space/deskStrategy/getSupportUsbTyp 获取USB外设类型UUID列表 | ["e3f8d1ee-...","476cf4dd-..."] |
| agreementInfo | from_query + constructed | POST /space/deskStrategy/agreement/template/list 获取templateId；framerate/bitrate等用户配置 | {wanEstConfig:{templateId:2,...}} |
| enableStudentAccount | user_input | 布尔值，true触发条件校验 | false |
| studentAccountPreName | constructed | enableStudentAccount=true时必填，正则匹配 | "student" |
| studentAccountPassword | constructed | AES加密传入，解密后≤16位 | AES加密串 |
| platformStrategyGroup | constructed | 含strategyGroupFacadeStr(JSON嵌套19参数)+business | JSON对象 |
| enableInternet | user_input | 布尔值 | true |

## 成功/失败断言基准

### 成功场景

| 场景 | 请求条件 | 断言点 |
|---|---|---|
| 创建基础VDI策略 | name唯一，CPU/内存合法，无vGPU | status==SUCCESS, content.id非空 |
| 创建带vGPU策略 | vgpuType非QXL，vgpuExtraInfo有效 | status==SUCCESS, VGPU信息已解析 |
| 创建带学生账号策略 | enableStudentAccount=true，账号密码格式正确 | status==SUCCESS |
| 创建带个人配置策略 | enablePersonalConfig=true，personalConfigDiskSize合法 | status==SUCCESS |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 策略名重复（本地） | name在本地DB已存在 | status==ERROR, msgKey含62100317 |
| 策略名重复（平台） | name在平台已存在 | status==ERROR, msgKey含62100220 |
| CPU超范围 | cpu&lt;1或cpu&gt;64 | status==ERROR, msgKey含62100331 |
| 内存超范围 | memory&lt;1024或memory&gt;262144 | status==ERROR, msgKey含62100332 |
| 系统盘超范围 | systemSize&lt;20或systemSize&gt;1024 | ⚠️ 创建期无此校验（checkVDIParamAvailable 只校验 cpu/memory；20/1024 常量仅用于变更时防降级比对；DTO @Range 因无 @Valid 不生效） |
| 个人配置磁盘超范围 | personalConfigDiskSize&lt;1或&gt;2048（enablePersonalConfig=true时） | status==ERROR, @Range(1-2048)校验 |
| HA优先级超范围 | haPriority&lt;0或haPriority&gt;10 | status==ERROR, @Range(0-10)校验 |
| 学生账号前缀为空 | enableStudentAccount=true但preName为空 | status==ERROR, msgKey含62100305 |
| 学生账号前缀超长 | preName&gt;15位 | status==ERROR, msgKey含62100304 |
| 学生账号前缀正则不匹配 | preName不匹配^[a-zA-Z-z0-9]*[a-zA-Z-z]+[a-zA-Z-z0-9\-]*$ | status==ERROR, 正则校验失败 |
| 学生密码超长 | 解密后password&gt;16位 | 抛IllegalStateException |
| 学生密码格式错误 | password不匹配^[A-Za-z0-9`~!@#$%^&amp;*()_-=+{}[]\|:;"'&lt;&gt;,.?/\]+$ | status==ERROR, msgKey含62100325 |
| VGPU校验失败 | vgpuType非QXL但VGPU信息无效 | BusinessException(平台错误码) |
| 平台创建失败 | strategyGroupFacadeAPI.create()抛异常 | status==ERROR |
| 权限不足 | 无@EnableAuthority权限 | 403/权限拦截 |

## 环境清理机制

### 清理接口

| 接口 | URL | 入参 | 前置条件 | 校验逻辑 |
|---|---|---|---|---|
| 删除策略 | POST /space/strategygroup/vdi/delete | idArr=[策略ID] | 策略存在 + 无关联镜像 | validateBindByImage检查镜像关联，有则抛62100324 |

### 清理失败处理

| 失败场景 | 原因 | 处理方式 |
|---|---|---|
| 策略关联了镜像 | 有classroomImage引用此策略 | 先解除镜像关联或删除镜像，再重试 |
| 平台策略组删除失败 | 平台不可用或策略组被平台其他模块引用 | 重试，或检查平台状态 |
| 本地策略组已删除但平台未删 | 网络中断导致部分步骤失败 | Taskflow不支持undo，需手动清理平台残留数据 |

## 前置状态和幂等性标注

### 前置状态要求

| 前置条件 | 要求 | 校验位置 | 失败结果 |
|---|---|---|---|
| 管理员登录 | SessionContext有效 | Controller层 | 401 |
| 创建权限 | @EnableAuthority通过 | 框架拦截 | 403 |
| 名称唯一 | name在本地和平台都不存在 | Validation层 | 62100317/62100220 |
| 无状态检查 | 不需要桌面池处于特定状态 | - | 顶层资源创建，无前置状态 |

### 幂等性分析

| 幂等维度 | 结论 | 代码证据 |
|---|---|---|
| 重复创建同名策略 | 非幂等（报错） | validateNameDuplication本地+平台双重查重 |
| 重复创建同ID策略 | 非幂等（DB主键冲突） | UUID如传入则使用，DB主键唯一约束 |
| Taskflow中途失败 | 非幂等（部分创建） | 每步带undo处理器，但DeleteTaskflow不支持undo |
| 并发创建 | 无分布式锁 | 无锁机制，依赖名称唯一约束兜底 |

### 幂等性标注

| 幂等级别 | 说明 |
|---|---|
| 非幂等 | 重复调用同名/同ID会报错。无幂等token机制。Taskflow失败后需人工检查并清理残留数据 |