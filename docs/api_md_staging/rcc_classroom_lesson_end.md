---
version: '2.0'
api:
  url: /rcc/classroom/lesson/end
  method: POST
  name: 下课：校验当前上课状态与可下课条件（含3分钟保护、云平台可用性），提交下课批处理任务
  controller: RccClassroomLessonController
  method_ref: endLesson
  permission: '@EnableAuthority'
  exec_mode: async_batch
  async: false
  description: 下课：校验当前上课状态与可下课条件（含3分钟保护、云平台可用性），提交下课批处理任务
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: createClassroom
  api: POST /rcc/classroom/create
  purpose: 创建教室
  extract:
    classroomName: ${param.classroom_name}
  request:
    body:
      classroomName: ${param.classroom_name}
  idempotent: recreate
  delete_api: /rcc/classroom/delete
  delete_param: classroomId
- name: listClassroom
  api: POST /rcc/classroom/list
  purpose: 查询教室ID；按教室名精确过滤分页查询教室（matchArr.fieldName=classroomName），取 classroomId
  extract:
    classroomId: $.content.itemArr[0].classroomId
  request:
    body:
      matchArr:
      - type: EXACT
        fieldName: classroomName
        valueArr:
        - ${param.classroom_name}
        matchRule: EQ
- name: startLesson
  api: POST /rcc/classroom/lesson/start
  purpose: 先上课再下课
request:
  dto: EndLessonWebRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 教室ID
      value: ${prev.listClassroom.output.classroomId}
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    taskId:
      type: UUID
      description: 下课批处理任务ID
polling:
  api: common_get_msgct_detail_info
  method: POST
  params:
    msgrelationid: ${content.taskId}
  interval_ms: 2000
  timeout_ms: 120000
  terminal_states:
    success: [SUCCESS]
    failure: [FAILURE, PARTIAL_SUCCESS]
upstream:
- api: 内部调用:ClassroomAPI
  purpose: 取教室信息与权限校验
- api: 内部调用:ClassroomLessonAPI
  purpose: 取当前上课镜像ID，无则拒绝下课
- api: 内部调用:SeatAPI
  purpose: 校验座位下课条件，无座位走强制下课
downstream:
- api: 内部调用:CmrClientAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: request
  field: classroomId
  rule: '@NotNull 非空'
  failure: webmvc 参数校验异常
- level: business
  field: classroomId
  rule: 教室必须处于上课状态且有当前镜像
  failure: rcdc_rcc_classroom_ending_class_fail_desc_for_classroom_imag
- level: business
  field: classroomId
  rule: 上课时长不足3分钟不允许下课
  failure: checkIsTimeToEndLesson 抛出异常
- level: business
  field: classroomId
  rule: 教室无座位时强制下课
  failure: rcdc_rcc_classroom_ending_class_force_desc_for_classroom_no_
- level: business
  field: platformId
  rule: VDI云平台不可用时需允许强制删除
  failure: rcdc_rcc_classroom_validate_force_ending_class_desc_for_plat
assertions:
  success:
  - scenario: 正常在课且座位存在
    expect: $.status==SUCCESS && $.content.taskId 非空（Builder.success(BatchTaskSubmitResult)）
  failure:
  - scenario: 未在上课
    trigger: 教室无当前上课镜像
    expect: $.status==ERROR && $.msgKey==rcdc_rcc_classroom_ending_class_fail_desc_for_classroom_image_not_in_class
  - scenario: 无座位教室
    trigger: getSeatInfoList 为空
    expect: $.status==ERROR && $.msgKey==rcdc_rcc_classroom_ending_class_force_desc_for_classroom_no_seat（本地直接下课 endLessonWithoutSeat）
  - scenario: 云平台不可用且禁止强制删除
    trigger: validForForceDelete 失败
    expect: $.status==ERROR && $.msgKey==rcdc_rcc_classroom_validate_force_ending_class_desc_for_platform_unavailable_server
  - scenario: 上课时间过短
    trigger: IN_CLASS 且 source 为 WEB 且不足3分钟
    expect: $.status==ERROR && $.msgKey==rcdc_classroom_end_lessoon_limit_time
cleanup: []
prereq_state:
  resource: classroom
  required_state: IN_CLASS
  achieve_via: []

idempotency:
  level: data_level
  note: 重复下课因当前镜像不存在或不在上课状态被拒绝；正常路径为一次性操作
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/lesson/end

