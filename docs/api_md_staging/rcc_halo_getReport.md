---
version: '2.0'
api:
  url: /rcc/halo/getReport
  method: POST
  name: HALO 体检报告上报回调：按文件名处理体检报告，返回处理结果
  controller: RccHaloController
  method_ref: receiveHaloReport
  permission: 无
  exec_mode: sync
  async: false
  description: HALO 体检报告上报回调：按文件名处理体检报告，返回处理结果
setup:
- name: up_1
  api: 内部调用:RccHaloCheckAPI
  method: POST
  produces: void
  purpose: （内部调用）
request:
  dto: request param
  body:
    fileName:
      type: String
      required: true
      constraint: URL query 参数（非DTO）
      description: Halo体检报告文件名
      value: ${param.file_name}
response:
  wrapper:
    result: String
    desc: String
  body:
    result:
      type: String
      description: 处理结果（success=成功/fail=失败）
    desc:
      type: String
      description: 描述信息（成功时为 SUCCESS，失败时为 i18n 错误信息）
upstream:
- api: 内部调用:RccHaloCheckAPI
  purpose: 处理指定路径下的Halo体检报告
downstream:
- api: 内部调用:RccHaloCheckAPI
  purpose: 内部调用（非 HTTP 端点）
constraints:
- level: request
  field: fileName
  rule: URL 参数需存在且指向有效报告文件
  failure: 文件缺失/解析失败抛 BusinessException
assertions:
  success:
  - scenario: 报告文件存在且处理成功
    expect: $.result==success；$.desc==SUCCESS（ResponseResultDTO 结构：{"result":"success","desc":"SUCCESS"}，非 DefaultWebResponse wrapper）
  failure:
  - scenario: 报告处理失败
    trigger: fileName 缺失/文件不存在/解析异常
    expect: $.result==fail；$.desc 非空（ResponseResultDTO.resultFail 写入 i18n 错误信息，非 DefaultWebResponse wrapper）
cleanup:
- api: 无对应 HTTP 清理接口
  purpose: 本接口为 Halo 报告上报回调，不创建可清理资源；无对应 HTTP 删除接口
idempotency:
  level: data_level
  note: 重复上报会重复处理同一报告文件，无防重标记
---
# POST /rcc/halo/getReport

> HALO 体检报告上报回调：按文件名处理体检报告，返回处理结果 ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["（无 HTTP 上游，内部服务调用）"]
    end
    B["POST /rcc/halo/getReport<br>HALO 体检报告上报回调：按文件名处理体检报告，返回处理结果<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: 从 RequestContextHolder 取 request/respons"]
        C2["Step2: request.getParameter("fileName") 取文件名并拼接"]
        C3["Step3: haloCheckAPI.dealHaloCheckReport(路径) 处理报"]
        C4["Step4: 成功输出 resultSuccess("SUCCESS")；BusinessEx"]
        C5["Step5: responseOutWithJson 以 UTF-8 JSON 写回"]
        C1 --> C2
        C2 --> C3
        C3 --> C4
        C4 --> C5
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
| URL | /rcc/halo/getReport |
| Controller | RccHaloController |
| 方法名 | receiveHaloReport |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | HALO 体检报告上报回调：按文件名处理体检报告，返回处理结果 |

## 入参详情

### request param

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| fileName | String | 是 | URL query 参数（非DTO） | Halo体检报告文件名 |

## 出参详情

| 返回类型 | ResponseResultDTO（responseOutWithJson 直接输出 JSON：{"result":"...","desc":"..."}，非 DefaultWebResponse wrapper） |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| result | String | 处理结果（success=成功/fail=失败，ResponseResultDTO.result） |
| desc | String | 描述信息（成功时为 SUCCESS；失败时为 i18n 错误信息，ResponseResultDTO.desc） |

## 上游前置业务

> 本接口上游为服务端内部调用（非 HTTP 端点）：
> - 
## 内部处理流程

### 处理流程

1. 从 RequestContextHolder 取 request/response
2. request.getParameter("fileName") 取文件名并拼接 CommonConstants.RCC_HALOCHECK_PATH 路径
3. haloCheckAPI.dealHaloCheckReport(路径) 处理报告
4. 成功输出 resultSuccess("SUCCESS")；BusinessException 输出 resultFail(i18nMessage)
5. responseOutWithJson 以 UTF-8 JSON 写回

## 下游消费方

（本接口数据主要被自身/关联接口消费，或经 SPI 通知）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | fileName | URL 参数需存在且指向有效报告文件 | 文件缺失/解析失败抛 BusinessException |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| fileName | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 报告文件存在且处理成功 | $.result==success；$.desc==SUCCESS |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 报告处理失败 | fileName 缺失/文件不存在/解析异常 | $.result==fail；$.desc 非空（i18n 错误信息） |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 无对应 HTTP 清理接口 | 本接口为 Halo 报告上报回调，不创建可清理资源；无对应 HTTP 删除接口 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | medium |
| 说明 | 重复上报会重复处理同一报告文件，无防重标记 |
