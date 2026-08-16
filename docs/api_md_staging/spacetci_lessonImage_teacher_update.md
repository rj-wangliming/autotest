---
version: '2.0'
api:
  url: /spacetci/lessonImage/teacher/update
  method: POST
  name: 更新教师机课程镜像并同步推送镜像列表到教师机
  controller: TCILessonImageController
  method_ref: updateTeacherLessonImage
  permission: '@EnableAuthority'
  exec_mode: sync
  async: false
  description: 更新教师机课程镜像并同步推送镜像列表到教师机
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
      searchKeyword: ${param.teacher_image_name}
      matchArr:
      - type: EXACT
        fieldName: imageName
        valueArr:
        - ${param.teacher_image_name}
        matchRule: EQ
request:
  dto: IdWebRequest
  body:
    id:
      type: UUID
      required: true
      constraint: '@NotNull，课程镜像ID'
      description: 要更新的课程镜像ID
      value: ${prev.list_lesson_image.output.lessonImageId}
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
      description: spacetci_lessonimage_update_teacher_image_success_log
upstream:
- api: POST /spacetci/lessonImage/getLessonImageList
  produces: $.content.itemArr[*].id
  purpose: 教师课程镜像ID（IdWebRequest=lessonImageId），来源为课程镜像列表
downstream:
- api: 内部调用:classroomTeacherAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: data
  field: admin
  rule: 需拥有镜像数据权限
  failure: spacetci_lessonimage_permission_denied
- level: business
  field: id
  rule: 必须为教师机镜像
  failure: '62110029'
assertions:
  success:
  - scenario: 更新教师机镜像
    expect: $.status==SUCCESS（content 为空，msgKey==spacetci_lessonimage_update_teacher_image_success_log）
  failure:
  - scenario: 操作学生机镜像
    trigger: assertTeacherImageTrue抛62110029
    expect: $.status==ERROR && $.msgKey==spacetci_lessonimage_update_teacher_image_fail_log
cleanup: []
idempotency:
  level: data_level
  note: 重复更新状态一致，但每次触发教师机推送
params:
  required:
  - name: student_image_name
    desc: ''
    used_by: 见 setup/request
  - name: image_name
  - name: teacher_image_name
    desc: ''
    used_by: setup/request
---
# POST /spacetci/lessonImage/teacher/update

> 更新教师机课程镜像并同步推送镜像列表到教师机 ｜ @EnableAuthority ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /spacetci/lessonImage/getLessonImageList"]
    end
    B["POST /spacetci/lessonImage/teacher/update<br>更新教师机课程镜像并同步推送镜像列表到教师机<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(webRequest/sessionContext"]
        C2["Step2: getByLessonImageId查询，checkPermission校验权限"]
        C3["Step3: assertTeacherImageTrue：学生机镜像抛62110029"]
        C4["Step4: classroomAPI.updateLessonImage(classroom"]
        C5["Step5: classroomTeacherAPI.pushClassroomImageTo"]
        C6["Step6: 记录审计日志返回成功"]
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
| URL | /spacetci/lessonImage/teacher/update |
| Controller | TCILessonImageController |
| 方法名 | updateTeacherLessonImage |
| 权限注解 | @EnableAuthority |
| 执行方式 | sync |
| 业务含义 | 更新教师机课程镜像并同步推送镜像列表到教师机 |

## 入参详情

### IdWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| id | UUID | 是 | @NotNull，课程镜像ID | 要更新的课程镜像ID |

## 出参详情

| 返回类型 | DefaultWebResponse |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| msgKey | String | spacetci_lessonimage_update_teacher_image_success_log |

## 上游前置业务

### 前置1：POST /spacetci/lessonImage/getLessonImageList

教师课程镜像ID（IdWebRequest=lessonImageId），来源为课程镜像列表（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull(webRequest/sessionContext) 校验入参
2. getByLessonImageId查询，checkPermission校验权限
3. assertTeacherImageTrue：学生机镜像抛62110029
4. classroomAPI.updateLessonImage(classroomId,id) 更新镜像
5. classroomTeacherAPI.pushClassroomImageToTeacher同步推送
6. 记录审计日志返回成功

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）

> 📖 错误码/状态码对照表见 **code_map_all.md**（工程级全量）与 **error_code_map_tci_strategy.md**（TCI 接口级，含触发条件）。

## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| data | admin | 需拥有镜像数据权限 | spacetci_lessonimage_permission_denied |
| business | id | 必须为教师机镜像 | 62110029 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| id | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 更新教师机镜像 | $.status==SUCCESS（content 为空，msgKey==spacetci_lessonimage_update_teacher_image_success_log） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 操作学生机镜像 | assertTeacherImageTrue抛62110029 | $.status==ERROR && $.msgKey==spacetci_lessonimage_update_teacher_image_fail_log |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | medium |
| 说明 | 重复更新状态一致，但每次触发教师机推送 |
