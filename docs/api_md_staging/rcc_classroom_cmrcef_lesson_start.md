---
version: '2.0'
api:
  url: /rcc/classroom/cmrcef/lesson/start
  method: POST
  name: CMR内嵌页面（CEF）上课：加教室上课互斥锁、校验镜像类型后启动上课批处理任务
  controller: RccClassroomCmrcefController
  method_ref: startLessonForCef
  permission: 无
  exec_mode: async
  async: false
  description: CMR内嵌页面（CEF）上课：加教室上课互斥锁、校验镜像类型后启动上课批处理任务
setup:
- name: up_1
  api: 内部调用:classroomLessonStatusAPI
  method: POST
  produces: void
  purpose: （内部调用）
- name: up_3
  api: 内部调用:lessonService
  method: POST
  produces: BatchTaskSubmitResult
  purpose: （内部调用）
request:
  dto: CefStartLessonWebRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull，教室ID'
      description: 要上课的教室
      value: ${prev.query_classroom.output.classroomId}
    token:
      type: String
      required: true
      constraint: '@NotNull，AES加密TOKEN'
      description: 由@ClassroomCef拦截器校验（CMR 专用加密 TOKEN，需测试环境提供/注入）
      generated_by: true
    imageId:
      type: UUID
      required: true
      constraint: '@NotNull，镜像ID'
      description: 上课使用的镜像
      value: ${prev.get_image.output.plusImageId}
    macArr:
      type: String[]
      required: false
      constraint: '@Nullable，终端mac数组'
      description: 指定上课的终端MAC列表
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
      description: 上课批处理任务ID
polling:
  api: common_get_msgct_detail_info
  # 公共轮询接口：POST /rco/msgct/msg/detail（消息中心），完整文档见 common_get_msgct_detail_info.md
  method: POST
  params:
    msgrelationid: ${content.lessonTaskId}
  interval_ms: 2000
  timeout_ms: 120000
  terminal_states:
    success:
    - SUCCESS
    - PARTIAL_SUCCESS
    failure:
    - FAILURE

upstream:
- api: 内部调用:classroomLessonStatusAPI
  purpose: 校验教室是否有其他上课操作进行中
- api: 内部调用:lessonService
  purpose: 执行上课校验与批处理启动
downstream:
- api: 内部调用:classroomLessonAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: auth
  field: token
  rule: AES解密等于classroomId
  failure: rcdc_rcc_classroom_cef_token_check_failure
- level: concurrency
  field: classroomId
  rule: 同一教室不允许并发上课
  failure: hasClassroomLessonMap抛异常
- level: business
  field: classroomId
  rule: 教室必须存在
  failure: rcdc_rcc_classroom_starting_class_fail_desc_for_no_classroom
- level: business
  field: classroomId
  rule: 准备上课中不允许重复上课
  failure: rcdc_rcc_classroom_starting_class_fail_desc_for_repeat_start
- level: business
  field: imageId
  rule: 已上课中且镜像相同不允许重复上课
  failure: rcdc_rcc_classroom_starting_class_fail_desc_for_the_same
assertions:
  success:
  - scenario: 教室空闲且镜像合法
    expect: $.status==SUCCESS && $.content.classroomId 非空 && $.content.lessonTaskId 非空（Builder.success(ClassroomLessonBatchTaskDTO)）
  failure:
  - scenario: token非法
    trigger: token解密失败
    expect: $.status==ERROR && $.msgKey==rcdc_rcc_classroom_cef_token_check_failure
  - scenario: 教室正在准备上课
    trigger: 重复点击上课
    expect: $.status==ERROR && $.msgKey==rcdc_rcc_classroom_starting_class_fail_desc_for_repeat_starting
  - scenario: 正在上课中且重复选择同一镜像
    trigger: 再点同一镜像上课
    expect: $.status==ERROR && $.msgKey==rcdc_rcc_classroom_starting_class_fail_desc_for_the_same
  - scenario: 上课过程中异常
    trigger: lessonService.startLesson抛异常
    expect: $.status==ERROR（异常向上抛出，无固定 msgKey）；finally 释放教室锁
cleanup: []
prereq_state:
  resource: classroom
  required_state: NONE_CLASS
  forbidden: [STARTING_CLASS, IN_CLASS]
  achieve_via: []

idempotency:
  level: data_level
  note: addClassroomLessonMap互斥防止并发，但同镜像重复上课被状态校验拦截；结果不保证幂等
---
# POST /rcc/classroom/cmrcef/lesson/start

