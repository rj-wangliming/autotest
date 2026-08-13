---
version: '2.0'
api:
  url: /rcc/halo/getScores
  method: GET
  name: 获取Halo体检分数
  controller: RccHaloController
  method_ref: getHaloScores
  permission: 无
  exec_mode: sync
  async: false
  description: 获取Halo体检分数
request: {}
setup:
- name: up_1
  api: 内部调用:RccHaloCheckAPI
  method: POST
  produces: int
  purpose: （内部调用）
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    scores:
      type: int
      description: Halo体检分数（HaloScoresDTO.scores）
upstream:
- api: 内部调用:RccHaloCheckAPI
  purpose: 查询Halo体检分数
downstream: []
assertions:
  success:
  - scenario: 正常查询
    expect: $.status==SUCCESS；$.content.scores 非空（HaloScoresDTO.scores，int）
  failure:
  - scenario: 系统异常
    trigger: 后端处理异常
    expect: status==ERROR（系统异常类 msgKey）
cleanup:
- api: 无对应 HTTP 清理接口
  purpose: 本接口为纯查询接口，不创建可清理资源；无对应 HTTP 删除接口
idempotency:
  level: non_idempotent
  note: 纯查询接口
---
# GET /rcc/halo/getScores

> 获取Halo体检分数 ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["GET /rcc/halo/getScores<br>获取Halo体检分数<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: haloCheckAPI.getHaloCheckScores() 取分数"]
        C2["Step2: 封装 HaloScoresDTO 返回"]
        C1 --> C2
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
| URL | /rcc/halo/getScores（GET） |
| Controller | RccHaloController |
| 方法名 | getHaloScores |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 获取Halo体检分数 |

## 入参详情

### 

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| page | Integer | 否 | 分页页码 | 当前页（框架自动注入） |
| limit | Integer | 否 | 分页行数 | 每页条数（框架自动注入） |
## 出参详情

| 返回类型 | DefaultWebResponse<HaloScoresDTO>（$.content 为 HaloScoresDTO） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| scores | int | Halo体检分数（HaloScoresDTO.scores） |

## 上游前置业务

（无上游数据依赖）
## 内部处理流程

### 处理流程

1. haloCheckAPI.getHaloCheckScores() 取分数
2. 封装 HaloScoresDTO 返回

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| （本接口无请求体参数约束） | | | |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 正常查询 | $.status==SUCCESS；$.content.scores 非空（HaloScoresDTO.scores，int） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 权限不足 | 无授权 | 403 |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 无对应 HTTP 清理接口 | 本接口为纯查询接口，不创建可清理资源；无对应 HTTP 删除接口 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | high |
| 说明 | 纯查询接口 |
