---
version: '2.0'
api:
  url: /rco/admin/loginAdmin
  method: POST
  name: 管理员登录（框架内置，executor.login 自动调用）
  controller: AdminManageController
  method_ref: loginAdmin
  permission: '@NoAuthUrl'
  exec_mode: sync
  async: false
  description: 管理员登录，返回 token；凭据经 AES 加密传输（pwd 非明文）。框架内置登录，不参与用例编排。
request:
  dto: LoginAdminWebRequest
  body:
    userName:
      type: String
      required: true
      constraint: '@NotBlank @TextShort @TextName'
      description: 管理员账号
      value: ${param.rcdc_user}
    pwd:
      type: String
      required: true
      constraint: '@NotBlank；AES-128-CBC 加密（key=ADMINPASSWORDKEY，随机 IV 前置，Base64）'
      description: 密码密文——后端固定 AesUtil.descrypt(pwd, ADMINPASSWORDKEY) 解密，明文会抛 RCDC_RCO_DECRYPT_FAIL
      value: ${param.rcdc_passwd}
    timestamp:
      type: Long
      required: true
      constraint: '@NotNull；毫秒时间戳；与上次登录相同会拒绝（ALREADY_LOGIN_CURRENT_TIME 防重放）'
      description: 请求时间戳（毫秒），每次登录必须生成新值
    captchaCode:
      type: String
      required: false
      constraint: '@Nullable'
      description: 验证码（未启用验证码时传空串）
    captchaKey:
      type: String
      required: false
      constraint: '@Nullable'
      description: 验证码 key（未启用验证码时传空串）
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    content:
      type: AdminVO
      description: 登录成功返回管理员信息与 token
      fields:
        token: String
        id: UUID
        userName: String
        menuNameArr: String[]
assertions:
  success:
  - scenario: 凭据正确
    expect: $.status==SUCCESS；$.content.token 非空
  failure:
  - scenario: pwd 未加密
    trigger: 明文密码
    expect: status==ERROR（RCDC_RCO_DECRYPT_FAIL）
  - scenario: pwd 为空
    trigger: pwd 缺失
    expect: status==ERROR（sk_validation_NotBlank）
  - scenario: timestamp 重复
    trigger: 与上次登录相同时间戳
    expect: status==ERROR（ALREADY_LOGIN_CURRENT_TIME）
idempotency:
  level: not_idempotent
  note: 每次登录生成新 token；timestamp 防重放，重复同值会被拒
---
# POST /rco/admin/loginAdmin

> 管理员登录 ｜ @NoAuthUrl ｜ 同步

## 接口基本信息

| 项目 | 内容 |
|---|---|
| URL | /rco/admin/loginAdmin |
| Controller | AdminManageController |
| 方法名 | loginAdmin |
| 权限 | @NoAuthUrl（免登录） |
| 业务含义 | 管理员登录，返回 token；框架内置登录（executor.login 自动调用，不参与用例编排） |

## 入参详情

### LoginAdminWebRequest（5 字段）

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| userName | String | 是 | @NotBlank @TextShort @TextName | 管理员账号 |
| pwd | String | 是 | @NotBlank；**AES-128-CBC 加密** | 密码密文——后端固定 `AesUtil.descrypt(pwd, ADMINPASSWORDKEY)` 解密；**明文会抛 RCDC_RCO_DECRYPT_FAIL** |
| timestamp | Long | 是 | @NotNull；毫秒时间戳 | 防重放：与上次登录相同会拒绝（ALREADY_LOGIN_CURRENT_TIME），每次必须新值 |
| captchaCode | String | 否 | @Nullable | 验证码（未启用时传空串） |
| captchaKey | String | 否 | @Nullable | 验证码 key（未启用时传空串） |

## 出参详情

| 字段 | 类型 | 说明 |
|---|---|---|
| content.token | String | 登录 token（后续请求 Authorization: Bearer <token>） |
| content.id / userName / menuNameArr | UUID / String / String[] | 管理员信息 |

## 加密约定（pwd）

- 算法：AES-128-CBC，key=`ADMINPASSWORDKEY`（16 字节，来自 RedLineUtil.getRealAdminRedLine()）
- 填充：PKCS7；随机 16 字节 IV **前置**于密文，整体 Base64 编码
- 示例：明文 `ruijie@!23` → `JAHsbfmj1Tem365ltzfFiH6LLP8JTPKuoBvO5/3Ozmo=`
- 校验：后端解密失败抛 `RCDC_RCO_DECRYPT_FAIL`，**明文密码永远登录失败**

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 凭据正确 | $.status==SUCCESS；$.content.token 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| pwd 未加密 | 明文密码 | status==ERROR（RCDC_RCO_DECRYPT_FAIL） |
| pwd 为空 | pwd 缺失 | status==ERROR（sk_validation_NotBlank） |
| timestamp 重复 | 与上次登录相同 | status==ERROR（ALREADY_LOGIN_CURRENT_TIME） |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | not_idempotent |
| 说明 | 每次登录生成新 token；timestamp 防重放，重复同值会被拒 |
