---
version: '2.0'
api:
  url: /rcc/classroom/select
  method: POST
  name: 按关键字模糊查询教室列表（用于前端下拉选择）。调 classroomAPI.findClassroomByName 返回匹配的教室 DTO 列表。
  controller: RccClassroomConfigController
  method_ref: getClassroomByName
  permission: '@EnableAuthority'
  exec_mode: 同步
  async: false
  description: 按关键字模糊查询教室列表（用于前端下拉选择）。调 classroomAPI.findClassroomByName 返回匹配的教室 DTO 列表。
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
request:
  dto: ClassroomQueryByNameRequest
  body:
    searchKeyword:
      type: String
      required: true
      constraint: '@NotNull'
      description: 教室名称搜索关键字
      value: ${param.classroom_name}
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    itemArr:
      type: ClassroomDTO[]
      description: 匹配教室列表（元素字段见下）
    classroomId:
      type: UUID
      description: 教室ID
    classroomName:
      type: String
      description: 教室名称
    timetableId:
      type: UUID
      description: 课表ID
    classroomState:
      type: ClassroomLessonStatusEnum
      description: 教室上课状态
    currentLessonId:
      type: UUID
      description: 当前上课ID
    startPolicy:
      type: DesktopStartPolicyEnum
      description: 上课云桌面启动策略
upstream:
- api: 内部调用:rcc/ClassroomAPI
  purpose: 按关键字查询教室列表
downstream:
- api: POST /rcc/classroom/* 与 /rcc/classroom/image/*
  purpose: 出参 ClassroomDTO.classroomId，是 create 异步批任务完成后获取教室ID的关键来源
constraints:
- level: PARAM
  field: searchKeyword
  rule: '@NotNull'
  failure: 缺失校验失败
assertions:
  success:
  - scenario: 传入关键字
    expect: $.status=="SUCCESS"；$.content 为匹配教室列表（可能为空）
  failure:
  - scenario: searchKeyword 为空
    trigger: 请求体缺少 searchKeyword
    expect: status==ERROR（参数校验失败）
cleanup: []
idempotency:
  level: non_idempotent
  note: 纯查询接口，无副作用
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/select

> 按关键字模糊查询教室列表（用于前端下拉选择）。调 classroomAPI.findClassroomByName 返回匹配的教室 DTO 列表。 ｜ @EnableAuthority ｜ 同步

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/select<br>按关键字模糊查询教室列表（用于前端下拉选择）。调 classroomAPI.fi<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(request)"]
        C2["Step2: classroomAPI.findClassroomByName(request"]
        C3["Step3: return CommonWebResponse.success(list)"]
        C1 --> C2
        C2 --> C3
    end
    B --> C1
    subgraph 下游消费方
        D1["POST /rcc/classroom/* 与 /rcc/classroom/image/*"]
    end
    B -->|数据| D1
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rcc/classroom/select |
| Controller | RccClassroomConfigController |
| 方法名 | getClassroomByName |
| 权限注解 | @EnableAuthority |
| 执行方式 | 同步 |
| 业务含义 | 按关键字模糊查询教室列表（用于前端下拉选择）。调 classroomAPI.findClassroomByName 返回匹配的教室 DTO 列表。 |

## 入参详情

### ClassroomQueryByNameRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| searchKeyword | String | 是 | @NotNull | 教室名称搜索关键字 |

## 出参详情

| 返回类型 | CommonWebResponse（data=List<ClassroomDTO>） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr | ClassroomDTO[] | 匹配教室列表（元素字段见下） |
| classroomId | UUID | 教室ID |
| classroomName | String | 教室名称 |
| timetableId | UUID | 课表ID |
| classroomState | ClassroomLessonStatusEnum | 教室上课状态 |
| currentLessonId | UUID | 当前上课ID |
| startPolicy | DesktopStartPolicyEnum | 上课云桌面启动策略 |

## 上游前置业务

（无上游数据依赖）
## 内部处理流程

### 处理流程

1. Assert.notNull(request)
2. classroomAPI.findClassroomByName(request) 查询
3. return CommonWebResponse.success(list)

## 下游消费方

### 消费1：POST /rcc/classroom/* 与 /rcc/classroom/image/*

出参 ClassroomDTO.classroomId，是 create 异步批任务完成后获取教室ID的关键来源（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | searchKeyword | @NotNull | 缺失校验失败 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| searchKeyword | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 传入关键字 | $.status=="SUCCESS"；$.content 为匹配教室列表（可能为空） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| searchKeyword 为空 | 请求体缺少 searchKeyword | status==ERROR（参数校验失败） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 纯查询接口，无副作用 |
