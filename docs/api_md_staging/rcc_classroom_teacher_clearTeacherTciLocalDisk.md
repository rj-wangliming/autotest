---
version: '2.0'
api:
  url: /rcc/classroom/teacher/clearTeacherTciLocalDisk
  method: POST
  name: 清空教师机TCI本地数据盘：单教室同步执行（teacherOperateAPI.diskClear），多教室提交批量任务异步执行。
  controller: RccTeacherManageController
  method_ref: clearTeacherTciLocalDisk
  permission: '@EnableAuthority'
  exec_mode: batch
  async: false
  description: 清空教师机TCI本地数据盘：单教室同步执行（teacherOperateAPI.diskClear），多教室提交批量任务异步执行。
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
  purpose: 按教室名精确过滤（matchArr.fieldName=classroomName）
  request:
    body:
      matchArr:
      - type: EXACT
        fieldName: classroomName
        valueArr:
        - ${param.classroom_name}
        matchRule: EQ
request:
  dto: ClassroomIdArrWebRequest
  body:
    idArr:
      type: UUID[]
      required: true
      constraint: '@NotEmpty 非空'
      description: 教室ID数组
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
      description: 批量场景下的任务提交结果
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
- api: POST /rcc/classroom/terminal/list
  produces: $.content.itemArr[*].classroomId
  purpose: 教室ID数组（ClassroomIdArrWebRequest.idArr）来自教室终端列表查询出参（ViewClassroomInfoEntity.classroomId）
downstream:
- api: 内部调用:PlatformTerminalOperatorAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: idArr
  rule: 非空
  failure: 参数校验失败（@NotEmpty）
- level: BIZ
  field: classroom
  rule: 教室必须存在且有教师终端配置且终端类型非PC
  failure: RCDC_RCC_TEACHER_OPERATE_CLASSROOM_NOT_FOUND / TEACHER_CONFI
assertions:
  success:
  - scenario: 教室存在教师终端且清空成功
    expect: 单条返回成功key或批量任务成功；轮询 content.taskId（2000ms 间隔）至终态 batchTaskItemStatus∈["SUCCESS"]
  failure:
  - scenario: 教室无教师终端配置
    trigger: classroomTeacherEntity 为空或 terminalId 为空
    expect: 单条返回 RCDC_RCC_TEACHER_OPERATE_CLEAR_DISK_FAIL，批量单项失败
  - scenario: 教师机类型为PC不支持
    trigger: teacherType 为 PC
    expect: $.status==ERROR；msgKey==RCDC_RCC_TEACHER_OPERATE_CLASSROOM_TEACHER_PC_NOT_SUPPORT
cleanup: []
idempotency:
  level: data_level
  note: 清空数据盘为可重复操作（结果趋于一致），但会删除终端本地数据，需谨慎重复
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/teacher/clearTeacherTciLocalDisk

> 清空教师机TCI本地数据盘：单教室同步执行（teacherOperateAPI.diskClear），多教室提交批量任务异步执行。 ｜ @EnableAuthority ｜ batch

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/terminal/list"]
    end
    B["POST /rcc/classroom/teacher/clearTeacherTciLocalDisk<br>清空教师机TCI本地数据盘：单教室同步执行（teacherOperateAPI.<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: 断言 request 与 builder 非空"]
        C2["Step2: 取 classroomIdArr"]
        C3["Step3: 单条：clearSingleTeacherLocalDisk 同步执行 disk"]
        C4["Step4: 多条：构建任务项，ClearTeacherTerminalDataDiskBat"]
        C5["Step5: 返回结果"]
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
| URL | /rcc/classroom/teacher/clearTeacherTciLocalDisk |
| Controller | RccTeacherManageController |
| 方法名 | clearTeacherTciLocalDisk |
| 权限注解 | @EnableAuthority |
| 执行方式 | batch |
| 业务含义 | 清空教师机TCI本地数据盘：单教室同步执行（teacherOperateAPI.diskClear），多教室提交批量任务异步执行。 |

## 入参详情

### ClassroomIdArrWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| idArr | UUID[] | 是 | @NotEmpty 非空 | 教室ID数组 |

## 出参详情

| 返回类型 | DefaultWebResponse |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| content | BatchTaskSubmitResult | 批量场景下的任务提交结果 |

## 上游前置业务

### 前置1：POST /rcc/classroom/terminal/list

教室ID数组（ClassroomIdArrWebRequest.idArr）来自教室终端列表查询出参（ViewClassroomInfoEntity.classroomId）（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：ClearTeacherTerminalDataDiskBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | teacherOperateAPI.diskClear(classroomId) 清空教师机数据盘 |
| 2 | obtainClassroomName 取教室名 |
| 3 | 成功记 RCDC_RCC_TEACHER_OPERATE_CLEAR_DISK_SUCCESS_LOG，失败记 FAIL_LOG 并返回 FAILURE 项 |

### 处理流程

1. 断言 request 与 builder 非空
2. 取 classroomIdArr
3. 单条：clearSingleTeacherLocalDisk 同步执行 diskClear 并记审计，成功返回业务key
4. 多条：构建任务项，ClearTeacherTerminalDataDiskBatchTaskHandler 提交批量任务
5. 返回结果

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | idArr | 非空 | 参数校验失败（@NotEmpty） |
| BIZ | classroom | 教室必须存在且有教师终端配置且终端类型非PC | RCDC_RCC_TEACHER_OPERATE_CLASSROOM_NOT_FOUND / TEACHER_CONFIG_NOT_FOUND / TERMINAL_NOT_FOUND / CLASSROOM_TEACHER_PC_NOT_SUPPORT / CLASSROOM_TERCHER_TERMINAL_ID_IS_NULL |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| idArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教室存在教师终端且清空成功 | 单条返回成功key或批量任务成功 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 教室无教师终端配置 | classroomTeacherEntity 为空或 terminalId 为空 | 单条返回 RCDC_RCC_TEACHER_OPERATE_CLEAR_DISK_FAIL，批量单项失败 |
| 教师机类型为PC不支持 | teacherType 为 PC | RCDC_RCC_TEACHER_OPERATE_CLASSROOM_TEACHER_PC_NOT_SUPPORT |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | medium |
| 说明 | 清空数据盘为可重复操作（结果趋于一致），但会删除终端本地数据，需谨慎重复 |
