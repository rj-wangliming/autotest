---
version: '2.0'
api:
  url: /rcc/classroom/editTeacherInfo
  method: POST
  name: 修改教师机配置：先校验终端组数据权限，再同步调 classroomAPI.validateTeacherConfig 做教师机配置校验（IP、主机名前缀、VLA
  controller: RccClassroomConfigController
  method_ref: editTeacherInfo
  permission: 无
  exec_mode: 异步批处理任务（BatchTask，TeacherConfigBatchTaskHandler）
  async: true
  description: 修改教师机配置：先校验终端组数据权限，再同步调 classroomAPI.validateTeacherConfig 做教师机配置校验（IP、主机名前缀、VLAN、VDI/TCI本地磁盘、策略、存储池等），通过后构造 TeacherConfigBatchTaskHandler 提交异步批任务；任务内 processItem 调 classroomAPI.editTeacherInfo 应用配置，接
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: create_classroom
  api: POST /rcc/classroom/create
  purpose: 创建教室（异步批任务，需轮询批任务完成后再查询教室）
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
  purpose: 按名称过滤查询教室（searchKeyword=${param.classroom_name}），获取 classroomId
  request:
    body:
      searchKeyword: ${param.classroom_name}
- name: get_strategy
  api: POST /rcc/classroom/strategy/list
  extract:
    classroomStrategyId: $.content.itemArr[0].classroomStrategyId
  purpose: 获取教师机教室策略ID（可选）；按策略名精确过滤获取教室策略（matchArr.fieldName=classroomStrategyName），取 classroomStrategyId
  request:
    body:
      matchArr:
      - type: EXACT
        fieldName: classroomStrategyName
        valueArr:
        - ${param.classroom_strategy_name}
        matchRule: EQ
request:
  dto: ClassroomTeacherConfigWebRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull'
      description: 教室ID
      value: ${prev.query_classroom.output.classroomId}
    teacherMode:
      type: TerminalTypeEnum
      required: false
      constraint: '@Nullable'
      description: 教师机终端类型（可选值：NONE/PC/VDI/IDV/VOI(TCI)/APP/UNKNOWN）
    teacherIp:
      type: String
      required: true
      constraint: '@NotNull'
      description: 教师机终端IP
      value: ${param.teacher_ip}
    teacherPreName:
      type: String
      required: false
      constraint: '@Nullable'
      description: 教师机终端虚机名称（主机名前缀）
    teacherVlanId:
      type: Integer
      required: false
      constraint: '@Nullable @Range(min=2, max=4094)'
      description: 教师机VLAN ID
    teacherVdiLocalDiskConfig:
      type: VdiLocalDiskConfig
      required: false
      constraint: '@Nullable'
      description: 教师VDI本地磁盘配置
    teacherClassroomStrategy:
      type: ClassroomStrategyDTO
      required: false
      constraint: '@Nullable（逻辑上教师机策略必填）'
      description: 教师机教室策略
    vdiLocalDiskStoragePoolList:
      type: List<VdiLocalDiskStorageDTO>
      required: false
      constraint: '@Nullable'
      description: VDI本地磁盘存储池列表
    teacherTciLocalDiskConfig:
      type: TciLocalDiskConfig
      required: false
      constraint: '@Nullable'
      description: 教师TCI本地磁盘配置
    shouldOnlyDeleteDataFromDb:
      type: Boolean
      required: false
      constraint: '@Nullable'
      description: 是否仅从数据库删除数据
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    taskName/taskDesc:
      type: String
      description: 教师机配置任务名称与描述
    taskId:
      type: UUID
      description: 批任务ID（使用 classroomId 作 uniqueId）
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
- api: POST /rcc/classroom/create -> POST /rcc/classroom/select
  produces: $.content[0].classroomId
  purpose: create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId
- api: POST /rcc/classroom/strategy/list
  produces: $.content.itemArr[0].classroomStrategyId
  purpose: 教师机教室策略ID
downstream:
- api: 内部调用:rcc/ClassroomAPI#editTeacherInfo
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: classroomId
  rule: '@NotNull'
  failure: 缺失校验失败
- level: PARAM
  field: teacherIp
  rule: '@NotNull'
  failure: 缺失校验失败
- level: BUSINESS
  field: teacherMode
  rule: 教师机工作模式合法
  failure: 抛 RCDC_RCC_CLASSROOM_TEACHER_WORK_MODE_ILLEGAL
- level: BUSINESS
  field: teacherIp
  rule: 教师机IP不得与现有教室/网络冲突
  failure: 抛 RCDC_RCC_CLASSROOM_IP_HAS_USED / CLASSROOM_IP_CHECK_* 系列
