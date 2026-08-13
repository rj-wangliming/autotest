---
version: '2.0'
api:
  url: /spacetci/lessonImage/getLessonImageList
  method: POST
  name: 分页获取课程镜像列表，按管理员数据权限自动过滤教室/镜像范围
  controller: TCILessonImageController
  method_ref: getLessonImageList
  permission: '@EnableAuthority'
  exec_mode: sync
  async: false
  description: 分页获取课程镜像列表，按管理员数据权限自动过滤教室/镜像范围
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
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
      type: TCIViewLessonImageDTO[]
      description: 课程镜像分页列表
    id:
      type: UUID
      description: 课程镜像ID
    classroomId:
      type: UUID
      description: 教室ID
    classroomName:
      type: String
      description: 教室名称
    imageId:
      type: UUID
      description: 镜像模板ID
    imageName:
      type: String
      description: 镜像名称
    teacherImage:
      type: Boolean
      description: 是否教师机镜像
    hide:
      type: Boolean
      description: 是否隐藏
    lessonStrategyId:
      type: UUID
      description: 课程策略ID
    strategyName:
      type: String
      description: 策略名称
    total:
      type: Long
      description: 总条数
    itemArr:
      type: List<Object>
      description: 分页数据项（位于 content 下：$.content.itemArr）
upstream:
- api: POST /rcc/classroom/create
  produces: $.content.itemArr[*].classroomId
  purpose: 教室ID筛选（可空）
downstream: []
constraints:
- level: data
  field: admin
  rule: 非全量权限自动追加教室与镜像权限过滤
  failure: 无权限数据自动不可见
assertions:
  success:
  - scenario: 任意权限管理员查询
    expect: $.status==SUCCESS && $.content.itemArr 非空（PageQueryResponse 分页框架字段为 itemArr/total）
  failure:
  - scenario: 分页参数为空
    trigger: pageQueryRequest为null
    expect: $.status==ERROR（Assert 参数校验，无固定 msgKey）
cleanup: []
idempotency:
  level: fully_idempotent
  note: 纯查询接口
---
# POST /spacetci/lessonImage/getLessonImageList

> 分页获取课程镜像列表，按管理员数据权限自动过滤教室/镜像范围 ｜ @EnableAuthority ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create"]
    end
    B["POST /spacetci/lessonImage/getLessonImageList<br>分页获取课程镜像列表，按管理员数据权限自动过滤教室/镜像范围<br>权限: @EnableAuthority"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert.notNull(pageQueryRequest/sessionC"]
        C2["Step2: pageQueryBuilderFactory.newRequestBuilde"]
        C3["Step3: 全量权限直接查询；否则按TERMINAL_GROUP权限映射教室ID做class"]
        C4["Step4: tciLessonImageAPI.pageQueryLessonImage 分"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
    end
    B --> C1
    subgraph 下游消费方
        D1["getInfo/getStrategy/delete/hide/show/update/strategy/edit"]
    end
    B -->|数据| D1
```

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /spacetci/lessonImage/getLessonImageList |
| Controller | TCILessonImageController |
| 方法名 | getLessonImageList |
| 权限注解 | @EnableAuthority |
| 执行方式 | sync |
| 业务含义 | 分页获取课程镜像列表，按管理员数据权限自动过滤教室/镜像范围 |

## 入参详情

### PageQueryRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| rows | Integer | 否 | 分页行数 | 每页条数 |
| page | Integer | 否 | 分页页码 | 当前页 |
| condition | Object | 否 |  | 排序与过滤条件（condition） |
| sort | Object | 否 |  | 排序与过滤条件（sort） |## 出参详情

| 返回类型 | DefaultWebResponse<PageQueryResponse<TCIViewLessonImageDTO>> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr[] | TCIViewLessonImageDTO[] | 课程镜像分页列表 |
| id | UUID | 课程镜像ID |
| classroomId | UUID | 教室ID |
| classroomName | String | 教室名称 |
| imageId | UUID | 镜像模板ID |
| imageName | String | 镜像名称 |
| teacherImage | Boolean | 是否教师机镜像 |
| hide | Boolean | 是否隐藏 |
| lessonStrategyId | UUID | 课程策略ID |
| strategyName | String | 策略名称 |
| total | Long | 总条数 |

## 上游前置业务

### 前置1：POST /rcc/classroom/create

教室ID筛选（可空）（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert.notNull(pageQueryRequest/sessionContext) 校验入参
2. pageQueryBuilderFactory.newRequestBuilder(pageQueryRequest) 构造分页请求
3. 全量权限直接查询；否则按TERMINAL_GROUP权限映射教室ID做classroomId in过滤，按IMAGE权限做imageId in过滤
4. tciLessonImageAPI.pageQueryLessonImage 分页查询并返回

## 下游消费方

### 消费1：POST /spacetci/lessonImage/getLessonImageList

课程镜像ID，被 getInfo/getStrategy/delete/hide/show/update/strategy/edit 消费（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| data | admin | 非全量权限自动追加教室与镜像权限过滤 | 无权限数据自动不可见 |

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
| 任意权限管理员查询 | $.status==SUCCESS && $.content.itemArr 非空（PageQueryResponse 分页框架字段为 itemArr/total） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 分页参数为空 | pageQueryRequest为null | $.status==ERROR（Assert 参数校验，无固定 msgKey） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | readonly |
| 说明 | 纯查询接口 |
