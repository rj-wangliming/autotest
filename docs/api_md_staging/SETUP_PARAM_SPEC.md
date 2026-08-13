# 接口文档参数引用规范（setup 数据绑定语法）

> 版本：1.0（2026-08）
> 用途：让接口文档的 `setup` / `request.body` 支持**测试用例参数驱动**——自动化引擎读文档时，能把测试输入参数（如 `classroom_name`）和前置步骤产出（如 `imageId`）绑定到请求字段，实现"输入测试用例 → 自动执行"。

## 1. 参数来源

| 引用语法 | 含义 | 示例 |
|---|---|---|
| `${param.xxx}` | 测试用例输入参数（由用例/数据文件提供，如 python 变量、json、yaml） | `${param.classroom_name}` → 教室名 |
| `${prev.<step_name>.output.<var>}` | 前置 setup 步骤的 extract 产出变量（跨步骤绑定） | `${prev.assign_image.output.imageId}` → 前置步骤提取的镜像 ID |
| `${context.xxx}` | 全局上下文（登录 token、环境 base_url 等） | `${context.token}` |

**优先级**：`${prev.*}` > `${param.*}` > `${context.*}`（后者的值覆盖前者的同名默认，若有冲突）。

## 2. setup 步骤结构（两种格式等价）

### 2.1 简化格式（dict）
```yaml
- name: query_classroom
  api: POST /rcc/classroom/select
  request:
    body:
      searchKeyword: ${param.classroom_name}   # ← 参数引用
  extract:
    classroomId: $.content[0].classroomId       # ← 产出变量（供 ${prev.*} 引用）
  purpose: 按名称查询教室
```

### 2.2 完整格式（list，支持多 extract / assert）
```yaml
- name: query_usb_types
  api: POST /space/deskStrategy/getSupportUsbTyp
  method: POST
  request:
    body: {}
  extract:
    - var: usbTypeIdArr
      from: response
      jsonpath: $.content[*].id
  assert:
    - path: $.status
      op: eq
      value: SUCCESS
```

## 3. request.body 字段值支持参数引用

`request.body.<字段>.value`（完整格式）或 `request.body.<字段>`（简化格式为标量时）可写：
- 字符串：`"${param.classroom_name}"` → 用参数值替换
- 常量：`"EST"` → 原样
- 引用数组：`["${param.usbTypeIdArr}"]` → 参数数组展开

**示例**（vdi/create 策略名 + 配置）：
```yaml
- name: create_strategy
  api: POST /space/strategygroup/vdi/create
  request:
    body:
      name:
        value: ${param.strategy_name}        # 用例参数
      cpu:
        value: 4
      memory:
        value: 8192
      systemSize:
        value: 80
      strategyType:
        value: VDI
  extract:
    deskStrategyId: $.content.id             # 产出策略 ID
  polling:                                    # 异步则轮询
    api: POST /space/strategygroup/vdi/detail
    params:
      id: ${content.id}
```

## 4. "名称 → ID"查询（用例给名称，接口要 ID）

查询类 setup 用**过滤条件**按名称精确取 ID，而非无条件 `itemArr[0]`：

```yaml
- name: get_image_by_name
  api: POST /rcc/classroom/image/list
  request:
    body:
      crId: ${prev.create_classroom.output.classroomId}
      teaTerminal: true
      searchKeyword: ${param.student_image_name}   # 按名称过滤
      matchArr:                                     # 精确匹配（若接口支持）
        - fieldName: imageName
          matchType: EQUAL
          value: ${param.student_image_name}
  extract:
    imageId: $.content.itemArr[0].id               # 过滤后取第一个（名称唯一）
  assert:
    - path: $.content.itemArr
      op: not_empty
```

## 5. 执行接口绑定前置产出

执行步骤（如 teacher/strategy/edit）的请求字段引用**前置步骤产出的 ID**，而非重新查询：
```yaml
- name: change_strategy
  api: POST /rcc/classroom/image/teacher/strategy/edit
  request:
    body:
      classroomId:
        value: ${prev.create_classroom.output.classroomId}
      imageId:
        value: ${prev.assign_image.output.imageId}       # ← 复用前置分配的镜像 A
      deskStrategyId:
        value: ${prev.create_strategy.output.deskStrategyId}  # ← 复用前置创建的策略 B
      clusterId:
        value: ${prev.get_cluster.output.clusterId}
      platformId:
        value: ${prev.get_cluster.output.platformId}
```

## 6. 验证步骤断言

