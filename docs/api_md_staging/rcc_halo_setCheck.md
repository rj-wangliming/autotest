---
version: '2.0'
api:
  url: /rcc/halo/setCheck
  method: POST
  name: 启用/禁用Halo体检：写全局参数 RCC_ENABLE_HALO_CHECK
  controller: RccHaloController
  method_ref: disableHaloCheck
  permission: 无
  exec_mode: sync
  async: false
  description: 启用/禁用Halo体检：写全局参数 RCC_ENABLE_HALO_CHECK
setup:
- name: up_1
  api: 内部调用:PlatformRcoGlobalParameterAPI
  method: POST
  produces: void
  purpose: （内部调用）
request:
  dto: SetHaloCheckRequest
  body:
    disableHaloCheck:
      type: Boolean
      required: true
      constraint: '@NotNull 非空'
      description: true=禁用Halo体检，false=启用
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
upstream:
- api: 内部调用:PlatformRcoGlobalParameterAPI
  purpose: 更新 RCC_ENABLE_HALO_CHECK 全局参数
downstream:
- api: 内部调用:PlatformRcoGlobalParameterAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: request
  field: disableHaloCheck
  rule: '@NotNull 非空'
  failure: webmvc 参数校验异常
assertions:
  success:
  - scenario: 传入布尔开关
    expect: $.status==SUCCESS；content 为空（Builder.success() 无参，纯操作接口）
  failure:
  - scenario: 参数为空
    trigger: request 为 null（Assert.notNull）
    expect: $.status==ERROR（参数校验失败，无固定 msgKey）
cleanup:
- api: 无对应 HTTP 清理接口
  purpose: 本接口为纯参数更新接口，不创建可清理资源；无对应 HTTP 删除接口
idempotency:
  level: non_idempotent
  note: 参数覆盖写入，重复设置同值幂等
---
# POST /rcc/halo/setCheck

> 启用/禁用Halo体检：写全局参数 RCC_ENABLE_HALO_CHECK ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/halo/setCheck<br>启用/禁用Halo体检：写全局参数 RCC_ENABLE_HALO_CHECK<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert request 非空"]
        C2["Step2: rcoGlobalParameterAPI.updateParameter(Up"]
        C3["Step3: 返回 success()"]
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
| URL | /rcc/halo/setCheck |
| Controller | RccHaloController |
| 方法名 | disableHaloCheck |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 启用/禁用Halo体检：写全局参数 RCC_ENABLE_HALO_CHECK |

## 入参详情

### SetHaloCheckRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| disableHaloCheck | Boolean | 是 | @NotNull 非空 | true=禁用Halo体检，false=启用 |

## 出参详情

| 返回类型 | DefaultWebResponse |
|---|---|
| 说明 | 成功返回 SUCCESS；失败返回 status/msgKey |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 处理流程

1. Assert request 非空
2. rcoGlobalParameterAPI.updateParameter(UpdateParameterRequest(RCC_ENABLE_HALO_CHECK, disableHaloCheck.toString()))
3. 返回 success()

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | disableHaloCheck | @NotNull 非空 | webmvc 参数校验异常 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| disableHaloCheck | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

> 该接口为纯操作接口（Builder.success() 无 content body），断言以 HTTP 响应为准：status==SUCCESS + content 为空。无 content body（纯参数更新接口）


### 成功场景

| 场景 | 断言点 |
|---|---|
| 传入布尔开关 | $.status==SUCCESS；content 为空（Builder.success() 无参） |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 权限不足 | 无授权 | 403 |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 无对应 HTTP 清理接口 | 本接口为纯参数更新接口，不创建可清理资源；无对应 HTTP 删除接口 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | high |
| 说明 | 参数覆盖写入，重复设置同值幂等 |