- level: BUSINESS
  field: teacherClassroomStrategy
  rule: 教师机策略不能为空
  failure: 抛 RCDC_RCC_CLASSROOM_TEACHER_CONFIG_STRATEGY_IS_NULL
- level: BUSINESS
  field: 教师机状态
  rule: 教师机未在线、教师桌面未运行/创建/删除中
  failure: 抛 CLASSROOM_TIP_TEACHER_ONLINE / CLASSROOM_TIP_TEACHER_DESKT
- level: BUSINESS
  field: teacherPreName
  rule: 教师机主机名前缀不与学生桌面前缀冲突
  failure: 抛 RCDC_RCC_CLASSROOM_TEACHER_PRE_NAME_CONFLICT_SEAT / _TEACH
assertions:
  success:
  - scenario: 教师机配置合法
    expect: 返回 HTTP 200 + BatchTaskSubmitResult，异步应用教师机配置并成功；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  failure:
  - scenario: 教师机在线
    trigger: 教师终端在线时修改
    expect: status==ERROR；msgKey==CLASSROOM_TIP_TEACHER_ONLINE
  - scenario: 教师机策略为空
    trigger: teacherClassroomStrategy 未传
    expect: status==ERROR；msgKey==RCDC_RCC_CLASSROOM_TEACHER_CONFIG_STRATEGY_IS_NULL
cleanup: []
idempotency:
  level: data_level
  note: 每次提交生成新批任务，但配置应用为最终态收敛；重复提交会重复触发任务执行
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
  - name: strategy_name
    desc: ''
    used_by: 见 setup/request
  - name: classroom_strategy_name
    desc: ''
    used_by: setup/request
---
# POST /rcc/classroom/editTeacherInfo

> 修改教师机配置：先校验终端组数据权限，再同步调 classroomAPI.validateTeacherConfig 做教师机配置校验（IP、主机名前缀、VLAN、VDI/TCI本地磁盘、策略、存储池等），通过后构造 TeacherConfigBatchTaskHandler 提交异步批任务；任务内 processItem 调 classroomAPI.editTeacherInfo 应用配置，接口立即返回 BatchTaskSubmitResult。 ｜ 无特殊权限 ｜ 异步批处理任务（BatchTask，TeacherConfigBatchTaskHandler）

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create -> POST /rcc/classroom/select"]
        A2["POST /rcc/classroom/strategy/list"]
    end
    B["POST /rcc/classroom/editTeacherInfo<br>修改教师机配置：先校验终端组数据权限，再同步调 classroomAPI.val<br>权限: 无"]
    A1 -->|数据| B
    A2 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request/builder/sessionCo"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: classroomAPI.validateTeacherConfig(reque"]
        C4["Step4: 构造 DefaultBatchTaskItem(classroomId, TEA"]
        C5["Step5: new TeacherConfigBatchTaskHandler(batchT"]
        C6["Step6: builder.setTaskName/DESC(TEACHER_CONFIG_"]
        C1 --> C2
        C7["Step7: return success(result)"]
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
| URL | /rcc/classroom/editTeacherInfo |
| Controller | RccClassroomConfigController |
| 方法名 | editTeacherInfo |
| 权限注解 | 无 |
| 执行方式 | 异步批处理任务（BatchTask，TeacherConfigBatchTaskHandler） |
| 业务含义 | 修改教师机配置：先校验终端组数据权限，再同步调 classroomAPI.validateTeacherConfig 做教师机配置校验（IP、主机名前缀、VLAN、VDI/TCI本地磁盘、策略、存储池等），通过后构造 TeacherConfigBatchTaskHandler 提交异步批任务；任务内 processItem 调 classroomAPI.editTeacherInfo 应用配置，接口立即返回 BatchTaskSubmitResult。 |

## 入参详情

### ClassroomTeacherConfigWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull | 教室ID |
| teacherMode | TerminalTypeEnum | 否 | @Nullable | 教师机终端类型 |
| teacherIp | String | 是 | @NotNull | 教师机终端IP |
| teacherPreName | String | 否 | @Nullable | 教师机终端虚机名称（主机名前缀） |
| teacherVlanId | Integer | 否 | @Nullable @Range(min=2, max=4094) | 教师机VLAN ID |
| teacherVdiLocalDiskConfig | VdiLocalDiskConfig | 否 | @Nullable | 教师VDI本地磁盘配置 |
| teacherClassroomStrategy | ClassroomStrategyDTO | 否 | @Nullable（逻辑上教师机策略必填） | 教师机教室策略 |
| vdiLocalDiskStoragePoolList | List<VdiLocalDiskStorageDTO> | 否 | @Nullable | VDI本地磁盘存储池列表 |
| teacherTciLocalDiskConfig | TciLocalDiskConfig | 否 | @Nullable | 教师TCI本地磁盘配置 |
| shouldOnlyDeleteDataFromDb | Boolean | 否 | @Nullable | 是否仅从数据库删除数据 |

