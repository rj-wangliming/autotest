---
version: '2.0'
api:
  url: /spacetci/lessonImage/student/strategy/edit
  method: POST
  name: 学生机课程镜像更换课程策略，校验目标镜像为学生机后调用教室策略变更
  controller: TCILessonImageController
  method_ref: editStudentStrategy
  permission: '@EnableAuthority'
  exec_mode: sync
  async: false
  description: 学生机课程镜像更换课程策略，校验目标镜像为学生机后调用教室策略变更
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
- name: list_tci_strategy
  api: POST /space/strategy/tci/list
  extract:
    lessonStrategyId: $.content.itemArr[0].id
  purpose: 按策略名精确过滤（matchArr.fieldName=strategyName）
  request:
    body:
      matchArr:
      - fieldName: strategyName
        matchType: EQUAL
        value: ${param.strategy_name}
request:
  dto: TCIChangeLessonStrategyWebRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull，教室ID'
      description: 教室
    lessonImageId:
      type: UUID
      required: true
      constraint: '@NotNull，课程镜像ID'
      description: 要更换策略的学生机课程镜像
    lessonStrategyId:
      type: UUID
      required: true
      constraint: '@NotNull，课程策略ID'
      description: 新的课程策略
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
      description: spacetci_lessonimage_change_student_image_lessonstrategy_suc
upstream:
- api: POST /rcc/classroom/create
  purpose: 教室ID，来源为教室创建返回
- api: POST /spacetci/lessonImage/getLessonImageList
  purpose: 学生课程镜像ID，来源为课程镜像列表
- api: POST /space/strategy/tci/list
  purpose: TCI课程策略ID，来源为策略列表
downstream:
- api: 内部调用:classroomAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: business
  field: lessonImageId
  rule: 必须为学生机镜像
  failure: 62110030 SPACETCI_LESSONIMAGE_CANNOT_FIND_STUDENT_IMAGE
- level: business
  field: lessonStrategyId
  rule: 策略磁盘需与镜像匹配
  failure: 62110024/62110025/62110026
assertions:
  success:
  - scenario: 更换学生机镜像策略
    expect: $.status==SUCCESS（content 为空，msgKey==spacetci_lessonimage_change_student_image_lessonstrategy_success_log）
  failure:
  - scenario: 目标是教师机镜像
    trigger: assertTeacherImageFalse抛62110030
    expect: $.status==ERROR && $.msgKey==spacetci_lessonimage_change_student_image_lessonstrategy_fail_log
cleanup:
- api: POST /spacetci/lessonImage/student/strategy/edit
  note: 误操作时再次调用本接口换回原策略
idempotency:
  level: data_level
  note: 重复设置相同策略状态一致，可视为幂等；不同策略为覆盖写
params:
  required:
  - name: student_image_name
    desc: ''
    used_by: 见 setup/request
  - name: strategy_name
    desc: ''
    used_by: 见 setup/request
  - name: image_name
    desc: ''
    used_by: setup/request
---
# POST /spacetci/lessonImage/student/strategy/edit

> 学生机课程镜像更换课程策略，校验目标镜像为学生机后调用教室策略变更 ｜ @EnableAuthority ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create"]
        A2["POST /spacetci/lessonImage/getLessonImageList"]
        A3["POST /space/strategy/tci/list"]
    end
    B["POST /spacetci/lessonImage/student/strategy/edit<br>学生机课程镜像更换课程策略，校验目标镜像为学生机后调用教室策略变更<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    A2 -->|数据| B
    A3 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(webRequest) 校验入参"]
        C2["Step2: BeanUtils.copyProperties转TCIChangeLesson"]
        C3["Step3: 获取教室名/镜像名/策略名（失败时用ID兜底）"]
        C4["Step4: getByLessonImageId查询并assertTeacherImageF"]
        C5["Step5: classroomAPI.changeLessonStrategy 更换策略"]
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
| URL | /spacetci/lessonImage/student/strategy/edit |
| Controller | TCILessonImageController |
| 方法名 | editStudentStrategy |
| 权限注解 | @EnableAuthority |
| 执行方式 | sync |
| 业务含义 | 学生机课程镜像更换课程策略，校验目标镜像为学生机后调用教室策略变更 |

## 入参详情

### TCIChangeLessonStrategyWebRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull，教室ID | 教室 |
| lessonImageId | UUID | 是 | @NotNull，课程镜像ID | 要更换策略的学生机课程镜像 |
| lessonStrategyId | UUID | 是 | @NotNull，课程策略ID | 新的课程策略 |

## 出参详情

| 返回类型 | DefaultWebResponse |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| msgKey | String | spacetci_lessonimage_change_student_image_lessonstrategy_success_log |

## 上游前置业务

### 前置1：POST /rcc/classroom/create

教室ID，来源为教室创建返回（由 field_map 契约映射）

### 前置2：POST /spacetci/lessonImage/getLessonImageList

学生课程镜像ID，来源为课程镜像列表（由 field_map 契约映射）

### 前置3：POST /space/strategy/tci/list

TCI课程策略ID，来源为策略列表（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull(webRequest) 校验入参
2. BeanUtils.copyProperties转TCIChangeLessonStrategyDTO
3. 获取教室名/镜像名/策略名（失败时用ID兜底）
4. getByLessonImageId查询并assertTeacherImageFalse：教师机镜像抛62110030
5. classroomAPI.changeLessonStrategy 更换策略
6. 记录审计日志返回成功

## 下游消费方

### 消费1：POST /spacetci/lessonImage/student/strategy/edit

镜像更换后的策略ID（由 field_map 契约映射）

> 📖 错误码/状态码对照表见 **code_map_all.md**（工程级全量）与 **error_code_map_tci_strategy.md**（TCI 接口级，含触发条件）。

## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| business | lessonImageId | 必须为学生机镜像 | 62110030 SPACETCI_LESSONIMAGE_CANNOT_FIND_STUDENT_IMAGE |
| business | lessonStrategyId | 策略磁盘需与镜像匹配 | 62110024/62110025/62110026 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| lessonImageId | user_input/from_query | 按业务构造 |
| lessonStrategyId | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 更换学生机镜像策略 | $.status==SUCCESS（content 为空，msgKey==spacetci_lessonimage_change_student_image_lessonstrategy_success_log） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 目标是教师机镜像 | assertTeacherImageFalse抛62110030 | $.status==ERROR && $.msgKey==spacetci_lessonimage_change_student_image_lessonstrategy_fail_log |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| POST /spacetci/lessonImage/student/strategy/edit | 误操作时再次调用本接口换回原策略 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | medium |
| 说明 | 重复设置相同策略状态一致，可视为幂等；不同策略为覆盖写 |
