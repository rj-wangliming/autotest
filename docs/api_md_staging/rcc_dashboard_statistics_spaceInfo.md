---
version: '2.0'
api:
  url: /rcc/dashboard/statistics/spaceInfo
  method: POST
  name: 实训桌面池总览统计（按当前登录管理员维度）
  controller: RccDashboardStatisticsController
  method_ref: statisticsSpaceInfo
  permission: 无
  exec_mode: sync
  async: false
  description: 实训桌面池总览统计（按当前登录管理员维度）
request: {}
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: createClassroom
  api: POST /rcc/classroom/create
  purpose: 造空间/教室数据使统计有值
  extract:
    classroomName: auto_classroom_<ts>
  request:
    body:
      classroomName: ${param.classroom_name}
  idempotent: recreate
  delete_api: /rcc/classroom/delete
  delete_param: classroomId
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    spaceTotaDeskPoolNum:
      type: int
      description: 实训桌面池总数
    spaceDeskTotalNum:
      type: int
      description: 实训桌面总数
    runingSpaceDeskNum:
      type: int
      description: 运行中实训桌面数量
    connectedSpaceDeskNum:
      type: int
      description: 已连接实训桌面数量
    freeSpaceDeskNum:
      type: int
      description: 未分配实训桌面数量
    faultSpaceDeskNum:
      type: int
      description: 报障实训桌面数量
upstream:
- api: 内部调用:RccDashboardStatisticsAPI
  purpose: 按管理员ID统计实训桌面池总览
downstream: []
constraints:
- level: request
  field: sessionContext
  rule: 非空
  failure: webmvc 校验异常
assertions:
  success:
  - scenario: 正常统计
    expect: $.status==SUCCESS；$.content.spaceTotaDeskPoolNum 非空（>=0，StatisticsSpaceInfoRespone.spaceTotaDeskPoolNum）
  failure:
  - scenario: 系统异常
    trigger: 后端处理异常
    expect: status==ERROR（系统异常类 msgKey）
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
# POST /rcc/dashboard/statistics/spaceInfo

> 实训桌面池总览统计（按当前登录管理员维度） ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/dashboard/statistics/spaceInfo<br>实训桌面池总览统计（按当前登录管理员维度）<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert sessionContext 非空"]
        C2["Step2: rccDashboardStatisticsAPI.statisticsSpac"]
        C3["Step3: 包装为 StatisticsSpaceInfoRespone 返回"]
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
| URL | /rcc/dashboard/statistics/spaceInfo |
| Controller | RccDashboardStatisticsController |
| 方法名 | statisticsSpaceInfo |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 实训桌面池总览统计（按当前登录管理员维度） |

## 入参详情

### 

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| page | Integer | 否 | 分页页码 | 当前页（框架自动注入） |
| limit | Integer | 否 | 分页行数 | 每页条数（框架自动注入） |
## 出参详情

| 返回类型 | DefaultWebResponse<StatisticsSpaceInfoRespone> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| spaceTotaDeskPoolNum | int | 实训桌面池总数 |
| spaceDeskTotalNum | int | 实训桌面总数 |
| runingSpaceDeskNum | int | 运行中实训桌面数量 |
| connectedSpaceDeskNum | int | 已连接实训桌面数量 |
| freeSpaceDeskNum | int | 未分配实训桌面数量 |
| faultSpaceDeskNum | int | 报障实训桌面数量 |

## 上游前置业务

（无上游数据依赖）
## 内部处理流程

### 处理流程

1. Assert sessionContext 非空
2. rccDashboardStatisticsAPI.statisticsSpaceInfo(sessionContext.getUserId()) 统计
3. 包装为 StatisticsSpaceInfoRespone 返回

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | sessionContext | 非空 | webmvc 校验异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 正常统计 | $.status==SUCCESS；$.content.spaceTotaDeskPoolNum 非空（>=0） |

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
