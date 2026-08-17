---
version: '1.0'
# ============================================================
# 业务规则库（跨接口通用规则，编排器加载后全用例生效）
# 用途：资源依赖链(造数顺序)、操作前置状态、用例前置状态达成途径
# 编排器 orchestrator.validate_plan() 读取本文件的 front-matter
# ============================================================

# 资源依赖链：资源类型 -> 按顺序执行的接口链（造数/数据就绪顺序）
resource_chains:
  classroom:
    order:
      - POST /rcc/classroom/create
      - POST /rcc/classroom/seat/batchCreate
      - POST /rcc/classroom/image/student/create
      - POST /rcc/classroom/image/teacher/create
    note: 教室 → 座位 → 分配学生机/教师机镜像；座位创建后无桌面，分配镜像后桌面才存在
  vdi_desktop:
    order:
      - POST /rcc/classroom/create
      - POST /rcc/classroom/seat/batchCreate
      - POST /rcc/classroom/image/student/create
    note: 学生机 VDI 桌面由「座位 + 镜像分配」生成；desktop/list 查询的数据源即该链产物
  tci_desktop:
    order:
      - POST /rcc/classroom/create
      - POST /spacetci/lessonImage/student/create
      - POST /spacetci/lessonImage/teacher/create
    note: TCI 桌面由「教室 + 课程镜像分配」生成（无独立座位环节）
  strategy:
    order:
      - POST /rcc/classroom/strategy/create
      - POST /space/strategygroup/vdi/create
      - POST /space/strategy/tci/create
    note: 策略独立创建（请求 DTO 无资源外键依赖）；教室创建与镜像分配依赖策略
  seat:
    order:
      - POST /rcc/classroom/create
      - POST /rcc/classroom/seat/batchCreate
    note: 座位创建依赖教室+集群+网络+平台（BatchCreateSeatWebRequest 外键推导）
  lesson_image:
    order:
      - POST /rcc/classroom/create
      - POST /space/strategygroup/vdi/create
      - POST /spacetci/lessonImage/student/create
    note: 学生机课程镜像分配依赖教室+策略+镜像模板+集群+网络+存储池+平台（请求 DTO 外键推导）

