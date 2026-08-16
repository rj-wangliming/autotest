---
version: '2.0'
api:
  url: /rcc/classroom/cmr/freeClassroom/list
  method: POST
  name: 分页查询自由组班教室列表（CMR客户端免认证调用）
  controller: RccFreeClassroomController
  method_ref: getFreeClassroomPage
  permission: 无
  exec_mode: sync
  async: false
  description: 分页查询自由组班教室列表（CMR客户端免认证调用）
setup:
- name: up_1
  api: 内部调用:rccFreeClassroomAPI
  method: POST
  produces: PageQueryResponse<FreeClassroomEntity>
  purpose: （内部调用）
request:
  dto: PageQueryRequest
  body:
    rows:
      type: Integer
      required: false
      constraint: 分页行数
      description: 每页条数
    page:
      type: Integer
      required: false
      constraint: 分页页码
      description: 当前页
    sort:
      type: Object
      required: false
      description: 排序与过滤条件（sort）
    condition:
      type: Object
      required: false
      description: 排序与过滤条件（condition）
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    itemArr[]:
      type: FreeClassroomDetailDTO[]
      description: 自由组班记录列表
    id:
      type: UUID
      description: 记录ID
    password:
      type: String
      description: 密码
    classroomName:
      type: String
      description: 教室名称
    teacherIp:
      type: String
      description: 教师机IP
    cmrId:
      type: UUID
      description: CMR ID
    teacherMac:
      type: String
      description: 教师机MAC
    studentMaxLimit:
      type: Integer
      description: 学生上限
    lessonDuration:
      type: Integer
      description: 上课时长
    total:
      type: Long
      description: 总记录数
    itemArr:
      type: List<Object>
      description: 分页数据项（位于 content 下：$.content.itemArr）
upstream:
- api: 内部调用:rccFreeClassroomAPI
  purpose: 分页查询自由组班DAO数据
downstream: []
constraints:
- level: request
  field: pageQueryRequest
  rule: 分页对象不能为空
  failure: Assert校验抛异常
assertions:
  success:
  - scenario: 自由组班存在记录
    expect: $.status=="SUCCESS"；$.content.itemArr 非空；$.content.total 非空
  failure:
  - scenario: 分页参数为空
    trigger: pageQueryRequest为null
    expect: status==ERROR（Assert 参数校验失败）
cleanup: []
idempotency:
  level: fully_idempotent
  note: 纯查询接口
---
# POST /rcc/classroom/cmr/freeClassroom/list

> 分页查询自由组班教室列表（CMR客户端免认证调用） ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/classroom/cmr/freeClassroom/list<br>分页查询自由组班教室列表（CMR客户端免认证调用）<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(pageQueryRequest) 校验分页参数"]
        C2["Step2: pageQueryBuilderFactory.newRequestBuilde"]
        C3["Step3: rccFreeClassroomAPI.pageQueryFreeClassro"]
        C4["Step4: 返回PageQueryResponse<FreeClassroomDetailD"]
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
| URL | /rcc/classroom/cmr/freeClassroom/list |
| Controller | RccFreeClassroomController |
| 方法名 | getFreeClassroomPage |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 分页查询自由组班教室列表（CMR客户端免认证调用） |

## 入参详情

### PageQueryRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| rows | Integer | 否 | 分页行数 | 每页条数 |
| page | Integer | 否 | 分页页码 | 当前页 |
| condition | Object | 否 |  | 排序与过滤条件（condition） |
| sort | Object | 否 |  | 排序与过滤条件（sort） |
## 出参详情

| 返回类型 | DefaultWebResponse<PageQueryResponse<FreeClassroomDetailDTO>> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr[] | FreeClassroomDetailDTO[] | 自由组班记录列表 |
| id | UUID | 记录ID |
| password | String | 密码 |
| classroomName | String | 教室名称 |
| teacherIp | String | 教师机IP |
| cmrId | UUID | CMR ID |
| teacherMac | String | 教师机MAC |
| studentMaxLimit | Integer | 学生上限 |
| lessonDuration | Integer | 上课时长 |
| total | Long | 总记录数 |

## 上游前置业务

（无上游数据依赖）
## 内部处理流程

### 处理流程

1. Assert.notNull(pageQueryRequest) 校验分页参数
2. pageQueryBuilderFactory.newRequestBuilder(pageQueryRequest) 构造分页请求
3. rccFreeClassroomAPI.pageQueryFreeClassroom(builder.build()) 分页查询自由组班
4. 返回PageQueryResponse<FreeClassroomDetailDTO>

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | pageQueryRequest | 分页对象不能为空 | Assert校验抛异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| rows | user_input/from_query | 按业务构造 |
| page | user_input/from_query | 按业务构造 |
| sort/condition | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 自由组班存在记录 | $.status=="SUCCESS"；$.content.itemArr 非空；$.content.total 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 分页参数为空 | pageQueryRequest为null | status==ERROR（Assert 参数校验失败） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | readonly |
| 说明 | 纯查询接口 |
