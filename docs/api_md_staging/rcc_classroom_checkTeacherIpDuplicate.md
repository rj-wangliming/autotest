---
version: '2.0'
api:
  url: /rcc/classroom/checkTeacherIpDuplicate
  method: POST
  name: 校验教师机终端 IP 是否与已有教室教师机/学生机 IP 段冲突。先做终端组数据权限校验（classroomId 可空），再调 classroomAPI.che
  controller: RccClassroomConfigController
  method_ref: checkTeacherIpDuplicate
  permission: 无
  exec_mode: 同步
  async: false
  description: 校验教师机终端 IP 是否与已有教室教师机/学生机 IP 段冲突。先做终端组数据权限校验（classroomId 可空），再调 classroomAPI.checkTeacherIpDuplicate 校验；冲突时返回 hasDuplication=true 与错误消息。
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
  dto: ParamVerifiedIpWebRequest
  body:
    classroomId:
      type: UUID
      required: false
      constraint: '@Nullable'
      description: 教室ID（编辑场景必传，创建场景可空）
    teacherIp:
      type: String
      required: true
      constraint: '@NotNull'
      description: 教师机终端IP
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
      description: IP是否冲突（默认 false）
    errorMsg:
      type: String
      description: 冲突的 i18n 错误消息
upstream:
- api: POST /rcc/classroom/create -> POST /rcc/classroom/select
  produces: $.content[0].classroomId
  purpose: create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId
downstream:
- api: 内部调用:rcc/ClassroomAPI#checkTeacherIpDuplicate
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: teacherIp
  rule: '@NotNull'
  failure: 缺失校验失败
- level: BUSINESS
  field: teacherIp
  rule: 教师机IP不得与已有教室教师机/学生机IP段冲突
  failure: 抛 RCDC_RCC_CLASSROOM_IP_HAS_USED 等，接口以 hasDuplication=true 返
assertions:
  success:
  - scenario: 教师机IP未被占用
    expect: $.status=="SUCCESS"；$.content.hasDuplication==false
  failure:
  - scenario: 教师机IP已被其他教室占用
    trigger: teacherIp 与已有教室冲突
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
# POST /rcc/classroom/checkTeacherIpDuplicate

> 校验教师机终端 IP 是否与已有教室教师机/学生机 IP 段冲突。先做终端组数据权限校验（classroomId 可空），再调 classroomAPI.checkTeacherIpDuplicate 校验；冲突时返回 hasDuplication=true 与错误消息。 ｜ 无特殊权限 ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create -> POST /rcc/classroom/select"]
    end
    B["POST /rcc/classroom/checkTeacherIpDuplicate<br>校验教师机终端 IP 是否与已有教室教师机/学生机 IP 段冲突。先做终端组数据<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request/sessionContext)"]
        C2["Step2: rccPermissionChecker.checkTerminalGroupP"]
        C3["Step3: classroomAPI.checkTeacherIpDuplicate(req"]
        C4["Step4: 正常：返回 hasDuplication=false"]
        C5["Step5: 异常：LOGGER.warn 记录教室与IP，设置 hasDuplication"]
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
| URL | /rcc/classroom/checkTeacherIpDuplicate |
| Controller | RccClassroomConfigController |
| 方法名 | checkTeacherIpDuplicate |
| 权限注解 | 无 |
| 执行方式 | 同步 |
| 业务含义 | 校验教师机终端 IP 是否与已有教室教师机/学生机 IP 段冲突。先做终端组数据权限校验（classroomId 可空），再调 classroomAPI.checkTeacherIpDuplicate 校验；冲突时返回 hasDuplication=true 与错误消息。 |

## 入参详情

### ParamVerifiedIpWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 否 | @Nullable | 教室ID（编辑场景必传，创建场景可空） |
| teacherIp | String | 是 | @NotNull | 教师机终端IP |

## 出参详情

| 返回类型 | DefaultWebResponse（data=ResponseHasDuplicateDTO） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| hasDuplication | Boolean | IP是否冲突（默认 false） |
| errorMsg | String | 冲突的 i18n 错误消息 |

## 上游前置业务

### 前置1：POST /rcc/classroom/create -> POST /rcc/classroom/select

create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull(request/sessionContext)
2. rccPermissionChecker.checkTerminalGroupPermissionByClassroomId([request.getClassroomId()], sessionContext)
3. classroomAPI.checkTeacherIpDuplicate(request) 校验教师机IP
4. 正常：返回 hasDuplication=false
5. 异常：LOGGER.warn 记录教室与IP，设置 hasDuplication=true、errorMsg=e.getI18nMessage()

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | teacherIp | @NotNull | 缺失校验失败 |
| BUSINESS | teacherIp | 教师机IP不得与已有教室教师机/学生机IP段冲突 | 抛 RCDC_RCC_CLASSROOM_IP_HAS_USED 等，接口以 hasDuplication=true 返回 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| teacherIp | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教师机IP未被占用 | $.status=="SUCCESS"；$.content.hasDuplication==false |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 教师机IP已被其他教室占用 | teacherIp 与已有教室冲突 | $.status=="SUCCESS"；$.content.hasDuplication==true；$.content.errorMsg 非空 |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 只读校验，无副作用 |
