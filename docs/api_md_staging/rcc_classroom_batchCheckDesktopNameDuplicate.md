---
version: '2.0'
api:
  url: /rcc/classroom/batchCheckDesktopNameDuplicate
  method: POST
  name: 教室创建弹窗中批量校验教师机主机名前缀与座位云桌面主机名前缀是否冲突/重复。教师机为非PC工作模式时教师机主机名前缀必填（为空抛 RCDC_RCC_CLASSR
  controller: RccClassroomConfigController
  method_ref: batchCheckDesktopNameDuplicate
  permission: 无
  exec_mode: 同步
  async: false
  description: 教室创建弹窗中批量校验教师机主机名前缀与座位云桌面主机名前缀是否冲突/重复。教师机为非PC工作模式时教师机主机名前缀必填（为空抛 RCDC_RCC_CLASSROOM_TEACHER_PRE_NAME_MUST_NOT_BE_NULL），随后将入参拷贝为 BatchCheckDesktopNameDTO 调 classroomAPI.batchCheckDesktopNameDuplicate 做
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
request:
  dto: BatchCheckDesktopNameRequest
  body:
    desktopPreName:
      type: String
      required: true
      constraint: '@NotNull @Size(max=9)'
      description: 学生机座位名前缀
      value: ${param.desktop_pre_name}
    desktopNameStartNum:
      type: Integer
      required: true
      constraint: '@NotNull @Range(min=1, max=65535)'
      description: 云桌面主机名起始值
      value: ${param.desktop_name_start_num}
    studentModeArr:
      type: TerminalTypeEnum[]
      required: true
      constraint: '@NotNull'
      description: 学生机工作模式数组（可选值：NONE/PC/VDI/IDV/VOI(TCI)/APP/UNKNOWN）
    desktopNum:
      type: Integer
      required: false
      constraint: '@Nullable @Range(min=1, max=1000)'
      description: 座位数量
    teacherPreName:
      type: String
      required: false
      constraint: '@Nullable；教师机非PC模式时逻辑必填'
      description: 教师机主机名前缀
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
      description: 是否存在主机名前缀冲突（默认 false）
    errorMsg:
      type: String
      description: 冲突 i18n 错误消息
upstream:
- api: 内部调用:rcc/ClassroomAPI
  purpose: 批量校验教师机/座位云桌面主机名前缀冲突，冲突抛 BusinessException
downstream:
- api: 内部调用:rcc/ClassroomAPI#batchCheckDesktopNameDuplicate
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: desktopPreName
  rule: '@NotNull @Size(max=9)'
  failure: 非空/长度超9校验失败
- level: PARAM
  field: desktopNameStartNum
  rule: '@NotNull @Range(1-65535)'
  failure: 越界校验失败
- level: PARAM
  field: studentModeArr
  rule: '@NotNull'
  failure: 缺失校验失败
- level: PARAM
  field: teacherMode
  rule: '@NotNull'
  failure: 缺失校验失败
- level: BUSINESS
  field: teacherPreName
  rule: 教师机非PC模式（worModeIncludePC=false）时必填
  failure: 抛 RCDC_RCC_CLASSROOM_TEACHER_PRE_NAME_MUST_NOT_BE_NULL
- level: BUSINESS
  field: teacherPreName/desktopPreName
  rule: 前缀不得与已有教室/桌面冲突
  failure: 抛 RCDC_RCC_CLASSROOM_TEACHER_PRE_NAME_EXIST / _CONFLICT_SEAT
assertions:
  success:
  - scenario: 传入无冲突的座位名前缀与主机名前缀
    expect: $.status=="SUCCESS"；$.content.hasDuplication==false
  failure:
  - scenario: 教师机为非PC模式且 teacherPreName 为空
    trigger: teacherMode=TCI/IDV 等非PC模式，teacherPreName 缺省
    expect: status==ERROR；msgKey==RCDC_RCC_CLASSROOM_TEACHER_PRE_NAME_MUST_NOT_BE_NULL
  - scenario: 教师机主机名前缀与已有座位名冲突
    trigger: 前缀已被其他教室使用
    expect: $.status=="SUCCESS"；$.content.hasDuplication==true；$.content.errorMsg 非空
cleanup: []
idempotency:
  level: non_idempotent
  note: 只读校验接口，重复调用无副作用
---
# POST /rcc/classroom/batchCheckDesktopNameDuplicate

