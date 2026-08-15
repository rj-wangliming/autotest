---
version: '2.0'
api:
  url: /rcc/classroom/lesson/start
  method: POST
  name: 按教室+镜像上课，先做教室权限与上课状态校验，通过后提交上课批处理任务
  controller: RccClassroomLessonController
  method_ref: startLesson
  permission: '@EnableAuthority'
  exec_mode: async_batch
  async: false
  description: 按教室+镜像上课，先做教室权限与上课状态校验，通过后提交上课批处理任务
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
- name: listImage
  api: POST /rcc/classroom/image/list
  purpose: 查询镜像ID；按镜像名精确过滤查询镜像（crId=${prev.listClassroom.output.classroomId}，searchKeyword=${param.student_image_name}），取 imageId
  extract:
    imageId: $.content.itemArr[0].id
  request:
    body:
      crId: ${prev.listClassroom.output.classroomId}
      searchKeyword: ${param.student_image_name}
      matchArr:
      - type: EXACT
        fieldName: imageName
        valueArr:
        - ${param.image_name}
        matchRule: EQ
request:
  dto: StartLessonWebRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 教室ID
      value: ${prev.listClassroom.output.classroomId}
    imageId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 上课使用的镜像模板ID
      value: ${prev.listImage.output.imageId}
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
      description: 提交的上课批处理任务ID
upstream:
- api: 内部调用:ClassroomAPI
  purpose: 按教室ID取教室基础信息（含terminalGroupId、classroomName）
- api: 内部调用:ClassroomLessonStatusAPI
  purpose: 上课并发锁：重复请求拦截、执行期加锁、finally释放
- api: 内部调用:PlatformImageTemplateMgmtAPI
  purpose: 按imageId取镜像类型
- api: 内部调用:ClassroomLessonAPI
  purpose: 准备上课数据（结束旧课、构建上课信息）
downstream:
- api: 内部调用:CmrClientAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: request
  field: classroomId/imageId
  rule: '@NotNull 非空'
  failure: webmvc 参数校验异常
- level: business
  field: classroomId
  rule: 教室必须存在
  failure: rcdc_rcc_classroom_starting_class_fail_desc_for_no_classroom
- level: business
  field: classroomId
  rule: 教室不能处于准备上课中
  failure: rcdc_rcc_classroom_starting_class_fail_desc_for_repeat_start
- level: business
  field: imageId
  rule: 已在课且镜像相同则不允许重复上课
  failure: rcdc_rcc_classroom_starting_class_fail_desc_for_the_same
- level: business
  field: terminalGroupId
  rule: 管理员需具备教室终端组数据权限
  failure: space_lesson_permission_denied
- level: business
  field: imageId
  rule: 镜像状态/类型需允许上课
  failure: rcdc_rcc_classroom_start_lesson_image_state_not_allowed / ..
assertions:
  success:
  - scenario: 权限通过且教室空闲
    expect: $.status==SUCCESS && $.content.taskId 非空（Builder.success(BatchTaskSubmitResult)）
  - scenario: 教室正在上课但镜像不同（切课）
    expect: $.status==SUCCESS && $.content.taskId 非空（自动先下课再提交上课任务）
  failure:
  - scenario: 无终端组权限
    trigger: 管理员不在全组权限且无对应终端组权限
    expect: $.status==ERROR && $.msgKey==space_lesson_permission_denied
  - scenario: 重复上课请求
    trigger: 教室已处于STARTING_CLASS或同镜像IN_CLASS
    expect: $.status==ERROR && $.msgKey==rcdc_rcc_classroom_starting_class_fail_desc_for_repeat_starting（系列）
  - scenario: 镜像非法
    trigger: imageId不存在/镜像隐藏/未分配
    expect: $.status==ERROR && $.msgKey==rcdc_rcc_classroom_start_lesson_image_state_not_allowed
cleanup:
- api: 无对应 HTTP 清理接口
  note: finally 释放上课执行锁为服务端内部动作，无 HTTP 清理接口
prereq_state:
  resource: classroom
  required_state: NONE_CLASS
  forbidden: [STARTING_CLASS, IN_CLASS]
  achieve_via: []

idempotency:
  level: data_level
  note: 通过 hasClassroomLessonMap 锁串行化；重复同镜像上课被拒绝，不同镜像视为切课（先下课再上课），非严格幂等
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
  - name: student_image_name
    desc: ''
    used_by: 见 setup/request
  - name: image_name
    desc: ''
    used_by: setup/request
---
# POST /rcc/classroom/lesson/start