## 出参详情

| 返回类型 | DefaultWebResponse（data=BatchTaskSubmitResult） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| taskId | UUID | 批任务ID（使用 classroomId 作 uniqueId） |
| taskName | String | 教师机配置任务名称 |
| taskDesc | String | 教师机配置任务描述 |

## 上游前置业务

### 前置1：POST /rcc/classroom/create -> POST /rcc/classroom/select

create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId（由 field_map 契约映射）

### 前置2：POST /rcc/classroom/strategy/list

教师机教室策略ID（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：TeacherConfigBatchTaskHandler（extends AbstractSingleTaskHandler）

| 步骤 | 说明 |
|---|---|
| 1 | processItem：Assert batchTaskItem 非空 |
| 2 | 调用 classroomAPI.editTeacherInfo(request) 应用教师机配置 |
| 3 | 成功：返回 SUCCESS，msgKey=RCDC_RCC_CLASSROOM_TEACHER_CONFIG_SUCCESS_LOG |
| 4 | 失败：捕获 BusinessException 返回 FAILURE，msgKey=RCDC_RCC_CLASSROOM_TEACHER_CONFIG_FAIL_LOG，args=e.getI18nMessage() |
| 5 | onFinish：failCount==0 → SUCCESS(TEACHER_CONFIG_TASK_SUCCESS)；否则 FAILURE(TEACHER_CONFIG_TASK_FAIL) |

### 处理流程

1. Assert.notNull(request/builder/sessionContext)
2. rccPermissionChecker.checkTerminalGroupPermissionByClassroomId([classroomId], sessionContext)
3. classroomAPI.validateTeacherConfig(request) 同步校验
4. 构造 DefaultBatchTaskItem(classroomId, TEACHER_CONFIG_TASK_NAME)
5. new TeacherConfigBatchTaskHandler(batchTaskItem, classroomAPI, request)
6. builder.setTaskName/DESC(TEACHER_CONFIG_TASK_NAME/DESC).setUniqueId(classroomId).registerHandler(handler).start()
7. return success(result)

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | classroomId | @NotNull | 缺失校验失败 |
| PARAM | teacherIp | @NotNull | 缺失校验失败 |
| BUSINESS | teacherMode | 教师机工作模式合法 | 抛 RCDC_RCC_CLASSROOM_TEACHER_WORK_MODE_ILLEGAL |
| BUSINESS | teacherIp | 教师机IP不得与现有教室/网络冲突 | 抛 RCDC_RCC_CLASSROOM_IP_HAS_USED / CLASSROOM_IP_CHECK_* 系列 |
| BUSINESS | teacherClassroomStrategy | 教师机策略不能为空 | 抛 RCDC_RCC_CLASSROOM_TEACHER_CONFIG_STRATEGY_IS_NULL |
| BUSINESS | 教师机状态 | 教师机未在线、教师桌面未运行/创建/删除中 | 抛 CLASSROOM_TIP_TEACHER_ONLINE / CLASSROOM_TIP_TEACHER_DESKTOP_RUNNING / RCDC_RCC_CLASSROOM_OPERATE_TIP_TEACHER_DESKTOP_CREATING 等 |
| BUSINESS | teacherPreName | 教师机主机名前缀不与学生桌面前缀冲突 | 抛 RCDC_RCC_CLASSROOM_TEACHER_PRE_NAME_CONFLICT_SEAT / _TEACHER_PRE_NAME_EXIST |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| teacherMode | user_input/from_query | 按业务构造 |
| teacherIp | user_input/from_query | 按业务构造 |
| teacherPreName | user_input/from_query | 按业务构造 |
| teacherVlanId | user_input/from_query | 按业务构造 |
| teacherVdiLocalDiskConfig | user_input/from_query | 按业务构造 |
| teacherClassroomStrategy | user_input/from_query | 按业务构造 |
| vdiLocalDiskStoragePoolList | user_input/from_query | 按业务构造 |
| teacherTciLocalDiskConfig | user_input/from_query | 按业务构造 |
| shouldOnlyDeleteDataFromDb | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教师机配置合法 | 返回 HTTP 200 + BatchTaskSubmitResult，异步应用教师机配置并成功 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 教师机在线 | 教师终端在线时修改 | status==ERROR；msgKey==CLASSROOM_TIP_TEACHER_ONLINE |
| 教师机策略为空 | teacherClassroomStrategy 未传 | status==ERROR；msgKey==RCDC_RCC_CLASSROOM_TEACHER_CONFIG_STRATEGY_IS_NULL |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | MEDIUM |
| 说明 | 每次提交生成新批任务，但配置应用为最终态收敛；重复提交会重复触发任务执行 |
