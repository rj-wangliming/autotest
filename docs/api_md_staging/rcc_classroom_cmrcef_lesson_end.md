---
version: '2.0'
api:
  url: /rcc/classroom/cmrcef/lesson/end
  method: POST
  name: CMR内嵌页面（CEF）下课：提交下课批处理任务，返回教室ID与批处理任务ID
  controller: RccClassroomCmrcefController
  method_ref: endLessonForCef
  permission: 无
  exec_mode: async
  async: false
  description: CMR内嵌页面（CEF）下课：提交下课批处理任务，返回教室ID与批处理任务ID
setup:
- name: up_1
  api: 内部调用:lessonService
  method: POST
  produces: BatchTaskSubmitResult
  purpose: （内部调用）
request:
  dto: CefEndLessonWebRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull，教室ID'
      description: 要下课的教室
    token:
      type: String
      required: true
      constraint: '@NotNull，AES加密TOKEN'
      description: 由@ClassroomCef拦截器校验
    closeTerminal:
      type: Boolean
      required: false
      constraint: '@Nullable，默认false'
      description: 是否同时关闭终端
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
    lessonTaskId:
      type: UUID
      description: 下课批处理任务ID
upstream:
- api: 内部调用:lessonService
  purpose: 执行下课校验、准备与批处理下发
downstream:
- api: 内部调用:classroomLessonAPI
  purpose: 内部调用（非 HTTP 端点）
- api: 内部调用:lessonFactory
  purpose: 内部调用（非 HTTP 端点）
- api: 内部调用:cmrClientAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: auth
  field: token
  rule: AES解密等于classroomId
  failure: rcdc_rcc_classroom_cef_token_check_failure
- level: business
  field: classroomId
  rule: 上课镜像必须存在
  failure: rcdc_rcc_classroom_ending_class_fail_desc_for_classroom_imag
- level: business
  field: classroomId
  rule: 教室信息必须存在
  failure: rcdc_rcc_classroom_ending_class_fail_desc_for_no_classroom
- level: business
  field: seat
  rule: 无座位时直接强制下课
  failure: rcdc_rcc_classroom_ending_class_force_desc_for_classroom_no_
- level: business
  field: 上课时长
  rule: 上课未满3分钟不允许下课
  failure: checkIsTimeToEndLesson抛异常
- level: business
  field: cloudPlatform
  rule: VDI云平台不可用时需允许强制删除
  failure: rcdc_rcc_classroom_validate_force_ending_class_desc_for_plat
assertions:
  success:
  - scenario: 教室正在上课且时长满足要求
    expect: $.status==SUCCESS && $.content.classroomId 非空 && $.content.lessonTaskId 非空（Builder.success(ClassroomLessonBatchTaskDTO)）
  failure:
  - scenario: token非法
    trigger: token解密失败
    expect: $.status==ERROR && $.msgKey==rcdc_rcc_classroom_cef_token_check_failure
  - scenario: 教室无上课镜像
    trigger: getCurrentLessonImageByClassroomId返回null
    expect: $.status==ERROR && $.msgKey==rcdc_rcc_classroom_ending_class_fail_desc_for_classroom_image_not_in_class
  - scenario: VDI平台不可用且不允许强制删除
    trigger: validForForceDelete失败
    expect: $.status==ERROR && $.msgKey==rcdc_rcc_classroom_validate_force_ending_class_desc_for_platform_unavailable_cmr
cleanup: []
idempotency:
  level: data_level
  note: 重复下课由classroomLessonAPI.checkCanEndLesson状态校验拦截，非严格幂等
---
# POST /rcc/classroom/cmrcef/lesson/end