验证接口（如 cloudDesktop/list）出参用 JSONPath 断言配置一致性：
```yaml
- name: verify_desktop_config
  api: POST /rcc/space/classroom/cloudDesktop/list
  request:
    body:
      classroomId:
        value: ${prev.create_classroom.output.classroomId}
  assert:
    - path: $.content.itemArr[0].cpu
      op: eq
      value: ${param.expected_cpu}
    - path: $.content.itemArr[0].memory
      op: eq
      value: ${param.expected_memory}
```

## 7. 自动化引擎读取顺序

1. 读测试用例参数（python 变量 / json / yaml）→ 存入 `${param.*}` 上下文
2. 遍历 `setup` 步骤：
   a. 替换 request.body 中的 `${param.*}` / `${prev.*}` → 发送请求
   b. 按 extract 提取产出 → 存入上下文（供 `${prev.<step>.output.<var>}` 引用）
   c. 若声明 polling → 轮询至终态
3. 主请求：用 setup 产出构造 body
4. 断言：读 response 按 assertions / assert 校验

## 8. 转换规则（旧格式 → 新格式）

- `extract: {var: jsonpath}` → `extract: [{var, from: response, jsonpath}]`（完整格式）
- `request.body: {field: {type, value}}` → 已兼容（value 支持 ${param.*}）
- setup 无 request 的查询步骤 → 补 `request.body` 过滤参数（searchKeyword/matchArr）使按名称精确取 ID
- setup 无条件 `itemArr[0]` 且字段可在请求体指定 → 补 `${prev.*}` 绑定（优先复用前置产出）

## 9. setup 幂等标记（多步用例防重复创建）

**问题**：每个接口的 setup 假设"从头开始"，若前置步骤已创建资源（教室/座位/策略），执行接口的 setup 再执行 create 会**重复创建**（名称冲突报错）。

**解决**：setup 步骤声明幂等标记，引擎据此决定"已存在则跳过/删除重建"：

### idempotent 三值枚举

| 值 | 含义 | 引擎行为 |
|---|---|---|
| `true` | 存在则**复用**（跳过创建，直接取 ID） | 先按名查重 → 存在则跳过；不存在则创建 |
| `false` | **始终执行**（不查重，可能冲突报错） | 直接创建（适合预期无冲突的步骤） |
| `recreate` | 存在同名则**先删除再创建**（干净重置） | 先按名查重 → 存在则调**对应删除接口**删掉 → 再创建 |

> `recreate` 用于"用例要求全新资源"（如每次跑用例都要干净的教室/策略），避免上轮遗留数据影响断言。

### 示例

```yaml
# 复用模式：教室已存在则跳过（多步用例复用前置）
- name: create_classroom
  api: POST /rcc/classroom/create
  idempotent: true
  request:
    body:
      classroomName: ${param.classroom_name}

# 重置模式：策略存在则先删再建（用例要求全新策略，验证创建流程）
- name: create_strategy
  api: POST /space/strategygroup/vdi/create
  idempotent: recreate          # ← 先删再建
  delete_api: POST /space/strategygroup/vdi/delete   # 对应的删除接口（按名查到的 ID 作为删除入参）
  request:
    body:
      name: ${param.strategy_name}
```

### 引擎执行规则

1. `idempotent: true` → 按该接口过滤参数（searchKeyword/matchArr）查重
   - 查到 → 跳过创建，直接走后续 extract（或从查询结果取 ID）
   - 未查到 → 执行创建
2. `idempotent: recreate` → 按名查重
   - 查到 → 调 `delete_api`（入参=查到的资源 ID）删除 → 再执行创建
   - 未查到 → 直接创建
3. `depends_on_existing: true` → 跳过（资源已由前置/环境提供）
4. `idempotent: false` / 无标记 → 始终执行

**recreate 的 delete_api 约定**：
- 创建步骤声明 `delete_api`（对应删除接口 URL），引擎删完后重建
- 删除入参：按名查到的资源 ID（如教室→classroomId、策略→id）
- 删除接口本身也应轮询（若异步）至终态，再创建

**默认建议**：
- 创建类步骤（create/add/assign）→ 默认 `idempotent: true`；**用例要求全新资源时用 `recreate`**
- 查询类步骤（list/select/get）→ 默认无标记（始终执行，用于取 ID）
- 操作类步骤（shutdown/delete/edit）→ 默认无标记（始终执行）

## 10. 用例参数清单（自动提取）

每个接口文档的 front-matter 头部应包含 `params` 段，列出该接口执行所需的**用例参数**（自动化引擎据此校验测试输入是否齐全）：

