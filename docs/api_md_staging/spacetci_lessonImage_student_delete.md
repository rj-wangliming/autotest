---
version: '2.0'
api:
  url: /spacetci/lessonImage/student/delete
  method: POST
  name: 删除学生机课程镜像：删除记录后若为最后一个镜像则批量删除座位云桌面，否则推送新镜像列表到座位
  controller: TCILessonImageController
  method_ref: deleteStudentLessonImage
  permission: '@EnableAuthority'
  exec_mode: async
  async: false
  description: 删除学生机课程镜像：删除记录后若为最后一个镜像则批量删除座位云桌面，否则推送新镜像列表到座位
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: list_lesson_image
  api: POST /spacetci/lessonImage/getLessonImageList
  extract:
    lessonImageId: $.content.itemArr[0].id
  purpose: 按镜像名精确过滤（searchKeyword + matchArr.fieldName=imageName）
  request:
    body:
      searchKeyword: ${param.student_image_name}
      matchArr:
      - fieldName: imageName
        matchType: EQUAL
        value: ${param.image_name}
request:
  dto: IdWebRequest
  body:
    id:
      type: UUID
      required: true
      constraint: '@NotNull，课程镜像ID'
      description: 要删除的课程镜像记录ID
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    msgKey:
      type: String
      description: spacetci_lessonimage_delete_student_image_success_log（座位为空/非
    taskId:
      type: UUID
      description: 最后镜像时返回删除云桌面批处理任务ID
upstream:
- api: POST /spacetci/lessonImage/getLessonImageList
  produces: $.content.itemArr[*].id
  purpose: 学生课程镜像ID（IdWebRequest=lessonImageId），来源为课程镜像列表
downstream:
- api: 内部调用:seatAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: data
  field: admin
  rule: 需拥有镜像数据权限
  failure: spacetci_lessonimage_permission_denied
- level: concurrency
  field: classroomId
  rule: 同一教室操作互斥
  failure: spacetci_lessonimage_operate_running
- level: business
  field: id
  rule: 必须为学生机镜像
  failure: 62110030 SPACETCI_LESSONIMAGE_CANNOT_FIND_STUDENT_IMAGE
assertions:
  success:
  - scenario: 教室无座位
    expect: $.status==SUCCESS（content 为空，msgKey==spacetci_lessonimage_delete_student_image_success_log）
  - scenario: 删除最后一个学生镜像
    expect: $.status==SUCCESS && $.content.taskId 非空（删除云桌面批处理任务）；轮询 content.taskId 至终态 batchTaskItemStatus∈["SUCCESS"]
  - scenario: 删除非最后镜像
    expect: $.status==SUCCESS（content 为空，msgKey==spacetci_lessonimage_delete_student_image_success_log）
  failure:
  - scenario: 无镜像权限
    trigger: checkPermission失败
    expect: $.status==ERROR && $.msgKey==spacetci_lessonimage_permission_denied
  - scenario: 教室操作进行中
    trigger: tryLock失败
    expect: $.status==ERROR && $.msgKey==spacetci_lessonimage_operate_running
  - scenario: 目标是教师机镜像
    trigger: assertTeacherImageFalse抛62110030
    expect: $.status==ERROR && $.msgKey==62110030
cleanup: []
idempotency:
  level: data_level
  note: 重复删除已删除记录会抛异常；删除操作本身非幂等
params:
  required:
  - name: student_image_name
    desc: ''
    used_by: 见 setup/request
  - name: image_name
    desc: ''
    used_by: setup/request
---
# POST /spacetci/lessonImage/student/delete

> 删除学生机课程镜像：删除记录后若为最后一个镜像则批量删除座位云桌面，否则推送新镜像列表到座位 ｜ @EnableAuthority ｜ async

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /spacetci/lessonImage/getLessonImageList"]
    end
    B["POST /spacetci/lessonImage/student/delete<br>删除学生机课程镜像：删除记录后若为最后一个镜像则批量删除座位云桌面，否则推送新镜<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(webRequest/sessionContext"]
        C2["Step2: getByLessonImageId查询课程镜像，checkPermission"]
        C3["Step3: getLock(classroomId).tryLock()，失败返回space"]
        C4["Step4: assertTeacherImageFalse：教师机镜像抛62110030"]
        C5["Step5: classroomAPI.deleteLessonImage删除记录"]
        C6["Step6: 座位为空直接返回成功；isLastImage为true→TCIDeleteSea"]
        C1 --> C2
        C7["Step7: 记录审计日志返回"]
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
| URL | /spacetci/lessonImage/student/delete |
| Controller | TCILessonImageController |
| 方法名 | deleteStudentLessonImage |
| 权限注解 | @EnableAuthority |
| 执行方式 | async |
| 业务含义 | 删除学生机课程镜像：删除记录后若为最后一个镜像则批量删除座位云桌面，否则推送新镜像列表到座位 |