# 操作前置状态：资源+动作 模式 -> 目标状态 + 达成途径
# （模式匹配：URL 同时含 resource 段与 action 段即命中，覆盖所有域的同类操作，无需逐接口列举）
state_prereq:
  - resource: desktop
    action: restart
    required_state: RUNNING
    source: 业务语义（本工程源码无显式状态校验，状态由底层平台处理；开机途径由 gen_business_rules.py 推导）
    achieve_via:
      - api: POST /rcc/classroom/cmrcef/lesson/start
        note: 学生桌面无独立开机接口，只能通过上课批量开机
  - resource: desktop
    action: shutdown
    required_state: RUNNING
    source: 业务语义（本工程源码无显式状态校验，状态由底层平台处理；开机途径由 gen_business_rules.py 推导）
    achieve_via:
      - api: POST /rcc/classroom/cmrcef/lesson/start
        note: 学生桌面无独立开机接口，只能通过上课批量开机
  - resource: desktop
    action: poweroff
    required_state: RUNNING
    source: 业务语义（本工程源码无显式状态校验，状态由底层平台处理；开机途径由 gen_business_rules.py 推导）
    achieve_via:
      - api: POST /rcc/classroom/cmrcef/lesson/start
        note: 学生桌面无独立开机接口，只能通过上课批量开机
  - resource: desktop
    action: forcewakeup
    required_state: SLEEP
    resource_optional: true
    source: 源码推导（RccSpaceDesktopForceWakeUpBatchTaskHandler 校验 deskState==SLEEP，STATE_NOT_SATISFIED，classroom 与 space 两域同校验）
    achieve_via: []
    note: 唤醒仅对睡眠(SLEEP)状态桌面生效；非睡眠桌面唤醒直接失败，无补步骤途径
  - resource: desktop
    action: restore
    required_state: RUNNING
    source: 业务语义（本工程源码无显式状态校验，状态由底层平台处理；开机途径由 gen_business_rules.py 推导）
    achieve_via:
      - api: POST /rcc/classroom/cmrcef/lesson/start
        note: 学生桌面无独立开机接口，只能通过上课批量开机
  - resource: desktop
    action: start
    required_state: CLOSE
    source: 源码推导（StartDesktopSPIImpl 校验桌面 CLOSE 状态）
    achieve_via: []
    note: 开机要求桌面处于关机(CLOSE)状态
  - resource: classroom
    action: lesson_start
    required_state: NONE_CLASS
    chain: false
    forbidden: [STARTING_CLASS, IN_CLASS]
    source: 源码推导（LessonService：STARTING_CLASS 重复上课禁止；IN_CLASS 同镜像禁止；IN_CLASS 不同镜像先下课再上课）
    achieve_via: []
    note: 上课要求教室非上课中；若 IN_CLASS 不同镜像需先下课
  - resource: classroom
    action: lesson_end
    required_state: IN_CLASS
    chain: false
    source: 源码语义（下课需上课中）
    achieve_via: []
    note: 下课要求教室处于上课中(IN_CLASS)
  - resource: strategy
    action: edit
    required_state: AVAILABLE
    source: 源码推导（SpaceStrategyGroupVDIValidationUtil 校验 state==AVAILABLE）
    achieve_via: []
    note: 策略编辑要求策略可用(AVAILABLE)
  - resource: strategy
    action: delete
    required_state: AVAILABLE
    source: 源码推导（删除流程先置 DELETING，操作要求 AVAILABLE）
    achieve_via: []
    note: 策略删除要求策略可用(AVAILABLE)
  - resource: classroom
    action: delete
    api: /rcc/classroom/delete
    required_state: NONE_CLASS
    forbidden: [STARTING_CLASS, IN_CLASS, ENDING_CLASS]
    source: 源码推导（ClassroomServiceImpl.checkClassroomCanDelete：非上课中才可删除；NONE_CLASS/ERROR 允许，上课状态禁止）
    chain: false
    achieve_via:
      - api: POST /rcc/classroom/cmrcef/lesson/end
        note: 教室上课中需先下课(lesson/end)才能删除
  - resource: teacher
    action: start
    required_state: CLOSE
    source: 业务语义（教师桌面启动类似桌面开机，要求关机状态；开机途径与桌面一致）
    achieve_via: []
    note: 教师桌面启动要求桌面处于关机(CLOSE)状态
  - resource: teacher
    action: end
    required_state: RUNNING
    source: 业务语义（关闭教师桌面要求桌面运行中）
    achieve_via: []
    note: 教师桌面关闭要求桌面运行中(RUNNING)
  - resource: terminal
    action: unlock
    required_state: ONLINE
    source: 源码推导（UnlockTerminalBatchTaskHandler 校验终端 OFFLINE 禁止，TERMINAL_UNLOCK_TERMINAL_OFFLINE）
    chain: false
    achieve_via: []
    note: 终端解锁要求终端在线(ONLINE)；离线终端操作直接失败，无接口可达成上线
  - resource: terminal
    action: shutdown
    required_state: ONLINE
    source: 业务语义（终端关机/重启/唤醒要求终端在线，参照解锁校验）
    chain: false
    achieve_via: []
    note: 终端操作要求终端在线(ONLINE)；无接口可达成上线
  - resource: terminal
    action: wake
    required_state: ONLINE
    source: 业务语义（参照终端解锁校验）
    chain: false
    achieve_via: []
    note: 终端操作要求终端在线(ONLINE)；无接口可达成上线
  - resource: terminal
    action: restart
    required_state: ONLINE
    source: 业务语义（参照终端解锁校验）
    chain: false
    achieve_via: []
    note: 终端操作要求终端在线(ONLINE)；无接口可达成上线

