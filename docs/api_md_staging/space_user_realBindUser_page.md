---
version: '2.0'
api:
  url: /space/user/realBindUser/page
  method: POST
  name: 分页查询桌面池真实绑定用户（仅已分配且非访客类型用户）
  controller: SpaceUserController
  method_ref: pageRealBindUser
  permission: 无
  exec_mode: sync
  async: false
  description: 分页查询桌面池真实绑定用户（仅已分配且非访客类型用户）
setup:
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
- name: create_classroom
  api: POST /rcc/classroom/create
  purpose: 创建教室产生 classroomId
  request:
    body:
      classroomName: ${param.classroom_name}
  idempotent: recreate
  delete_api: /rcc/classroom/delete
  delete_param: classroomId
- name: select_classroom_id
  api: POST /rcc/classroom/select
  purpose: 按名称过滤查询教室（searchKeyword=${param.classroom_name}）
  extract:
    classroomId: $.content[0].classroomId
  request:
    body:
      searchKeyword: ${param.classroom_name}
request:
  dto: PageQueryRequest
  body:
    page:
      type: Integer
      required: true
      constraint: pagekit 分页参数
      description: 页码
    limit:
      type: Integer
      required: true
      constraint: pagekit 分页参数
      description: 每页条数
    matchArr:
      type: Match[]
      required: true
      constraint: 需含 classroomId 匹配条件
      description: 查询条件
response:
  wrapper:
    status: String
    message: String
    msgKey: String
    msgArgArr: String[]
    content: Object
  body:
    itemArr:
      type: UserListDTO[]
      description: 真实绑定用户列表
    total:
      type: Long
      description: 总数
    itemArr[]_id:
      type: UUID
      description: 用户ID
    itemArr[]_hostId:
      type: UUID
      description: 主机ID
    itemArr[]_userRole:
      type: String
      description: 用户角色
    itemArr[]_userType:
      type: IacUserTypeEnum
      description: 用户类型
    itemArr[]_realName:
      type: String
      description: 真实姓名
    itemArr[]_userDescription:
      type: String
      description: 用户描述
    itemArr[]_userName:
      type: String
      description: 用户名
    itemArr[]_phoneNum:
      type: String
      description: 手机号
    itemArr[]_groupId:
      type: UUID
      description: 用户组ID
    itemArr[]_groupName:
      type: String
      description: 用户组名称
    itemArr[]_groupNameArr:
      type: String[]
      description: 用户组名称数组
    itemArr[]_userState:
      type: IacUserStateEnum
      description: 用户状态
    itemArr[]_createTime:
      type: Date
      description: 创建时间
    itemArr[]_email:
      type: String
      description: 邮箱
    itemArr[]_desktopNum:
      type: Integer
      description: 绑定云桌面数量
    itemArr[]_canDelete:
      type: Boolean
      description: 是否可删除
    itemArr[]_hasRecycleBin:
      type: Boolean
      description: 回收站是否有桌面
    itemArr[]_lock:
      type: Boolean
      description: 是否锁定
    itemArr[]_lockTime:
      type: Date
      description: 锁定时间
    itemArr[]_unlockTime:
      type: Date
      description: 解锁时间
    itemArr[]_openOtpCertification:
      type: Boolean
      description: 是否开启动态口令认证
    itemArr[]_hasBindOtp:
      type: Boolean
      description: 是否绑定动态口令
    itemArr[]_openCasCertification:
      type: Boolean
      description: 是否开启外部CAS认证
    itemArr[]_openAccountPasswordCertification:
      type: Boolean
      description: 是否开启账号密码认证
    itemArr[]_openHardwareCertification:
      type: Boolean
      description: 是否开启硬件特征码
    itemArr[]_openSmsCertification:
      type: Boolean
      description: 是否开启短信认证
    itemArr[]_openThirdPartyCertification:
      type: Boolean
      description: 是否开启第三方认证
    itemArr[]_accountExpireDateStr:
      type: String
      description: 账户过期时间（字符串）
    itemArr[]_enableDomainSync:
      type: Boolean
      description: 是否开启域同步
    itemArr[]_isAssigned:
      type: Boolean
      description: 是否已分配
    itemArr[]_hasBindDisk:
      type: Boolean
      description: 是否绑定磁盘
    itemArr[]_disabled:
      type: Boolean
      description: 是否禁用
    itemArr[]_invalidTime:
      type: Integer
      description: 失效时长
    itemArr[]_isInvalid:
      type: Boolean
      description: 是否失效
    itemArr[]_invalidDescription:
      type: String
      description: 失效描述
    itemArr[]_accountExpireDate:
      type: String
      description: 账户过期时间
    itemArr[]_openRadiusCertification:
      type: Boolean
      description: 是否开启RADIUS认证
    itemArr[]_vdi1License:
      type: Integer
      description: 是否占用VDI1授权（1/0）
    itemArr[]_vdi1LicenseDuration:
      type: CbbLicenseDurationEnum
      description: VDI1授权持续类型
    itemArr[]_vgpuLicense:
      type: Integer
      description: 是否占用3D设计授权（1/0）
    itemArr[]_vgpuLicenseDuration:
      type: CbbLicenseDurationEnum
      description: 3D设计授权持续类型
    itemArr[]_hasBindPoolDesktop:
      type: Boolean
      description: 是否绑定桌面池中的桌面
    itemArr[]_hasBindAppHost:
      type: Boolean
      description: 是否绑定静态应用主机
    itemArr[]_openWorkWeixinCertification:
      type: Boolean
      description: 是否开启企业微信认证
    itemArr[]_openFeishuCertification:
      type: Boolean
      description: 是否开启飞书认证
    itemArr[]_openDingdingCertification:
      type: Boolean
      description: 是否开启钉钉认证
    itemArr[]_openOauth2Certification:
      type: Boolean
      description: 是否开启OAuth2认证
    itemArr[]_openPluginCertification:
      type: Boolean
      description: 是否开启插件认证
    itemArr[]_openRjclientCertification:
      type: Boolean
      description: 是否开启锐捷客户端扫码
    itemArr[]_groupPath:
      type: String
      description: 用户组路径
    itemArr[]_enableCustomPasswordPolicy:
      type: Boolean
      description: 是否开启自定义密码有效期
    itemArr[]_thirdPartyUserDisableType:
      type: ThirdPartyUserDisableType
      description: 第三方用户禁用类型
    itemArr[]_hasVdi1License:
      type: Boolean
      description: 是否占用VDI1授权
    itemArr[]_hasVgpuLicense:
      type: Boolean
      description: 是否占用3D设计授权
    itemArr[]_workRole:
      type: IacWorkRole
      description: 用户工作角色