## 入参详情

### IdWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| id | UUID | 是 | @NotNull，课程镜像ID | 要删除的课程镜像记录ID |

## 出参详情

| 返回类型 | DefaultWebResponse（成功消息key或BatchTaskSubmitResult） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| msgKey | String | spacetci_lessonimage_delete_student_image_success_log（座位为空/非最后镜像） |
| taskId | UUID | 最后镜像时返回删除云桌面批处理任务ID |

## 上游前置业务

### 前置1：POST /spacetci/lessonImage/getLessonImageList

学生课程镜像ID（IdWebRequest=lessonImageId），来源为课程镜像列表（由 field_map 契约映射）
## 内部处理流程

### 批量处理器：TCIDeleteSeatDesktopBatchTaskHandler(AbstractBatchTaskHandler) 或 PushImageListBatchTaskHandler

| 步骤 | 说明 |
|---|---|
| 1 | TCIDeleteSeatDesktopBatchTaskHandler.processItem：seatAPI.deleteTCIDesktop(dto,seatId)逐座位删除云桌面，失败返回FAILURE |
| 2 | PushImageListBatchTaskHandler.processItem：seatAPI.pushClassroomImageList2Seat(seatId)刷新座位镜像列表 |
| 3 | onFinish：seatAPI.refreshDeskInfo(classroomId)；全成功SUCCESS、全失败FAILURE、部分成功PARTIAL_SUCCESS |

### 处理流程

1. Assert.notNull(webRequest/sessionContext/builder) 校验入参
2. getByLessonImageId查询课程镜像，checkPermission校验镜像权限，失败返回spacetci_lessonimage_permission_denied
3. getLock(classroomId).tryLock()，失败返回spacetci_lessonimage_operate_running
4. assertTeacherImageFalse：教师机镜像抛62110030
5. classroomAPI.deleteLessonImage删除记录
6. 座位为空直接返回成功；isLastImage为true→TCIDeleteSeatDesktopBatchTaskHandler批量删除座位云桌面；否则推送镜像列表
7. 记录审计日志返回

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）

> 📖 错误码/状态码对照表见 **code_map_all.md**（工程级全量）与 **error_code_map_tci_strategy.md**（TCI 接口级，含触发条件）。

## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| data | admin | 需拥有镜像数据权限 | spacetci_lessonimage_permission_denied |
| concurrency | classroomId | 同一教室操作互斥 | spacetci_lessonimage_operate_running |
| business | id | 必须为学生机镜像 | 62110030 SPACETCI_LESSONIMAGE_CANNOT_FIND_STUDENT_IMAGE |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| id | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教室无座位 | $.status==SUCCESS（content 为空，msgKey==spacetci_lessonimage_delete_student_image_success_log） |
| 删除最后一个学生镜像 | $.status==SUCCESS && $.content.taskId 非空（删除云桌面批处理任务）；轮询 content.taskId 至终态 batchTaskItemStatus∈["SUCCESS"] |
| 删除非最后镜像 | $.status==SUCCESS（content 为空，msgKey==spacetci_lessonimage_delete_student_image_success_log） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 无镜像权限 | checkPermission失败 | $.status==ERROR && $.msgKey==spacetci_lessonimage_permission_denied |
| 教室操作进行中 | tryLock失败 | $.status==ERROR && $.msgKey==spacetci_lessonimage_operate_running |
| 目标是教师机镜像 | assertTeacherImageFalse抛62110030 | $.status==ERROR && $.msgKey==62110030 |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | low |
| 说明 | 重复删除已删除记录会抛异常；删除操作本身非幂等 |