# 语义匹配修正规则：_semantic_match 基础打分（动作+2/实体+2）后叠加 delta
# 字段：if_entities=用例句须命中的实体词（URL 段）；url_any/name_any=接口 URL/名称含任一词才命中；
#       name_none=名称含任一词则排除（例外条件）；delta=命中加减分
# 新增反规则只需在此追加条目，无需修改编排器代码
semantic_rules:
  - if_entities: [cluster]
    name_any: [存储池, StoragePool, storagePool]
    delta: -10
    note: 集群语义不匹配存储池接口（语义冲突重罚）
  - if_entities: [storagePool]
    name_any: [集群, Cluster, cluster]
    delta: -10
    note: 存储池语义不匹配集群接口（语义冲突重罚）
  - if_entities: [network]
    name_any: [镜像, Image, image]
    name_none: [Assigned]
    delta: -10
    note: 网络语义不匹配镜像接口（getAssignedClusterAndNetwork 例外）
  - url_any: [/dashboard/statistics/]
    delta: -10
    note: 统计接口不是业务查询
  - if_entities: [cluster]
    url_any: [/rco/user/obtainComputeClusterList]
    delta: 5
    note: 集群优先 RDCD 侧接口（不穿透 CBB，更稳定）
  - if_entities: [cluster]
    url_any: [/space/cluster/]
    delta: -3
    note: Space 侧集群接口穿透 CBB，降权
  - if_entities: [storagePool]
    url_any: [/rcc/]
    delta: 3
    note: 存储池优先 RCC 侧接口
  - if_entities: [storagePool]
    url_any: [/space/storagePool/]
    delta: -3
    note: Space 侧存储池接口穿透 CBB，降权

# 用例前置条件：前置步骤关键词 -> 需满足的资源状态 + 达成途径
# （校验用例前置声明是否被编排步骤覆盖，不满足时自动补达成步骤）
case_prereq:
  - keyword: 运行中
    resource: desktop
    required_state: RUNNING
    achieve_via:
      - api: POST /rcc/classroom/cmrcef/lesson/start
        note: 前置要求桌面运行中；若已分配镜像但处于关机，先上课开机
  - keyword: 已分配
    resource: desktop
    required_state: ASSIGNED
    achieve_via:
      - api: POST /rcc/classroom/image/student/create
        note: 前置要求已分配镜像；若只有教室/座位而无镜像，先分配学生机镜像
---
# 业务规则库（Business Rules）

本文件是**跨接口通用业务规则**的集中定义，供编排器（`orchestrator.validate_plan`）加载，用于：
1. **依赖顺序校验**：操作/查询某资源前，其资源依赖链（`resource_chains`）中的前置接口必须先执行
2. **前置状态校验**：操作接口（`state_prereq`）要求目标资源处于特定状态（如桌面 RUNNING），不满足时按 `achieve_via` 自动补步骤
3. **用例前置覆盖校验**：用例前置条件（`case_prereq`）声明的状态必须被编排步骤达成，否则自动补

## 通用规则要点

### 资源依赖链（造数顺序）
- **教室 → 座位(batchCreate) → 分配镜像(image/student|teacher/create) → 桌面可用**
- 座位本身**不含桌面**，桌面由「座位 + 镜像分配」生成——`desktop/list` 的查询结果依赖该链完成
- TCI 桌面由「教室 + 课程镜像分配」生成（无座位环节）

### 桌面生命周期状态机
```
教室创建 → 座位创建 → 分配镜像 → 桌面存在(关机 OFF)
                                    ↓ 上课(cmrcef/lesson/start)
                                 桌面运行中(RUNNING) → 重启/关机/唤醒/取消报障
```
- 学生桌面**无独立开机接口**，只能通过上课（`cmrcef/lesson/start`）批量开机
- 教师桌面可经 `teacher/terminal/wake` 唤醒

### 操作前置状态
| 操作 | 前置状态 | 达成途径 |
|---|---|---|
| desktop/restart、shutdown、powerOff、forceWakeUp、restoreVDIImage | 桌面 RUNNING | 上课 cmrcef/lesson/start |
| desktop/tci/restart、tci/shutdown | 桌面 RUNNING | 上课 cmrcef/lesson/start |

### 维护约定
- 新增资源类型/操作前置状态时，在 front-matter 对应节追加即可，**无需修改编排器代码**
- 编排器自动补的步骤会标记 `_auto_by_rules: true`，可在编排计划中人工确认