> CMR内嵌页面（CEF）下课：提交下课批处理任务，返回教室ID与批处理任务ID ｜ 无特殊权限 ｜ async

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/cmrcef/lesson/end<br>CMR内嵌页面（CEF）下课：提交下课批处理任务，返回教室ID与批处理任务ID<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(webRequest) 校验入参"]
        C2["Step2: @ClassroomCef拦截器校验token"]
        C3["Step3: webRequest.buildEndLessonDTO()：source=CM"]
        C4["Step4: lessonService.endLesson(dto,false)：校验教室存"]
        C5["Step5: 若VDI云平台不可用则走强制下课链路（endLessonWithoutSeat "]
        C6["Step6: classroomLessonAPI.prepareEndLesson 准备下课"]
        C1 --> C2
        C7["Step7: 返回ClassroomLessonBatchTaskDTO{classroomI"]
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
| URL | /rcc/classroom/cmrcef/lesson/end |
| Controller | RccClassroomCmrcefController |
| 方法名 | endLessonForCef |
| 权限注解 | 无 |
| 执行方式 | async |
| 业务含义 | CMR内嵌页面（CEF）下课：提交下课批处理任务，返回教室ID与批处理任务ID |

## 入参详情

### CefEndLessonWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull，教室ID | 要下课的教室 |
| token | String | 是 | @NotNull，AES加密TOKEN | 由@ClassroomCef拦截器校验 |
| closeTerminal | Boolean | 否 | @Nullable，默认false | 是否同时关闭终端 |

## 出参详情

| 返回类型 | DefaultWebResponse<ClassroomLessonBatchTaskDTO> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| classroomId | UUID | 教室ID |
| lessonTaskId | UUID | 下课批处理任务ID |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 批量处理器：LessonFactory创建的下课BatchTaskHandler（按CbbImageType分VDI/VOI等实现）

| 步骤 | 说明 |
|---|---|
| 1 | 检查云平台/资源可用性后批量执行各座位关机/回收桌面 |
| 2 | 通过批处理消息通知课堂进度 |

### 处理流程

1. Assert.notNull(webRequest) 校验入参
2. @ClassroomCef拦截器校验token
3. webRequest.buildEndLessonDTO()：source=CMR，closeTerminal默认false
4. lessonService.endLesson(dto,false)：校验教室存在与上课镜像、checkCanEndLesson、检查上课时长限制
5. 若VDI云平台不可用则走强制下课链路（endLessonWithoutSeat + notifyClassroomInfoChange）并抛业务异常
6. classroomLessonAPI.prepareEndLesson 准备下课，lessonFactory按镜像类型创建下课批处理任务
7. 返回ClassroomLessonBatchTaskDTO{classroomId,lessonTaskId}

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| auth | token | AES解密等于classroomId | rcdc_rcc_classroom_cef_token_check_failure |
| business | classroomId | 上课镜像必须存在 | rcdc_rcc_classroom_ending_class_fail_desc_for_classroom_image_not_in_class |
| business | classroomId | 教室信息必须存在 | rcdc_rcc_classroom_ending_class_fail_desc_for_no_classroom |
| business | seat | 无座位时直接强制下课 | rcdc_rcc_classroom_ending_class_force_desc_for_classroom_no_seat（返回成功消息） |
| business | 上课时长 | 上课未满3分钟不允许下课 | checkIsTimeToEndLesson抛异常 |
| business | cloudPlatform | VDI云平台不可用时需允许强制删除 | rcdc_rcc_classroom_validate_force_ending_class_desc_for_platform_unavailable_cmr / rcdc_rcc_classroom_force_ending_class_desc_for_platform_unavailable |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| token | user_input/from_query | 按业务构造 |
| closeTerminal | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教室正在上课且时长满足要求 | $.status==SUCCESS && $.content.classroomId 非空 && $.content.lessonTaskId 非空（Builder.success(ClassroomLessonBatchTaskDTO)） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| token非法 | token解密失败 | $.status==ERROR && $.msgKey==rcdc_rcc_classroom_cef_token_check_failure |
| 教室无上课镜像 | getCurrentLessonImageByClassroomId返回null | $.status==ERROR && $.msgKey==rcdc_rcc_classroom_ending_class_fail_desc_for_classroom_image_not_in_class |
| VDI平台不可用且不允许强制删除 | validForForceDelete失败 | $.status==ERROR && $.msgKey==rcdc_rcc_classroom_validate_force_ending_class_desc_for_platform_unavailable_cmr |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | medium |
| 说明 | 重复下课由classroomLessonAPI.checkCanEndLesson状态校验拦截，非严格幂等 |
