---
version: '2.0'
api:
  url: /rcc/classroom/checkStudentIpDuplicate
  method: POST
  name: 校验学生机可接入终端 IP 地址段（startIp-endIp）是否与已有教室/网络策略/物理服务器等冲突。classroomId 可为空（创建场景）；先做终端
  controller: RccClassroomConfigController
  method_ref: checkStudentIpDuplicate
  permission: 无
  exec_mode: 同步
  async: false
  description: 校验学生机可接入终端 IP 地址段（startIp-endIp）是否与已有教室/网络策略/物理服务器等冲突。classroomId 可为空（创建场景）；先做终端组数据权限校验，再调 classroomAPI.checkIPSegmentConflict 校验；冲突时返回 hasDuplication=true 与错误消息。
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
  dto: ParamVerifiedIpSegmentWebRequest
  body:
    classroomId:
      type: UUID
      required: false
      constraint: '@Nullable'
      description: 教室ID（编辑场景必传，创建场景可空）
    studentStartIp:
      type: String
      required: true
      constraint: '@NotNull'
      description: 学生机可接入终端起始IP
    studentEndIp:
      type: String
      required: true
      constraint: '@NotNull'
      description: 学生机可接入终端终止IP
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
      description: IP段是否冲突（默认 false）
    errorMsg:
      type: String
      description: 冲突的 i18n 错误消息
upstream:
- api: POST /rcc/classroom/create -> POST /rcc/classroom/select
  produces: $.content[0].classroomId
  purpose: create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId
downstream:
- api: 内部调用:rcc/ClassroomAPI#checkIPSegmentConflict
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: studentStartIp
  rule: '@NotNull'
  failure: 缺失校验失败
- level: PARAM
  field: studentEndIp
  rule: '@NotNull'
  failure: 缺失校验失败
- level: BUSINESS
  field: studentStartIp/studentEndIp
  rule: IP段合法（起始≤终止、同网段、非广播/网络地址）且不与现有教室/网络策略冲突
  failure: 抛 CLASSROOM_IP_CHECK_* 系列（RCDC_RCC_CLASSROOM_IP_HAS_USED 等），
assertions:
  success:
  - scenario: IP段未被占用且合法
    expect: $.status=="SUCCESS"；$.content.hasDuplication==false
  failure:
  - scenario: IP段与已有教室冲突
    trigger: studentStartIp-studentEndIp 与其他教室段重叠
    expect: $.status=="SUCCESS"；$.content.hasDuplication==true；$.content.errorMsg 非空
cleanup: []
idempotency:
  level: non_idempotent
  note: 只读校验，无副作用
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/checkStudentIpDuplicate

> 校验学生机可接入终端 IP 地址段（startIp-endIp）是否与已有教室/网络策略/物理服务器等冲突。classroomId 可为空（创建场景）；先做终端组数据权限校验，再调 classroomAPI.checkIPSegmentConflict 校验；冲突时返回 hasDuplication=true 与错误消息。 ｜ 无特殊权限 ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create -> POST /rcc/classroom/select"]
    end
    B["POST /rcc/classroom/checkStudentIpDuplicate<br>校验学生机可接入终端 IP 地址段（startIp-endIp）是否与已有教室/<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request/sessionContext)"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: classroomAPI.checkIPSegmentConflict(requ"]
        C4["Step4: 正常：返回 hasDuplication=false"]
        C5["Step5: 异常：LOGGER.warn 记录 IP 段信息，设置 hasDuplicati"]
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
| URL | /rcc/classroom/checkStudentIpDuplicate |
| Controller | RccClassroomConfigController |
| 方法名 | checkStudentIpDuplicate |
| 权限注解 | 无 |
| 执行方式 | 同步 |
| 业务含义 | 校验学生机可接入终端 IP 地址段（startIp-endIp）是否与已有教室/网络策略/物理服务器等冲突。classroomId 可为空（创建场景）；先做终端组数据权限校验，再调 classroomAPI.checkIPSegmentConflict 校验；冲突时返回 hasDuplication=true 与错误消息。 |

## 入参详情

### ParamVerifiedIpSegmentWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 否 | @Nullable | 教室ID（编辑场景必传，创建场景可空） |
| studentStartIp | String | 是 | @NotNull | 学生机可接入终端起始IP |
| studentEndIp | String | 是 | @NotNull | 学生机可接入终端终止IP |

## 出参详情

| 返回类型 | DefaultWebResponse（data=ResponseHasDuplicateDTO） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| hasDuplication | Boolean | IP段是否冲突（默认 false） |
| errorMsg | String | 冲突的 i18n 错误消息 |

## 上游前置业务

### 前置1：POST /rcc/classroom/create -> POST /rcc/classroom/select

create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull(request/sessionContext)
2. rccPermissionChecker.checkTerminalGroupPermissionByClassroomId([request.getClassroomId()], sessionContext)
3. classroomAPI.checkIPSegmentConflict(request) 执行IP段冲突校验
4. 正常：返回 hasDuplication=false
5. 异常：LOGGER.warn 记录 IP 段信息，设置 hasDuplication=true、errorMsg=e.getI18nMessage()

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | studentStartIp | @NotNull | 缺失校验失败 |
| PARAM | studentEndIp | @NotNull | 缺失校验失败 |
| BUSINESS | studentStartIp/studentEndIp | IP段合法（起始≤终止、同网段、非广播/网络地址）且不与现有教室/网络策略冲突 | 抛 CLASSROOM_IP_CHECK_* 系列（RCDC_RCC_CLASSROOM_IP_HAS_USED 等），接口以 hasDuplication=true 返回 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| studentStartIp | user_input/from_query | 按业务构造 |
| studentEndIp | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| IP段未被占用且合法 | $.status=="SUCCESS"；$.content.hasDuplication==false |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| IP段与已有教室冲突 | studentStartIp-studentEndIp 与其他教室段重叠 | $.status=="SUCCESS"；$.content.hasDuplication==true；$.content.errorMsg 非空 |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 只读校验，无副作用 |
