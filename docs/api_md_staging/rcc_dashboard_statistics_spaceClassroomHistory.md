---
version: '2.0'
api:
  url: /rcc/dashboard/statistics/spaceClassroomHistory
  method: POST
  name: 教学（教室）桌面池使用率历史统计
  controller: RccDashboardStatisticsController
  method_ref: statisticsSpaceClassroomHistory
  permission: 无
  exec_mode: sync
  async: false
  description: 教学（教室）桌面池使用率历史统计
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: createClassroom
  api: POST /rcc/classroom/create
  purpose: 创建教室
  extract:
    classroomName: auto_classroom_<ts>
  request:
    body:
      classroomName: ${param.classroom_name}
  idempotent: recreate
  delete_api: /rcc/classroom/delete
  delete_param: classroomId
- name: listClassroom
  api: POST /rcc/classroom/list
  purpose: 按教室名精确过滤（matchArr.fieldName=classroomName）
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
request:
  dto: RccSpaceHistoryRequest
  body:
    id:
      type: UUID
      required: false
      constraint: '@Nullable 可空'
      description: 对象ID（教室/空间ID）
    timeQueryType:
      type: TimeQueryTypeEnum
      required: true
      constraint: '@NotNull 非空'
      description: 时间查询类型（可选值：HOUR/DAY/MONTHLY/YEAR/WEEK）
      value: ${param.time_query_type}
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    maxUseRateList:
      type: List<RccSpaceDesktopUsageRecordDTO>
      description: 最大使用率记录
    avgUseRateList:
      type: List<RccSpaceDesktopUsageRecordDTO>
      description: 平均使用率记录
    maxUseRateList[]_count:
      type: double
      description: 使用率数值
    maxUseRateList[]_dateTime:
      type: String
      description: 统计时间点
    avgUseRateList[]_count:
      type: double
      description: 使用率数值
    avgUseRateList[]_dateTime:
      type: String
      description: 统计时间点
upstream:
- api: 内部调用:RccDashboardStatisticsAPI
  purpose: 按RCC_CLASSROOM业务类型统计桌面池使用率历史
downstream: []
constraints:
- level: request
  field: timeQueryType
  rule: '@NotNull 非空'
  failure: webmvc 参数校验异常
assertions:
  success:
  - scenario: 正常统计
    expect: $.status==SUCCESS；$.content.maxUseRateList 非空（RccSpaceAndClassroomHistoryDTO.maxUseRateList）
  failure:
  - scenario: 必填参数缺失
    trigger: timeQueryType 未传或非法
    expect: status==ERROR（参数校验类 msgKey）
cleanup:
- api: POST /rcc/classroom/delete
  purpose: 清理 setup 阶段创建用于造统计数据的教室（需先经 /rcc/classroom/list 获取 classroomId）；接口本身不创建资源
idempotency:
  level: non_idempotent
  note: 纯统计查询
params:
  required:
  - name: classroom_name
    desc: ''
    used_by: 见 setup/request
---
# POST /rcc/dashboard/statistics/spaceClassroomHistory

> 教学（教室）桌面池使用率历史统计 ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/dashboard/statistics/spaceClassroomHistory<br>教学（教室）桌面池使用率历史统计<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert request 非空"]
        C2["Step2: rccDashboardStatisticsAPI.statisticsSpac"]
        C3["Step3: 返回 success(dto)"]
        C1 --> C2
        C2 --> C3
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
| URL | /rcc/dashboard/statistics/spaceClassroomHistory |
| Controller | RccDashboardStatisticsController |
| 方法名 | statisticsSpaceClassroomHistory |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 教学（教室）桌面池使用率历史统计 |

## 入参详情

### RccSpaceHistoryRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| id | UUID | 否 | @Nullable 可空 | 对象ID（教室/空间ID） |
| timeQueryType | TimeQueryTypeEnum | 是 | @NotNull 非空 | 时间查询类型 |

## 出参详情

| 返回类型 | DefaultWebResponse<RccSpaceAndClassroomHistoryDTO> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| maxUseRateList | List<RccSpaceDesktopUsageRecordDTO> | 最大使用率记录 |
| avgUseRateList | List<RccSpaceDesktopUsageRecordDTO> | 平均使用率记录 |
| maxUseRateList[].count | double | 使用率数值 |
| maxUseRateList[].dateTime | String | 统计时间点 |
| avgUseRateList[].count | double | 使用率数值 |
| avgUseRateList[].dateTime | String | 统计时间点 |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 处理流程

1. Assert request 非空
2. rccDashboardStatisticsAPI.statisticsSpaceHistory(id, timeQueryType, BusinessTypeAndCreateSourceEnum.RCC_CLASSROOM)
3. 返回 success(dto)

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | timeQueryType | @NotNull 非空 | webmvc 参数校验异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| id | user_input/from_query | 按业务构造 |
| timeQueryType | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 正常统计 | $.status==SUCCESS；$.content.maxUseRateList 非空（RccSpaceAndClassroomHistoryDTO.maxUseRateList） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 权限不足 | 无授权 | 403 |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| POST /rcc/classroom/delete | 清理 setup 阶段创建用于造统计数据的教室（需先经 /rcc/classroom/list 获取 classroomId）；接口本身不创建资源 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | high |
| 说明 | 纯统计查询 |