> CMR内嵌页面（CEF）上课：加教室上课互斥锁、校验镜像类型后启动上课批处理任务 ｜ 无特殊权限 ｜ async

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/cmrcef/lesson/start<br>CMR内嵌页面（CEF）上课：加教室上课互斥锁、校验镜像类型后启动上课批处理任务<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(webRequest) 校验入参"]
        C2["Step2: @ClassroomCef拦截器校验token"]
        C3["Step3: webRequest.buildStartLessonDTO()：source="]
        C4["Step4: hasClassroomLessonMap校验无并发上课，失败直接抛异常"]
        C5["Step5: addClassroomLessonMap加互斥锁（finally中remove"]
        C6["Step6: lessonService.startLesson：校验教室存在/重复上课状态，"]
        C1 --> C2
        C7["Step7: lessonFactory按镜像类型启动上课批处理，更新上课任务ID"]
        C8["Step8: 返回ClassroomLessonBatchTaskDTO{classroomI"]
        C6 --> C7
        C7 --> C8
        C2 --> C3
        C3 --> C4
        C4 --> C5
        C5 --> C6
    end
    B --> C1
    subgraph 下游消费方
        D1["cmrcef/lesson/progress"]
    end
    B -->|数据| D1
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rcc/classroom/cmrcef/lesson/start |
| Controller | RccClassroomCmrcefController |
| 方法名 | startLessonForCef |
| 权限注解 | 无 |
| 执行方式 | async |
| 业务含义 | CMR内嵌页面（CEF）上课：加教室上课互斥锁、校验镜像类型后启动上课批处理任务 |

## 入参详情

### CefStartLessonWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull，教室ID | 要上课的教室 |
| token | String | 是 | @NotNull，AES加密TOKEN | 由@ClassroomCef拦截器校验 |
| imageId | UUID | 是 | @NotNull，镜像ID | 上课使用的镜像 |
| macArr | String[] | 否 | @Nullable，终端mac数组 | 指定上课的终端MAC列表 |

## 出参详情

| 返回类型 | DefaultWebResponse<ClassroomLessonBatchTaskDTO> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| classroomId | UUID | 教室ID |
| lessonTaskId | UUID | 上课批处理任务ID |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 批量处理器：LessonFactory创建的上课BatchTaskHandler（按CbbImageType分VDI/VOI等实现）

| 步骤 | 说明 |
|---|---|
| 1 | checkBeforeStartLesson校验镜像状态与策略 |
| 2 | 批量对座位下发开机/启动云桌面指令 |
| 3 | 批处理消息实时更新进度 |

### 处理流程

1. Assert.notNull(webRequest) 校验入参
2. @ClassroomCef拦截器校验token
3. webRequest.buildStartLessonDTO()：source=CMR，含classroomId/imageId/macArr
4. hasClassroomLessonMap校验无并发上课，失败直接抛异常
5. addClassroomLessonMap加互斥锁（finally中removeClassroomLessonMap释放）
6. lessonService.startLesson：校验教室存在/重复上课状态，若上课中则先下课并等待完成（切课），再prepareStartLesson
7. lessonFactory按镜像类型启动上课批处理，更新上课任务ID
8. 返回ClassroomLessonBatchTaskDTO{classroomId,lessonTaskId}

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| auth | token | AES解密等于classroomId | rcdc_rcc_classroom_cef_token_check_failure |
| concurrency | classroomId | 同一教室不允许并发上课 | hasClassroomLessonMap抛异常 |
| business | classroomId | 教室必须存在 | rcdc_rcc_classroom_starting_class_fail_desc_for_no_classroom |
| business | classroomId | 准备上课中不允许重复上课 | rcdc_rcc_classroom_starting_class_fail_desc_for_repeat_starting |
| business | imageId | 已上课中且镜像相同不允许重复上课 | rcdc_rcc_classroom_starting_class_fail_desc_for_the_same |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| token | user_input/from_query | 按业务构造 |
| imageId | user_input/from_query | 按业务构造 |
| macArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教室空闲且镜像合法 | $.status==SUCCESS && $.content.classroomId 非空 && $.content.lessonTaskId 非空（Builder.success(ClassroomLessonBatchTaskDTO)） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| token非法 | token解密失败 | $.status==ERROR && $.msgKey==rcdc_rcc_classroom_cef_token_check_failure |
| 教室正在准备上课 | 重复点击上课 | $.status==ERROR && $.msgKey==rcdc_rcc_classroom_starting_class_fail_desc_for_repeat_starting |
| 正在上课中且重复选择同一镜像 | 再点同一镜像上课 | $.status==ERROR && $.msgKey==rcdc_rcc_classroom_starting_class_fail_desc_for_the_same |
| 上课过程中异常 | lessonService.startLesson抛异常 | $.status==ERROR（异常向上抛出，无固定 msgKey）；finally 释放教室锁 |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | medium |
| 说明 | addClassroomLessonMap互斥防止并发，但同镜像重复上课被状态校验拦截；结果不保证幂等 |
