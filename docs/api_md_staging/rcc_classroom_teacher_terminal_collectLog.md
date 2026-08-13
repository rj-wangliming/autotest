---
version: '2.0'
api:
  url: /rcc/classroom/teacher/terminal/collectLog
  method: POST
  name: 教师机终端日志收集：按教室向教师终端下发日志收集指令，返回终端ID供后续查询状态。
  controller: RccTeacherManageController
  method_ref: collectTeacherTerminalLog
  permission: '@EnableAuthority'
  exec_mode: sync
  async: false
  description: 教师机终端日志收集：按教室向教师终端下发日志收集指令，返回终端ID供后续查询状态。
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
  purpose: 按教室名精确过滤（matchArr.fieldName=classroomName）
  request:
    body:
      matchArr:
      - fieldName: classroomName
        matchType: EQUAL
        value: ${param.classroom_name}
- name: collect_log
  api: POST /rcc/classroom/teacher/terminal/collectLog
  purpose: 发起教师机日志收集
request:
  dto: IdWebRequest
  body:
    id:
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
      type: TeacherOperateResponse
      description: 操作响应
    content_terminalId:
      type: String
      description: 教师终端ID（用于 collectLog/get 查询状态）
upstream:
- api: POST /rcc/classroom/terminal/list
  produces: $.content.itemArr[0].classroomId
  purpose: 教室ID在创建教室(POST /rcc/classroom/create)后经教室终端列表查询获得（ViewClassroomInfoEntity.classroomId）
downstream:
- api: 内部调用:PlatformTerminalLogAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: id
  rule: 非空
  failure: 参数校验失败（@NotNull）
- level: BIZ
  field: classroom
  rule: 教室存在且配置教师终端且类型非PC
  failure: RCDC_RCC_TEACHER_OPERATE_CLASSROOM_NOT_FOUND / TEACHER_CONFI
assertions:
  success:
  - scenario: 教室配置教师终端且下发成功
    expect: $.status=="SUCCESS" 且 $.content.terminalId 非空；审计 RCDC_RCC_TEACHER_COLLECT_LOG_SUCCESS_LOG
  failure:
  - scenario: 教室无教师终端配置
    trigger: 教师配置或终端缺失
    expect: $.status=="ERROR" 且 $.msgKey∈["rcdc_rcc_teacher_operate_classroom_not_found","rcdc_rcc_teacher_operate_teacher_config_not_found","rcdc_rcc_teacher_operate_classroom_tercher_terminal_id_is_null","rcdc_rcc_teacher_operate_terminal_not_found"]；审计 rcdc_rcc_teacher_collect_log_fail_log
cleanup: []
idempotency:
  level: data_level
  note: 重复调用会重复下发日志收集，会产生多条日志记录
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/teacher/terminal/collectLog

> 教师机终端日志收集：按教室向教师终端下发日志收集指令，返回终端ID供后续查询状态。 ｜ @EnableAuthority ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/terminal/list"]
    end
    B["POST /rcc/classroom/teacher/terminal/collectLog<br>教师机终端日志收集：按教室向教师终端下发日志收集指令，返回终端ID供后续查询状态<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: 断言 request 非空"]
        C2["Step2: obtainClassroomName(classroomId) 取教室名"]
        C3["Step3: teacherOperateAPI.collectLog(classroomId"]
        C4["Step4: 记成功审计，构造 TeacherOperateResponse 返回 termi"]
        C5["Step5: catch BusinessException：记失败审计后重新抛出"]
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
| URL | /rcc/classroom/teacher/terminal/collectLog |
| Controller | RccTeacherManageController |
| 方法名 | collectTeacherTerminalLog |
| 权限注解 | @EnableAuthority |
| 执行方式 | sync |
| 业务含义 | 教师机终端日志收集：按教室向教师终端下发日志收集指令，返回终端ID供后续查询状态。 |

## 入参详情

### IdWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| id | UUID | 是 | @NotNull 非空 | 教室ID |

## 出参详情

| 返回类型 | DefaultWebResponse |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| content | TeacherOperateResponse | 操作响应 |
| content.terminalId | String | 教师终端ID（用于 collectLog/get 查询状态） |

## 上游前置业务

### 前置1：POST /rcc/classroom/terminal/list

教室ID在创建教室(POST /rcc/classroom/create)后经教室终端列表查询获得（ViewClassroomInfoEntity.classroomId）（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. 断言 request 非空
2. obtainClassroomName(classroomId) 取教室名
3. teacherOperateAPI.collectLog(classroomId)：校验教室/教师终端/终端类型后下发收集指令并返回terminalId
4. 记成功审计，构造 TeacherOperateResponse 返回 terminalId
5. catch BusinessException：记失败审计后重新抛出

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | id | 非空 | 参数校验失败（@NotNull） |
| BIZ | classroom | 教室存在且配置教师终端且类型非PC | RCDC_RCC_TEACHER_OPERATE_CLASSROOM_NOT_FOUND / TEACHER_CONFIG_NOT_FOUND / TERMINAL_NOT_FOUND / CLASSROOM_TEACHER_PC_NOT_SUPPORT |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| id | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教室配置教师终端且下发成功 | $.status=="SUCCESS" 且 $.content.terminalId 非空；审计 RCDC_RCC_TEACHER_COLLECT_LOG_SUCCESS_LOG |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 教室无教师终端配置 | 教师配置或终端缺失 | $.status=="ERROR" 且 $.msgKey∈["rcdc_rcc_teacher_operate_classroom_not_found","rcdc_rcc_teacher_operate_teacher_config_not_found","rcdc_rcc_teacher_operate_classroom_tercher_terminal_id_is_null","rcdc_rcc_teacher_operate_terminal_not_found"]；审计 rcdc_rcc_teacher_collect_log_fail_log |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | medium |
| 说明 | 重复调用会重复下发日志收集，会产生多条日志记录 |
