---
version: '2.0'
api:
  url: /rcc/classroom/editClassroomBasicInfo
  method: POST
  name: 修改教室基本配置（名称、描述）。先校验终端组数据权限，调 classroomAPI.editClassroomBasicInfo 更新；成功记录更新成功审计日志
  controller: RccClassroomConfigController
  method_ref: editClassroomBasicInfo
  permission: 无
  exec_mode: 同步
  async: false
  description: 修改教室基本配置（名称、描述）。先校验终端组数据权限，调 classroomAPI.editClassroomBasicInfo 更新；成功记录更新成功审计日志并返回 ResponseClassroomIdDTO，失败记录失败审计日志后重新抛出异常。
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
  dto: ClassroomBasicConfigWebRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull'
      description: 教室ID
    classroomName:
      type: String
      required: true
      constraint: '@NotNull @Size(min=3, max=20)'
      description: 新教室名称
    classroomDesc:
      type: String
      required: false
      constraint: '@Nullable @Size(max=200)'
      description: 新教室描述
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    classroomId:
      type: UUID
      description: 教室ID
    classroomName:
      type: String
      description: 修改后的教室名称
    status:
      type: Integer
      description: 1=教室创建成功但座位创建失败（默认0）
    errorMessage:
      type: String
      description: 错误消息（可选）
upstream:
- api: POST /rcc/classroom/create -> POST /rcc/classroom/select
  produces: $.content[0].classroomId
  purpose: create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId
downstream:
- api: POST /rcc/classroom/getInfo|getClassroomBasicInfo|image/*
  purpose: 出参 ResponseClassroomIdDTO.classroomId 回显教室ID
constraints:
- level: PARAM
  field: classroomId
  rule: '@NotNull'
  failure: 缺失校验失败
- level: PARAM
  field: classroomName
  rule: '@NotNull @Size(3-20)'
  failure: 非空/长度校验失败
- level: BUSINESS
  field: classroomId
  rule: 教室存在且有数据权限
  failure: 不存在抛 RCDC_CLASSROOM_NOT_FIND；权限不足抛权限异常
- level: BUSINESS
  field: classroomName
  rule: 新名称不与其它教室重复
  failure: 抛 RCDC_RCC_CLASSROOM_NAME_DUPLICATION
assertions:
  success:
  - scenario: 合法的新名称/描述
    expect: $.status=="SUCCESS"；$.content.classroomId 非空
  failure:
  - scenario: 教室ID不存在
    trigger: classroomId 无效
    expect: status==ERROR（BusinessException 重新抛出，如 RCDC_CLASSROOM_NOT_FIND）
  - scenario: 新名称与其他教室重复
    trigger: classroomName 被占用
    expect: status==ERROR；msgKey==RCDC_RCC_CLASSROOM_NAME_DUPLICATION
cleanup: []
idempotency:
  level: data_level
  note: 按 classroomId 整体更新基本配置，重复提交收敛于最终值；名称冲突时失败
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/editClassroomBasicInfo

> 修改教室基本配置（名称、描述）。先校验终端组数据权限，调 classroomAPI.editClassroomBasicInfo 更新；成功记录更新成功审计日志并返回 ResponseClassroomIdDTO，失败记录失败审计日志后重新抛出异常。 ｜ 无特殊权限 ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create -> POST /rcc/classroom/select"]
    end
    B["POST /rcc/classroom/editClassroomBasicInfo<br>修改教室基本配置（名称、描述）。先校验终端组数据权限，调 classroomAP<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request/sessionContext)"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: classroomAPI.editClassroomBasicInfo(requ"]
        C4["Step4: 成功：auditLogAPI.recordLog(RCDC_CLASSROOM_"]
        C5["Step5: 失败：取教室名（classroomAPI.getClassroomName）记录"]
        C6["Step6: return DefaultWebResponse.Builder.succes"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
        C4 --> C5
        C5 --> C6
    end
    B --> C1
    subgraph 下游消费方
        D1["POST /rcc/classroom/getInfo|getClassroomBasicInfo|image/*"]
    end
    B -->|数据| D1
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rcc/classroom/editClassroomBasicInfo |
| Controller | RccClassroomConfigController |
| 方法名 | editClassroomBasicInfo |
| 权限注解 | 无 |
| 执行方式 | 同步 |
| 业务含义 | 修改教室基本配置（名称、描述）。先校验终端组数据权限，调 classroomAPI.editClassroomBasicInfo 更新；成功记录更新成功审计日志并返回 ResponseClassroomIdDTO，失败记录失败审计日志后重新抛出异常。 |

## 入参详情

### ClassroomBasicConfigWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull | 教室ID |
| classroomName | String | 是 | @NotNull @Size(min=3, max=20) | 新教室名称 |
| classroomDesc | String | 否 | @Nullable @Size(max=200) | 新教室描述 |

## 出参详情

| 返回类型 | DefaultWebResponse（data=ResponseClassroomIdDTO，msg=CLASSROOM_OPERATE_TIP_SUCCESS） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| classroomId | UUID | 教室ID |
| classroomName | String | 修改后的教室名称 |
| status | Integer | 1=教室创建成功但座位创建失败（默认0） |
| errorMessage | String | 错误消息（可选） |

## 上游前置业务

### 前置1：POST /rcc/classroom/create -> POST /rcc/classroom/select

create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull(request/sessionContext)
2. rccPermissionChecker.checkTerminalGroupPermissionByClassroomId([classroomId], sessionContext)
3. classroomAPI.editClassroomBasicInfo(request) 更新基本配置
4. 成功：auditLogAPI.recordLog(RCDC_CLASSROOM_RECORD_LOG_UPDATE_SUCCESS, 教室名, CLASSROOM_RECORD_LOG_I18MESSAGE_BASIC)
5. 失败：取教室名（classroomAPI.getClassroomName）记录 RCDC_CLASSROOM_RECORD_LOG_UPDATE_FAILED 审计后 throw e
6. return DefaultWebResponse.Builder.success(CLASSROOM_OPERATE_TIP_SUCCESS, classroomIdDTO)

## 下游消费方

### 消费1：POST /rcc/classroom/getInfo|getClassroomBasicInfo|image/*

出参 ResponseClassroomIdDTO.classroomId 回显教室ID（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | classroomId | @NotNull | 缺失校验失败 |
| PARAM | classroomName | @NotNull @Size(3-20) | 非空/长度校验失败 |
| BUSINESS | classroomId | 教室存在且有数据权限 | 不存在抛 RCDC_CLASSROOM_NOT_FIND；权限不足抛权限异常 |
| BUSINESS | classroomName | 新名称不与其它教室重复 | 抛 RCDC_RCC_CLASSROOM_NAME_DUPLICATION |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| classroomName | user_input/from_query | 按业务构造 |
| classroomDesc | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 合法的新名称/描述 | $.status=="SUCCESS"；$.content.classroomId 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 教室ID不存在 | classroomId 无效 | status==ERROR（BusinessException 重新抛出，如 RCDC_CLASSROOM_NOT_FIND） |
| 新名称与其他教室重复 | classroomName 被占用 | status==ERROR；msgKey==RCDC_RCC_CLASSROOM_NAME_DUPLICATION |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | MEDIUM |
| 说明 | 按 classroomId 整体更新基本配置，重复提交收敛于最终值；名称冲突时失败 |
