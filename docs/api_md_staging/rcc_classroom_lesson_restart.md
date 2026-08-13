---
version: '2.0'
api:
  url: /rcc/classroom/lesson/restart
  method: POST
  name: 重启课程（切换上课镜像），与上课流程一致但跳过同镜像重复校验，强制先结束当前课再上课
  controller: RccClassroomLessonController
  method_ref: restartLesson
  permission: '@EnableAuthority'
  exec_mode: async_batch
  async: false
  description: 重启课程（切换上课镜像），与上课流程一致但跳过同镜像重复校验，强制先结束当前课再上课
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
      - fieldName: classroomName
        matchType: EQUAL
        value: ${param.classroom_name}
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
      - fieldName: imageName
        matchType: EQUAL
        value: ${param.student_image_name}
request:
  dto: StartLessonWebRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 教室ID
    imageId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 新镜像模板ID
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
      description: 重启课程批处理任务ID
upstream:
- api: 内部调用:ClassroomAPI
  purpose: 取教室信息与权限校验
- api: 内部调用:ClassroomLessonStatusAPI
  purpose: 并发锁控制
- api: 内部调用:ClassroomLessonAPI
  purpose: 准备上课数据
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
  rule: 教室必须存在且未在准备中
  failure: rcdc_rcc_classroom_starting_class_fail_desc_for_no_classroom
- level: business
  field: terminalGroupId
  rule: 管理员需具备教室终端组数据权限
  failure: space_lesson_permission_denied
assertions:
  success:
  - scenario: 教室在课或空闲
    expect: $.status==SUCCESS && $.content.taskId 非空（Builder.success(BatchTaskSubmitResult)）
  failure:
  - scenario: 正在准备上课中重启
    trigger: classroomState==STARTING_CLASS
    expect: $.status==ERROR && $.msgKey==rcdc_rcc_classroom_starting_class_fail_desc_for_repeat_starting
  - scenario: 无权限
    trigger: 终端组权限不匹配
    expect: $.status==ERROR && $.msgKey==space_lesson_permission_denied
cleanup:
- api: 无对应 HTTP 清理接口
  note: finally 释放上课执行锁为服务端内部动作，无 HTTP 清理接口
idempotency:
  level: data_level
  note: 语义为切课：强制先下课再上课，重复提交会重复执行下课-上课全流程
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
  - name: student_image_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/lesson/restart

> 重启课程（切换上课镜像），与上课流程一致但跳过同镜像重复校验，强制先结束当前课再上课 ｜ @EnableAuthority ｜ async_batch

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/lesson/restart<br>重启课程（切换上课镜像），与上课流程一致但跳过同镜像重复校验，强制先结束当前课再<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert 参数非空"]
        C2["Step2: 查教室信息，权限校验（SPACE_LESSON_PERMISSION_DENIE"]
        C3["Step3: hasClassroomLessonMap 防重；addClassroomLes"]
        C4["Step4: lessonService.restartLesson：checkStartLe"]
        C5["Step5: dealStartLesson：endCurrentLesson 若在课必先下课"]
        C6["Step6: prepareStartLesson → beginBatchTaskForSt"]
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
| URL | /rcc/classroom/lesson/restart |
| Controller | RccClassroomLessonController |
| 方法名 | restartLesson |
| 权限注解 | @EnableAuthority |
| 执行方式 | async_batch |
| 业务含义 | 重启课程（切换上课镜像），与上课流程一致但跳过同镜像重复校验，强制先结束当前课再上课 |

## 入参详情

### StartLessonWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull 非空 | 教室ID |
| imageId | UUID | 是 | @NotNull 非空 | 新镜像模板ID |

## 出参详情

| 返回类型 | DefaultWebResponse<BatchTaskSubmitResult> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| taskId | UUID | 重启课程批处理任务ID |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 批量处理器：LessonFactory按镜像类型创建的上课批处理Handler

| 步骤 | 说明 |
|---|---|
| 1 | 逐座位启动桌面并汇总结果 |

### 处理流程

1. Assert 参数非空
2. 查教室信息，权限校验（SPACE_LESSON_PERMISSION_DENIED）
3. hasClassroomLessonMap 防重；addClassroomLessonMap 加锁
4. lessonService.restartLesson：checkStartLessonStatus(needCheckInLesson=false)（不校验同镜像重复）
5. dealStartLesson：endCurrentLesson 若在课必先下课并 waitEndLesson 等待下课任务完成
6. prepareStartLesson → beginBatchTaskForStartLesson 提交上课任务；finally 释放锁

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | classroomId/imageId | @NotNull 非空 | webmvc 参数校验异常 |
| business | classroomId | 教室必须存在且未在准备中 | rcdc_rcc_classroom_starting_class_fail_desc_for_no_classroom / _for_repeat_starting |
| business | terminalGroupId | 管理员需具备教室终端组数据权限 | space_lesson_permission_denied |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| imageId | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教室在课或空闲 | $.status==SUCCESS && $.content.taskId 非空（Builder.success(BatchTaskSubmitResult)） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 正在准备上课中重启 | classroomState==STARTING_CLASS | $.status==ERROR && $.msgKey==rcdc_rcc_classroom_starting_class_fail_desc_for_repeat_starting |
| 无权限 | 终端组权限不匹配 | $.status==ERROR && $.msgKey==space_lesson_permission_denied |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 无对应 HTTP 清理接口 | finally 释放上课执行锁为服务端内部动作，无 HTTP 清理接口 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | low |
| 说明 | 语义为切课：强制先下课再上课，重复提交会重复执行下课-上课全流程 |