```yaml
params:
  required:
    - name: classroom_name
      desc: 教室名称
      used_by: request.body.classroomName / setup.create_classroom
    - name: strategy_name
      desc: VDI 策略名
      used_by: setup.get_strategy
  optional:
    - name: cluster_name
      desc: 集群名（缺省时取第一条）
      used_by: setup.get_cluster
```

**自动生成**：扫描文档中所有 `${param.xxx}` 引用 → 汇总为 params 段（required=无默认值、optional=有"取第一条"兜底）。


## 11. 登录约定（loginAdmin 内置）

`POST /rco/admin/loginAdmin` 是**平台级公共登录接口**（RCC-Space 工程外、所有子模块共用），**不生成独立接口文档**，由自动化框架**内置实现**（引擎硬编码处理，无需从 MD 文档读取）。

### 内置登录步骤

```yaml
# 每个接口文档 setup 第一步的标准登录步骤（已存在于 211 个文档）
- name: login
  api: POST /rco/admin/loginAdmin
  purpose: 管理员登录（框架内置，引擎自动处理）
```

引擎遇到 `api == POST /rco/admin/loginAdmin` 的 setup 步骤时：
1. **不查接口文档**，直接按内置登录逻辑执行
2. 请求体由环境配置提供：`{ "userName": "${context.admin_user}", "password": "${context.admin_password}" }`（或 BASE_URL/API_KEY 配置注入）
3. 从响应提取 token（**登录响应 JSONPath 由环境配置 `login_token_path` 指定**，默认 `$.content.token`；因响应 DTO 在外部平台 jar，允许通过环境配置覆盖路径，无需改文档）
4. token 注入**全局上下文** `${context.token}`，后续所有请求自动带鉴权头
5. token 失效/401 时：自动重新登录一次再重试原请求（会话过期自愈）

### 配置项（环境变量 / 配置文件）

| 配置 | 默认值 | 说明 |
|---|---|---|
| `ADMIN_USER` | - | 管理员用户名 |
| `ADMIN_PASSWORD` | - | 管理员密码 |
| `LOGIN_TOKEN_PATH` | `$.content.token` | 登录响应中 token 的 JSONPath（外部 DTO 变化时可覆盖） |
| `AUTH_HEADER` | `Authorization` | 鉴权请求头名称 |
| `AUTH_TOKEN_PREFIX` | `Bearer ` | token 前缀（如无则空） |

### 统一好处

- 211 个文档的 login 步骤不再需要各自维护请求/响应细节（当前 1 个文档的 `$.content.token` extract 标注"待验证"可移除）
- 登录响应 DTO 在外部 jar（无法从 RCC-Space 源码验证）→ 引擎用配置化 token 路径，规避文档无法覆盖外部接口的盲区
- 会话过期自动重登，提升长链路用例稳定性


## 12. 用例输入模板（降低 AI 解析歧义）

用例文本按固定分段标签书写，每段内"动作+实体+约束"短句分行，显著降低自然语言歧义：

```text
【前置】
1. 创建教室（教室名=${param.classroom_name}）
2. 分配 VDI 镜像（镜像=${param.student_image_name}）到教师终端（教室=${prev.step1.output.classroomId}）
3. 创建 VDI 策略（策略名=${param.strategy_name}；CPU、内存、系统盘与镜像A不同）

【操作】
1. 修改教师机课程镜像（镜像=${param.student_image_name}）的云桌面策略为 ${param.strategy_name}

【预期】
1. 操作成功：$.status=="SUCCESS"
2. 云桌面（教室=${prev.step1.output.classroomId}）的 CPU、内存、系统盘 == 策略 ${param.strategy_name} 的配置
```

### 模板规则

| 段 | 动作词 | 实体 | 约束/产出 |
|---|---|---|---|
| 【前置】 | 创建/分配/存在/使用已有 | 实体类型+名称 | 约束条件；产出变量（${prev.*} 引用源） |
| 【操作】 | 修改/删除/启动/关闭/查询 | 实体+目标 | 操作参数 |
| 【预期】 | 成功/失败/等于/一致 | 断言目标 | $.status / 字段比较 |

- 实体命名显式（"策略B"→ 用名称参数 ${param.strategy_name}，而非"B"）
- 产出变量在【前置】中声明（outcome_variable），【操作】【预期】用 ${prev.*} 引用
- 编译期校验：预期结果引用的实体必须在【前置】有产出，缺失则提示补充