upstream:
- api: POST /rcc/classroom/create
  produces: $.content.classroomId
  purpose: 教室ID（通过 exact match 字段 classroomId 传入），来源为教室创建返回
downstream: []
constraints:
- level: request
  field: request
  rule: 非空且需含 classroomId 匹配条件
  failure: 缺少classroomId时 Assert 失败
assertions:
  success:
  - scenario: 无权限
    expect: $.status==SUCCESS 且 $.content.itemArr 为空
  - scenario: 有已分配用户
    expect: $.content.itemArr 非空
  failure:
  - scenario: 必填参数缺失
    trigger: page/limit/matchArr 未传或非法
    expect: status==ERROR（参数校验类 msgKey）
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
# POST /space/user/realBindUser/page

> 分页查询桌面池真实绑定用户（仅已分配且非访客类型用户） ｜ 无特殊权限 ｜ sync

## 依赖关系全景图

```mermaid
graph LR
    subgraph 上游前置业务
        A1["POST /rcc/classroom/create"]
    end
    B["POST /space/user/realBindUser/page<br>分页查询桌面池真实绑定用户（仅已分配且非访客类型用户）<br>权限: 无"]
    A1 -->|数据| B
    subgraph 内部处理流程
        C1["Step1: Assert request/sessionContext 非空"]
        C2["Step2: buildAssignmentQueryContext 解析 classroom"]
        C3["Step3: 构造 PoolUserQueryRequest{已分配=true, enable"]
        C4["Step4: findBindDeskUserIdSet 取绑定桌面用户ID，convertR"]
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
| URL | /space/user/realBindUser/page |
| Controller | SpaceUserController |
| 方法名 | pageRealBindUser |
| 权限注解 | 无 |
| 执行方式 | sync |
| 业务含义 | 分页查询桌面池真实绑定用户（仅已分配且非访客类型用户） |

## 入参详情

### PageQueryRequest

| 参数名 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| page | Integer | 是 | pagekit 分页参数 | 页码 |
| limit | Integer | 是 | pagekit 分页参数 | 每页条数 |
| matchArr | Match[] | 是 | 需含 classroomId 匹配条件 | 查询条件 |

## 出参详情

| 返回类型 | CommonWebResponse<DefaultPageResponse<UserListDTO>> |
|---|---|

| 字段 | 类型 | 说明 |
|---|---|---|
| itemArr | UserListDTO[] | 真实绑定用户列表 |
| total | Long | 总数 |
| itemArr[].id | UUID | 用户ID |
| itemArr[].hostId | UUID | 主机ID |
| itemArr[].userRole | String | 用户角色 |
| itemArr[].userType | IacUserTypeEnum | 用户类型 |
| itemArr[].realName | String | 真实姓名 |
| itemArr[].userDescription | String | 用户描述 |
| itemArr[].userName | String | 用户名 |
| itemArr[].phoneNum | String | 手机号 |
| itemArr[].groupId | UUID | 用户组ID |
| itemArr[].groupName | String | 用户组名称 |
| itemArr[].groupNameArr | String[] | 用户组名称数组 |
| itemArr[].userState | IacUserStateEnum | 用户状态 |
| itemArr[].createTime | Date | 创建时间 |
| itemArr[].email | String | 邮箱 |
| itemArr[].desktopNum | Integer | 绑定云桌面数量 |
| itemArr[].canDelete | Boolean | 是否可删除 |
| itemArr[].hasRecycleBin | Boolean | 回收站是否有桌面 |
| itemArr[].lock | Boolean | 是否锁定 |
| itemArr[].lockTime | Date | 锁定时间 |
| itemArr[].unlockTime | Date | 解锁时间 |
| itemArr[].openOtpCertification | Boolean | 是否开启动态口令认证 |
| itemArr[].hasBindOtp | Boolean | 是否绑定动态口令 |
| itemArr[].openCasCertification | Boolean | 是否开启外部CAS认证 |
| itemArr[].openAccountPasswordCertification | Boolean | 是否开启账号密码认证 |
| itemArr[].openHardwareCertification | Boolean | 是否开启硬件特征码 |
| itemArr[].openSmsCertification | Boolean | 是否开启短信认证 |
| itemArr[].openThirdPartyCertification | Boolean | 是否开启第三方认证 |
| itemArr[].accountExpireDateStr | String | 账户过期时间（字符串） |
| itemArr[].enableDomainSync | Boolean | 是否开启域同步 |
| itemArr[].isAssigned | Boolean | 是否已分配 |
| itemArr[].hasBindDisk | Boolean | 是否绑定磁盘 |
| itemArr[].disabled | Boolean | 是否禁用 |
| itemArr[].invalidTime | Integer | 失效时长 |
| itemArr[].isInvalid | Boolean | 是否失效 |
| itemArr[].invalidDescription | String | 失效描述 |
| itemArr[].accountExpireDate | String | 账户过期时间 |
| itemArr[].openRadiusCertification | Boolean | 是否开启RADIUS认证 |
| itemArr[].vdi1License | Integer | 是否占用VDI1授权（1/0） |
| itemArr[].vdi1LicenseDuration | CbbLicenseDurationEnum | VDI1授权持续类型 |
| itemArr[].vgpuLicense | Integer | 是否占用3D设计授权（1/0） |
| itemArr[].vgpuLicenseDuration | CbbLicenseDurationEnum | 3D设计授权持续类型 |
| itemArr[].hasBindPoolDesktop | Boolean | 是否绑定桌面池中的桌面 |
| itemArr[].hasBindAppHost | Boolean | 是否绑定静态应用主机 |
| itemArr[].openWorkWeixinCertification | Boolean | 是否开启企业微信认证 |
| itemArr[].openFeishuCertification | Boolean | 是否开启飞书认证 |
| itemArr[].openDingdingCertification | Boolean | 是否开启钉钉认证 |
| itemArr[].openOauth2Certification | Boolean | 是否开启OAuth2认证 |
| itemArr[].openPluginCertification | Boolean | 是否开启插件认证 |
| itemArr[].openRjclientCertification | Boolean | 是否开启锐捷客户端扫码 |
| itemArr[].groupPath | String | 用户组路径 |
| itemArr[].enableCustomPasswordPolicy | Boolean | 是否开启自定义密码有效期 |
| itemArr[].thirdPartyUserDisableType | ThirdPartyUserDisableType | 第三方用户禁用类型 |
| itemArr[].hasVdi1License | Boolean | 是否占用VDI1授权 |
| itemArr[].hasVgpuLicense | Boolean | 是否占用3D设计授权 |
| itemArr[].workRole | IacWorkRole | 用户工作角色 |
## 上游前置业务

### 前置1：POST /rcc/classroom/create

教室ID（通过 exact match 字段 classroomId 传入），来源为教室创建返回（由 field_map 契约映射）
## 内部处理流程

### 处理流程

1. Assert request/sessionContext 非空
2. buildAssignmentQueryContext 解析 classroomId 与权限；无权限返回空成功
3. 构造 PoolUserQueryRequest{已分配=true, enableUseRType=true, 非访客类型枚举} 调 pageQueryPoolUser
4. findBindDeskUserIdSet 取绑定桌面用户ID，convertRealBindUserList 转换并返回

## 下游消费方

### 消费1：POST /space/user/realBindUser/page

真实绑定用户ID列表（由 field_map 契约映射）
## 接口参数约束分析

| 层级 | 参数 | 规则 | 失败结果 |
|---|---|---|---|
| request | request | 非空且需含 classroomId 匹配条件 | 缺少classroomId时 Assert 失败 |

## 参数取值策略

| 参数 | 策略 | 说明 |
|---|---|---|
| page | user_input/from_query | 按业务构造 |
| limit | user_input/from_query | 按业务构造 |
| matchArr | user_input/from_query | 按业务构造 |

## 成功/失败断言基准

### 成功场景

| 场景 | 断言点 |
|---|---|
| 无权限 | $.status==SUCCESS 且 $.content.itemArr 为空 |
| 有已分配用户 | $.content.itemArr 非空 |

### 失败场景

| 场景 | 触发条件 | 断言点 |
|---|---|---|
| 权限不足 | 无授权 | 403 |

## 环境清理机制

| 接口 | 说明 |
|---|---|
| 本接口创建的资源 | 通过对应 delete 接口清理 |

## 前置状态和幂等性标注

| 维度 | 结论 |
|---|---|
| 幂等性 | high |
| 说明 | 纯查询接口 |