> 下课：校验当前上课状态与可下课条件（含3分钟保护、云平台可用性），提交下课批处理任务 ｜ @EnableAuthority ｜ async_batch

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/lesson/end<br>下课：校验当前上课状态与可下课条件（含3分钟保护、云平台可用性），提交下课批处理<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert 参数非空"]
        C2["Step2: 查教室信息，权限校验（SPACE_LESSON_PERMISSION_DENIE"]
        C3["Step3: 组装 EndLessonDTO{classroomId, source=WEB,"]
        C4["Step4: lessonService.endLesson：getImageIdByClas"]
        C5["Step5: 查镜像类型 → checkBeforeEndLesson"]
        C6["Step6: checkEndLesson：checkCanEndLesson + seatA"]
        C1 --> C2
        C7["Step7: forceEndLessonIfPlatformUnavailable：VDI云"]
        C8["Step8: prepareEndLesson → beginBatchTaskForEndL"]
        C6 --> C7
        C7 --> C8
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
| URL | /rcc/classroom/lesson/end |
| Controller | RccClassroomLessonController |
| 方法名 | endLesson |
| 权限注解 | @EnableAuthority |
| 执行方式 | async_batch |
| 业务含义 | 下课：校验当前上课状态与可下课条件（含3分钟保护、云平台可用性），提交下课批处理任务 |

## 入参详情

### EndLessonWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull 非空 | 教室ID |

## 出参详情

| 返回类型 | DefaultWebResponse<BatchTaskSubmitResult> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| taskId | UUID | 下课批处理任务ID |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 批量处理器：LessonFactory按镜像类型创建的下课批处理Handler

| 步骤 | 说明 |
|---|---|
| 1 | 逐座位关闭桌面/终端，汇总成功与失败 |

### 处理流程

1. Assert 参数非空
2. 查教室信息，权限校验（SPACE_LESSON_PERMISSION_DENIED）
3. 组装 EndLessonDTO{classroomId, source=WEB, closeTerminal=false}
4. lessonService.endLesson：getImageIdByClassroomId 无当前镜像抛 RCDC_RCC_CLASSROOM_ENDING_CLASS_FAIL_DESC_FOR_CLASSROOM_IMAGE_NOT_IN_CLASS
5. 查镜像类型 → checkBeforeEndLesson
6. checkEndLesson：checkCanEndLesson + seatAPI.checkCanEndLesson + 无座位强制下课 + 3分钟保护校验
7. forceEndLessonIfPlatformUnavailable：VDI云平台不可用时校验 validForForceDelete 后本地强制下课并抛 RCDC_RCC_CLASSROOM_FORCE_ENDING_CLASS_DESC_FOR_PLATFORM_UNAVAILABLE
8. prepareEndLesson → beginBatchTaskForEndLesson 提交下课批处理；updateEndLessonStatisticsLessonTaskId

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | classroomId | @NotNull 非空 | webmvc 参数校验异常 |
| business | classroomId | 教室必须处于上课状态且有当前镜像 | rcdc_rcc_classroom_ending_class_fail_desc_for_classroom_image_not_in_class |
| business | classroomId | 上课时长不足3分钟不允许下课 | checkIsTimeToEndLesson 抛出异常 |
| business | classroomId | 教室无座位时强制下课 | rcdc_rcc_classroom_ending_class_force_desc_for_classroom_no_seat |
| business | platformId | VDI云平台不可用时需允许强制删除 | rcdc_rcc_classroom_validate_force_ending_class_desc_for_platform_unavailable_* |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 正常在课且座位存在 | $.status==SUCCESS && $.content.taskId 非空（Builder.success(BatchTaskSubmitResult)） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 未在上课 | 教室无当前上课镜像 | $.status==ERROR && $.msgKey==rcdc_rcc_classroom_ending_class_fail_desc_for_classroom_image_not_in_class |
| 无座位教室 | getSeatInfoList 为空 | $.status==ERROR && $.msgKey==rcdc_rcc_classroom_ending_class_force_desc_for_classroom_no_seat（本地直接下课 endLessonWithoutSeat） |
| 云平台不可用且禁止强制删除 | validForForceDelete 失败 | $.status==ERROR && $.msgKey==rcdc_rcc_classroom_validate_force_ending_class_desc_for_platform_unavailable_server |
| 上课时间过短 | IN_CLASS 且 source 为 WEB 且不足3分钟 | $.status==ERROR && $.msgKey==rcdc_classroom_end_lessoon_limit_time |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | medium |
| 说明 | 重复下课因当前镜像不存在或不在上课状态被拒绝；正常路径为一次性操作 |
