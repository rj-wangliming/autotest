---
version: '2.0'
api:
  url: /rcc/classroom/editTeacherInfoCheckDesktopPreName
  method: POST
  name: 教室设置中编辑教师机信息时校验教师机主机名前缀是否与座位云桌面主机名前缀冲突。先校验终端组数据权限，构造 EditClassroomTeacherInfoChe
  controller: RccClassroomConfigController
  method_ref: editTeacherInfoCheckDesktopPreName
  permission: 无
  exec_mode: 同步
  async: false
  description: 教室设置中编辑教师机信息时校验教师机主机名前缀是否与座位云桌面主机名前缀冲突。先校验终端组数据权限，构造 EditClassroomTeacherInfoCheckDTO 调 classroomAPI.checkTeacherDesktopNameForEdit 校验；冲突时返回 hasDuplication=true 与错误消息。
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
request:
  dto: EditClassroomTeacherInfoCheckRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull'
      description: 教室ID
      value: ${prev.query_classroom.output.classroomId}
    teacherPreName:
      type: String
      required: true
      constraint: '@NotNull'
      description: 待校验的教师机主机名前缀
      value: ${param.teacher_pre_name}
    teacherMode:
      type: TerminalTypeEnum
      required: true
      constraint: '@NotNull'
      description: 教师机工作模式（可选值：NONE/PC/VDI/IDV/VOI(TCI)/APP/UNKNOWN）
      value: ${param.teacher_mode}
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    hasDuplication:
      type: Boolean
      description: 前缀是否冲突（默认 false）
    errorMsg:
      type: String
      description: 冲突的 i18n 错误消息
upstream:
- api: POST /rcc/classroom/create -> POST /rcc/classroom/select
  produces: $.content[0].classroomId
  purpose: create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId
downstream:
- api: 内部调用:rcc/ClassroomAPI#checkTeacherDesktopNameForEdit
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: classroomId
  rule: '@NotNull'
  failure: 缺失校验失败
- level: PARAM
  field: teacherPreName
  rule: '@NotNull'
  failure: 缺失校验失败
- level: PARAM
  field: teacherMode
  rule: '@NotNull'
  failure: 缺失校验失败
- level: BUSINESS
  field: teacherPreName
  rule: 前缀不与座位桌面前缀冲突
  failure: 抛 RCDC_RCC_CLASSROOM_TEACHER_PRE_NAME_CONFLICT_SEAT / _TEACH
assertions:
  success:
  - scenario: 前缀无冲突
    expect: $.status=="SUCCESS"；$.content.hasDuplication==false
  failure:
  - scenario: 前缀与座位名前缀重复
    trigger: teacherPreName 与某座位桌面前缀重叠
    expect: $.status=="SUCCESS"；$.content.hasDuplication==true；$.content.errorMsg 非空
cleanup: []
idempotency:
  level: non_idempotent
  note: 只读校验，无副作用
params:
  required:
  - name: classroom_name
  - name: teacher_mode
  - name: teacher_pre_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/editTeacherInfoCheckDesktopPreName

> 教室设置中编辑教师机信息时校验教师机主机名前缀是否与座位云桌面主机名前缀冲突。先校验终端组数据权限，构造 EditClassroomTeacherInfoCheckDTO 调 classroomAPI.checkTeacherDesktopNameForEdit 校验；冲突时返回 hasDuplication=true 与错误消息。 ｜ 无特殊权限 ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create -> POST /rcc/classroom/select"]
    end
    B["POST /rcc/classroom/editTeacherInfoCheckDesktopPreName<br>教室设置中编辑教师机信息时校验教师机主机名前缀是否与座位云桌面主机名前缀冲突。先<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request/sessionContext)"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: 构造 EditClassroomTeacherInfoCheckDTO(clas"]
        C4["Step4: classroomAPI.checkTeacherDesktopNameForE"]
        C5["Step5: 成功：返回 hasDuplication=false"]
        C6["Step6: 异常：LOGGER.error 记录，设置 hasDuplication=tru"]
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
| URL | /rcc/classroom/editTeacherInfoCheckDesktopPreName |
| Controller | RccClassroomConfigController |
| 方法名 | editTeacherInfoCheckDesktopPreName |
| 权限注解 | 无 |
| 执行方式 | 同步 |
| 业务含义 | 教室设置中编辑教师机信息时校验教师机主机名前缀是否与座位云桌面主机名前缀冲突。先校验终端组数据权限，构造 EditClassroomTeacherInfoCheckDTO 调 classroomAPI.checkTeacherDesktopNameForEdit 校验；冲突时返回 hasDuplication=true 与错误消息。 |

## 入参详情

### EditClassroomTeacherInfoCheckRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull | 教室ID |
| teacherPreName | String | 是 | @NotNull | 待校验的教师机主机名前缀 |
| teacherMode | TerminalTypeEnum | 是 | @NotNull | 教师机工作模式 |

## 出参详情

| 返回类型 | DefaultWebResponse（data=CheckDuplicationResultDTO） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| hasDuplication | Boolean | 前缀是否冲突（默认 false） |
| errorMsg | String | 冲突的 i18n 错误消息 |

## 上游前置业务

### 前置1：POST /rcc/classroom/create -> POST /rcc/classroom/select

create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull(request/sessionContext)
2. rccPermissionChecker.checkTerminalGroupPermissionByClassroomId([classroomId], sessionContext)
3. 构造 EditClassroomTeacherInfoCheckDTO(classroomId, teacherPreName, teacherMode)
4. classroomAPI.checkTeacherDesktopNameForEdit(dto) 校验前缀冲突
5. 成功：返回 hasDuplication=false
6. 异常：LOGGER.error 记录，设置 hasDuplication=true、errorMsg=e.getI18nMessage()，仍返回成功响应

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | classroomId | @NotNull | 缺失校验失败 |
| PARAM | teacherPreName | @NotNull | 缺失校验失败 |
| PARAM | teacherMode | @NotNull | 缺失校验失败 |
| BUSINESS | teacherPreName | 前缀不与座位桌面前缀冲突 | 抛 RCDC_RCC_CLASSROOM_TEACHER_PRE_NAME_CONFLICT_SEAT / _TEACHER_PRE_NAME_EXIST，接口以 hasDuplication=true 返回 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| teacherPreName | user_input/from_query | 按业务构造 |
| teacherMode | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 前缀无冲突 | $.status=="SUCCESS"；$.content.hasDuplication==false |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 前缀与座位名前缀重复 | teacherPreName 与某座位桌面前缀重叠 | $.status=="SUCCESS"；$.content.hasDuplication==true；$.content.errorMsg 非空 |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 只读校验，无副作用 |