> 按教室+镜像上课，先做教室权限与上课状态校验，通过后提交上课批处理任务 ｜ @EnableAuthority ｜ async_batch

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/lesson/start<br>按教室+镜像上课，先做教室权限与上课状态校验，通过后提交上课批处理任务<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert sessionContext/webRequest/builder"]
        C2["Step2: classroomAPI.getClassroomBasicInfo 取教室基础"]
        C3["Step3: permissionUtils 按 TERMINAL_GROUP 校验教室 te"]
        C4["Step4: classroomLessonStatusAPI.hasClassroomLes"]
        C5["Step5: addClassroomLessonMap 加执行锁"]
        C6["Step6: lessonService.startLesson：checkStartLess"]
        C1 --> C2
        C7["Step7: dealStartLesson：查镜像类型→checkBeforeStartLe"]
        C8["Step8: updateStartLessonStatisticsLessonTaskId "]
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
| URL | /rcc/classroom/lesson/start |
| Controller | RccClassroomLessonController |
| 方法名 | startLesson |
| 权限注解 | @EnableAuthority |
| 执行方式 | async_batch |
| 业务含义 | 按教室+镜像上课，先做教室权限与上课状态校验，通过后提交上课批处理任务 |

## 入参详情

### StartLessonWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull 非空 | 教室ID |
| imageId | UUID | 是 | @NotNull 非空 | 上课使用的镜像模板ID |

## 出参详情

| 返回类型 | DefaultWebResponse<BatchTaskSubmitResult> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| taskId | UUID | 提交的上课批处理任务ID |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 批量处理器：LessonFactory按镜像类型创建的批处理Handler（VDI/VOI上课Handler）

| 步骤 | 说明 |
|---|---|
| 1 | beginBatchTaskForStartLesson 逐座位启动桌面/下发开机指令，汇总成功与失败 |

### 处理流程

1. Assert sessionContext/webRequest/builder 非空
2. classroomAPI.getClassroomBasicInfo 取教室基础信息
3. permissionUtils 按 TERMINAL_GROUP 校验教室 terminalGroupId 权限，不通过返回 SPACE_LESSON_PERMISSION_DENIED
4. classroomLessonStatusAPI.hasClassroomLessonMap 防重检查，重复抛异常并记录 RCDC_RCC_CLASSROOM_STARTING_CLASS_FAIL_DESC 审计
5. addClassroomLessonMap 加执行锁
6. lessonService.startLesson：checkStartLessonStatus(needCheckInLesson=true)（无教室/重复启动中/同镜像已上课均拒绝）
7. dealStartLesson：查镜像类型→checkBeforeStartLesson→endCurrentLesson(若在课先下课并等待结束)→prepareStartLesson→beginBatchTaskForStartLesson
8. updateStartLessonStatisticsLessonTaskId 回写任务ID；finally removeClassroomLessonMap 释放锁

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | classroomId/imageId | @NotNull 非空 | webmvc 参数校验异常 |
| business | classroomId | 教室必须存在 | rcdc_rcc_classroom_starting_class_fail_desc_for_no_classroom |
| business | classroomId | 教室不能处于准备上课中 | rcdc_rcc_classroom_starting_class_fail_desc_for_repeat_starting |
| business | imageId | 已在课且镜像相同则不允许重复上课 | rcdc_rcc_classroom_starting_class_fail_desc_for_the_same |
| business | terminalGroupId | 管理员需具备教室终端组数据权限 | space_lesson_permission_denied |
| business | imageId | 镜像状态/类型需允许上课 | rcdc_rcc_classroom_start_lesson_image_state_not_allowed / ..._for_no_image 等 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| imageId | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

> ⚠️ 断言以 HTTP 响应为准（status + msgKey / BatchTaskSubmitResult），非服务端审计日志。

### 成功场景

| 场景 | 断言点 |
|---|---|
| 权限通过且教室空闲 | $.status==SUCCESS && $.content.taskId 非空（Builder.success(BatchTaskSubmitResult)） |
| 教室正在上课但镜像不同（切课） | $.status==SUCCESS && $.content.taskId 非空（自动先下课再提交上课任务） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 无终端组权限 | 管理员不在全组权限且无对应终端组权限 | $.status==ERROR && $.msgKey==space_lesson_permission_denied |
| 重复上课请求 | 教室已处于STARTING_CLASS或同镜像IN_CLASS | $.status==ERROR && $.msgKey==rcdc_rcc_classroom_starting_class_fail_desc_for_repeat_starting（系列） |
| 镜像非法 | imageId不存在/镜像隐藏/未分配 | $.status==ERROR && $.msgKey==rcdc_rcc_classroom_start_lesson_image_state_not_allowed |
## 环境清理机制

| 接口 | 说明 |
|---|---|
| 无对应 HTTP 清理接口 | finally 释放上课执行锁为服务端内部动作，无 HTTP 清理接口 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | medium |
| 说明 | 通过 hasClassroomLessonMap 锁串行化；重复同镜像上课被拒绝，不同镜像视为切课（先下课再上课），非严格幂等 |