> 教室创建弹窗中批量校验教师机主机名前缀与座位云桌面主机名前缀是否冲突/重复。教师机为非PC工作模式时教师机主机名前缀必填（为空抛 RCDC_RCC_CLASSROOM_TEACHER_PRE_NAME_MUST_NOT_BE_NULL），随后将入参拷贝为 BatchCheckDesktopNameDTO 调 classroomAPI.batchCheckDesktopNameDuplicate 做前缀冲突校验；冲突时接口仍返回成功，但 data.hasDuplication=true 并携带 i18n 错误消息。 ｜ 无特殊权限 ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/batchCheckDesktopNameDuplicate<br>教室创建弹窗中批量校验教师机主机名前缀与座位云桌面主机名前缀是否冲突/重复。教师<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request) 校验入参非空"]
        C2["Step2: 若 !TerminalTypeEnum.worModeIncludePC(req"]
        C3["Step3: BeanUtils.copyProperties 将请求拷贝到 BatchChe"]
        C4["Step4: classroomAPI.batchCheckDesktopNameDuplic"]
        C5["Step5: 成功：返回 hasDuplication=false 的空 CheckDupli"]
        C6["Step6: 失败：LOGGER.error 记录日志，设置 hasDuplication=t"]
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
| URL | /rcc/classroom/batchCheckDesktopNameDuplicate |
| Controller | RccClassroomConfigController |
| 方法名 | batchCheckDesktopNameDuplicate |
| 权限注解 | 无 |
| 执行方式 | 同步 |
| 业务含义 | 教室创建弹窗中批量校验教师机主机名前缀与座位云桌面主机名前缀是否冲突/重复。教师机为非PC工作模式时教师机主机名前缀必填（为空抛 RCDC_RCC_CLASSROOM_TEACHER_PRE_NAME_MUST_NOT_BE_NULL），随后将入参拷贝为 BatchCheckDesktopNameDTO 调 classroomAPI.batchCheckDesktopNameDuplicate 做前缀冲突校验；冲突时接口仍返回成功，但 data.hasDuplication=true 并携带 i18n 错误消息。 |

## 入参详情

### BatchCheckDesktopNameRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| desktopPreName | String | 是 | @NotNull @Size(max=9) | 学生机座位名前缀 |
| desktopNameStartNum | Integer | 是 | @NotNull @Range(min=1, max=65535) | 云桌面主机名起始值 |
| studentModeArr | TerminalTypeEnum[] | 是 | @NotNull | 学生机工作模式数组 |
| desktopNum | Integer | 否 | @Nullable @Range(min=1, max=1000) | 座位数量 |
| teacherPreName | String | 否 | @Nullable；教师机非PC模式时逻辑必填 | 教师机主机名前缀 |
| teacherMode | TerminalTypeEnum | 是 | @NotNull | 教师机工作模式 |

## 出参详情

| 返回类型 | DefaultWebResponse（data=CheckDuplicationResultDTO） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| hasDuplication | Boolean | 是否存在主机名前缀冲突（默认 false） |
| errorMsg | String | 冲突 i18n 错误消息 |

## 上游前置业务

（无上游数据依赖）
## 内部处理流程

### 处理流程

1. Assert.notNull(request) 校验入参非空
2. 若 !TerminalTypeEnum.worModeIncludePC(request.getTeacherMode()) 且 teacherPreName 为空，抛 BusinessException(RCDC_RCC_CLASSROOM_TEACHER_PRE_NAME_MUST_NOT_BE_NULL)
3. BeanUtils.copyProperties 将请求拷贝到 BatchCheckDesktopNameDTO
4. classroomAPI.batchCheckDesktopNameDuplicate(dto) 执行前缀冲突校验
5. 成功：返回 hasDuplication=false 的空 CheckDuplicationResultDTO
6. 失败：LOGGER.error 记录日志，设置 hasDuplication=true、errorMsg=e.getI18nMessage()，仍返回成功响应

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | desktopPreName | @NotNull @Size(max=9) | 非空/长度超9校验失败 |
| PARAM | desktopNameStartNum | @NotNull @Range(1-65535) | 越界校验失败 |
| PARAM | studentModeArr | @NotNull | 缺失校验失败 |
| PARAM | teacherMode | @NotNull | 缺失校验失败 |
| BUSINESS | teacherPreName | 教师机非PC模式（worModeIncludePC=false）时必填 | 抛 RCDC_RCC_CLASSROOM_TEACHER_PRE_NAME_MUST_NOT_BE_NULL |
| BUSINESS | teacherPreName/desktopPreName | 前缀不得与已有教室/桌面冲突 | 抛 RCDC_RCC_CLASSROOM_TEACHER_PRE_NAME_EXIST / _CONFLICT_SEAT 等，接口以 hasDuplication=true 返回 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| desktopPreName | user_input/from_query | 按业务构造 |
| desktopNameStartNum | user_input/from_query | 按业务构造 |
| studentModeArr | user_input/from_query | 按业务构造 |
| desktopNum | user_input/from_query | 按业务构造 |
| teacherPreName | user_input/from_query | 按业务构造 |
| teacherMode | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 传入无冲突的座位名前缀与主机名前缀 | $.status=="SUCCESS"；$.content.hasDuplication==false |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 教师机为非PC模式且 teacherPreName 为空 | teacherMode=TCI/IDV 等非PC模式，teacherPreName 缺省 | status==ERROR；msgKey==RCDC_RCC_CLASSROOM_TEACHER_PRE_NAME_MUST_NOT_BE_NULL |
| 教师机主机名前缀与已有座位名冲突 | 前缀已被其他教室使用 | $.status=="SUCCESS"；$.content.hasDuplication==true；$.content.errorMsg 非空 |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 只读校验接口，重复调用无副作用 |
