---
version: '2.0'
api:
  url: /rcc/classroom/image/getVDIDesktopCount
  method: POST
  name: 获取教室 VDI 云桌面数量（教师机或学生机），用于前端展示桌面数统计
  controller: RccClassroomImageController
  method_ref: getVDIDesktopCount
  permission: 无
  exec_mode: sync
  async: false
  description: 获取教室 VDI 云桌面数量（教师机或学生机），用于前端展示桌面数统计
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: create_classroom
  api: POST /rcc/classroom/create
  purpose: 创建教室（异步批任务，需轮询批任务完成后再查询教室）
  request:
    body:
      classroomName: ${param.classroom_name}
  idempotent: recreate
  delete_api: /rcc/classroom/delete
  delete_param: classroomId
- name: query_classroom
  api: POST /rcc/classroom/select
  extract:
    classroomId: $.content[0].classroomId
  purpose: 按名称过滤查询教室（searchKeyword=${param.classroom_name}）
  request:
    body:
      searchKeyword: ${param.classroom_name}
request:
  dto: GetVDILessonImageCountsRequest
  body:
    classroomId:
      type: UUID
      required: true
      constraint: '@NotNull 非空'
      description: 教室ID
    enableTeacher:
      type: Boolean
      required: true
      constraint: '@NotNull 非空'
      description: 是否教师机
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    content:
      type: GetVDILessonImageCountsResponse
      description: VDI 桌面数量统计
      fields:
        totalCount: Integer
upstream:
- api: POST /rcc/classroom/create -> POST /rcc/classroom/select
  produces: $.content[0].classroomId
  purpose: create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId
downstream:
- api: 内部调用:rcc/ClassroomDesktopRelationAPI#getVdiDesktopList
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: PARAM
  field: classroomId/enableTeacher
  rule: '@NotNull'
  failure: 参数缺失校验失败
assertions:
  success:
  - scenario: 教室有 VDI 桌面
    expect: $.status==SUCCESS && $.content.totalCount 非空（Builder.success(GetVDILessonImageCountsResponse)）
  - scenario: 无桌面
    expect: $.status==SUCCESS && $.content.totalCount==0
  failure:
  - scenario: 参数缺失
    trigger: classroomId 为空
    expect: $.status==ERROR（参数校验，无固定 msgKey）
cleanup: []
idempotency:
  level: non_idempotent
  note: 纯查询接口
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/classroom/image/getVDIDesktopCount

> 获取教室 VDI 云桌面数量（教师机或学生机），用于前端展示桌面数统计 ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create -> POST /rcc/classroom/select"]
    end
    B["POST /rcc/classroom/image/getVDIDesktopCount<br>获取教室 VDI 云桌面数量（教师机或学生机），用于前端展示桌面数统计<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull 校验 webRequest 与 sessionCo"]
        C2["Step2: 调用 classroomDesktopRelationAPI.getVdiDes"]
        C3["Step3: totalCount = 列表为空 ? 0 : size()"]
        C4["Step4: return success(response)"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
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
| URL | /rcc/classroom/image/getVDIDesktopCount |
| Controller | RccClassroomImageController |
| 方法名 | getVDIDesktopCount |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 获取教室 VDI 云桌面数量（教师机或学生机），用于前端展示桌面数统计 |

## 入参详情

### GetVDILessonImageCountsRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| classroomId | UUID | 是 | @NotNull 非空 | 教室ID |
| enableTeacher | Boolean | 是 | @NotNull 非空 | 是否教师机 |

## 出参详情

| 返回类型 | DefaultWebResponse（data=GetVDILessonImageCountsResponse） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| totalCount | Integer | VDI 桌面数量（默认0） |

## 上游前置业务

### 前置1：POST /rcc/classroom/create -> POST /rcc/classroom/select

create 为异步批任务，响应为 BatchTaskSubmitResult 不直接返回 ID；实际经 select 按名称查询 content[0].classroomId（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull 校验 webRequest 与 sessionContext
2. 调用 classroomDesktopRelationAPI.getVdiDesktopList(classroomId, teaTerminal)
3. totalCount = 列表为空 ? 0 : size()
4. return success(response)

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| PARAM | classroomId/enableTeacher | @NotNull | 参数缺失校验失败 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| classroomId | user_input/from_query | 按业务构造 |
| enableTeacher | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 教室有 VDI 桌面 | $.status==SUCCESS && $.content.totalCount 非空（Builder.success(GetVDILessonImageCountsResponse)） |
| 无桌面 | $.status==SUCCESS && $.content.totalCount==0 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 参数缺失 | classroomId 为空 | $.status==ERROR（参数校验，无固定 msgKey） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | HIGH |
| 说明 | 纯查询接口 |
