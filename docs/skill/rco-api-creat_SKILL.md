---
name: rco-api-creat
description: Analyze Java backend API endpoints and generate comprehensive interface analysis documents in Feishu wiki. Use when the user asks to analyze an API endpoint, trace business relationships, or generate interface documentation. Covers protocol format, dependency chains, parameter strategies, assertion baselines, cleanup mechanisms, and idempotency analysis across 6 dimensions (P0-P2).
---

# API Interface Analysis

Analyze Java backend API endpoints and generate structured analysis documents in Feishu wiki, covering 6 dimensions: protocol format, interface relationships, parameter strategies, assertion baselines, cleanup mechanisms, and idempotency.

## When to Use

- User asks to analyze an API endpoint (e.g., "分析这个接口 rcdc/rcc/space/user/update")
- User asks to generate interface documentation for a Java project
- User asks about endpoint business relationships (upstream/downstream)
- User asks to add a new endpoint analysis to an existing Feishu document
- User asks to batch-generate docs for many endpoints (e.g. "these 20 URLs → interface docs") — use the Batch Deep-Doc workflow below

## Prerequisites

1. Java project path — the backend project containing the endpoint
2. Endpoint URL — the API path to analyze (e.g., `/rcc/space/user/update`)
3. Feishu wiki URL — the target document (must be a docx-type wiki node)
4. lark-cli installed and authenticated (check: `lark-cli auth status`)
5. **Actual request JSON** — the single source of truth for input parameters (see Step 2)
6. For verification-level completeness: actual **response JSON** samples (success + failure) for assertion baselines
7. Java project path MUST be accessible for code cross-checks (DTO fields, serialization targets, validation layers)

## Analysis Workflow (14 Steps)

### Step 1: Locate the Endpoint

Search for the URL path in `@RequestMapping`/`@Path` annotations. Read the controller method to get: URL, HTTP method, return type, permission annotations (`@EnableAuthority`, `@OneTimeTokenRequired`), input parameter class name.

**Line number citation rule** — when the document cites a code line (e.g., `RccSpaceController.java #764`), point to the **method signature line** (where `public ... methodName(` begins), NOT the `@ApiOperation` annotation line above it (annotations can sit 2-3 lines earlier). Also verify the class-level `@RequestMapping` prefix + method-level path combine to exactly the documented URL before writing it down.

### Step 2: Extract Input Parameters

**SOURCE OF TRUTH = actual request JSON** (a real captured request body for this endpoint). The DTO class is a *supplement*, NOT the primary source.

1. **Get the actual request JSON first** — sources in priority order:
   - A captured/pasted real request body (user-provided, browser devtools, packet capture)
   - `space-test` module: `TestDataFactory` (e.g. `getDefaultStrategyGroupData()` returns a real `strategyGroupFacadeStr` string), `*Data.java` test fixtures
   - Code that constructs the request DTO then serializes it (`JSON.toJSONString(...)`)
   - As last resort, the DTO class field list
2. **Extract top-level fields from the real JSON** — these are the fields automation will actually send. Record each field's real type and a real example value.
3. **CRITICAL: Check for nested JSON string fields** — fields of type `String` named like `*FacadeStr`/`*JsonStr` contain JSON with nested parameters. Trace the deserialization target class (e.g., `JSON.parseObject(field, StrategyGroupFacadeDTO.class)`) and extract ALL nested fields **from the actual JSON string**, not from the DTO.
4. **Diff top-level JSON fields vs DTO fields, in BOTH directions**:
   - JSON has but DTO lacks → **framework-injected fields** (e.g. `business: "RCC"` is a request-framework field not on `SpaceDeskStrategyGroupVDI`). MUST include in doc — automation needs them.
   - DTO has but JSON lacks → **optional/DTO-only fields** (e.g. `enableGpu`, `vgpuItem`, `vgpuModel` exist in `VDIDeskStrategyDTO.java` but are NOT sent in the real request — vGPU is expressed by top-level `vgpuType`+`vgpuExtraInfo`). Mark them as "⚠️ DTO 有、请求不传" or exclude from the request table entirely.
5. **Same diff for nested nodes** (e.g. the `vdi` node inside `strategyGroupFacadeStr`): compare the real JSON node fields vs the nested DTO fields; keep only what the real JSON sends.
6. **Use script to extract fields** — do NOT rely on manual scanning for completeness. Run a grep/AST extraction on the target DTO, then cross-check against the real JSON.
7. **Do NOT cross-reference with Python test framework for completeness** — the test framework's parameters are NOT complete; using it as a validation source creates false confidence and misses parameters.

### Step 3: Extract Output Parameters

1. Read the response DTO class — list EVERY field with type and description, INCLUDING inherited fields (parent classes). Do NOT merge/compress related fields into one line (e.g. `vdiDesktopId/vdiDesktopIp/...` or `terminalId/terminalName/terminalMac/terminalIp`) — each field gets its own row.
2. For framework types (BatchTaskSubmitResult, etc.), infer fields from Java builder calls and response DTO definitions — use the REAL framework field names (`itemArr`/`total` from `PageQueryResponse.getItemArr()`/`getTotal()`, NOT the guessed `items`), not intuition.
3. Include response wrapper fields (status, message, content, msgKey, msgArgArr) and the wrapper hierarchy (`content.itemArr`, not flat `itemArr`) so orchestrators know the JSONPath. The SK `DefaultWebResponse` wrapper is EXACTLY these five fields — it has NO `code`/`retCode`/`resultCode`. NEVER invent a wrapper field; if a sub-agent wrote `code`, it is a fabrication — remove it and use the standard five.
4. **HARD RULE: response fields must be complete, per-field, and REAL** — (a) list every source DTO field (incl. inherited), never merge rows (`vdiDesktopId/vdiDesktopIp/...`); (b) use REAL framework field names (`itemArr`/`total`, not guessed `items`); (c) the wrapper is the standard five (`status/message/msgKey/msgArgArr/content`), never fabricated `code`/`retCode`/`resultCode`; (d) describe conditional content branches (e.g. "普通分配 content 空 / 跨存储 content=BatchTaskSubmitResult"). Automation reading `$.content.xxx` and `$.status` must resolve every real field.
5. **Mechanical check after generation**: grep the 出参详情 section — any row whose field name contains `/` (multiple fields merged) is a bug; fix by expanding from the source DTO. Cross-check field COUNT against the DTO class (`grep -c "private" DTO.java`).

### Step 4: Trace Upstream Dependencies

1. For every query-type setup step that extracts an ID via `[0]`, add the name-filtering params (searchKeyword/matchArr/exactMatchArr with the REAL field name from the DTO — e.g. `matchArr=[{fieldName: classroomName, EQUAL, ${param.classroom_name}}]`, seat/list uses `exactMatchArr=[{name: desktopName, valueArr: [${param.desktop_name}]}]`). Without the filter the step takes the FIRST arbitrary record, breaking use-case fidelity. If the interface has no name field, mark the step purpose with "取第一条（无名称过滤）".
2. **Producer-consumer closure**: for every create/add/assign endpoint (a producer), its success assertion must assert the produced ID (`$.content.id` or `$.content.taskId` when async) AND it must have polling if async; then check that downstream consumers either re-query by name (documented in their setup) or reference `${prev.*}`. A producer whose ID is never asserted or never consumed is a broken chain.

1. Identify which parameters are IDs that must come from other APIs
2. Search for which endpoints CREATE the data this endpoint reads
3. Build the dependency chain: `创建A → 创建B → 当前接口`

### Step 5: Trace Downstream Consumers

1. Search for all callers of the same API/service methods
2. Categorize: HTTP endpoints (other controllers), SPI consumers (system-internal triggers)

### Step 6: Analyze Internal Processing Flow

1. Read the service implementation — trace step by step
2. For batch task handlers, read `*BatchHandler.processItem()`
3. Document: what API/DAO is called, what validation is performed, what database operations happen

### Step 7: Analyze Parameter Constraints

1. DTO annotations — `@NotNull`, `@Range`, `@Size`, `@Pattern` (basic)
2. Controller method body — conditional branches (`if (request.getXxx() == true)`)
3. Validation helpers — search for `validate*`, `check*`, `verify*` methods
4. Extract: feature gate constraints, conditional requirements, cross-parameter validation, value range checks
5. **CRITICAL: verify annotations are actually enforced** — if the Controller method has NO `@Valid`/`@Validated` annotation (only `Assert.notNull`), then DTO `@NotNull`/`@Range`/`@Pattern` are NOT enforced. Document the real enforcement layer (controller asserts / service `validate*` methods / `checkVDIParamAvailable` etc.) and mark unenforced annotations as such. Do NOT copy DTO annotation constraints blindly.
6. Only include constraints specific to THIS interface

### Step 8: Analyze Parameter Value Strategies

1. For EVERY required field in request.body, define HOW the value is obtained — the doc is not complete until each required field has one of: `${param.xxx}` (test input), `${prev.<step>.output.<var>}` (upstream step output), a fixed enum/default value, or a `generated_by: config_generator` marker. A required field with NO value source breaks automation (the engine doesn't know what to send).
2. **Config generation rules** for numeric specs: read the constraint (`@Range`) for legal bounds and step — cpu(1-64, step 1), memory(1024-262144, align to 2048/4096/8192), systemSize(0-2048, ≥ image template minimum). "different from X" = ±1 step or ×2 within bounds; if X is at the limit, report "cannot generate a legal different config" instead of emitting an invalid value.
3. ID-type fields (crId/classroomId/clusterId/platformId/storagePoolIdList/networkId) must bind to the actual setup step that produces them — `${prev.get_cluster.output.clusterId}` — and the setup MUST contain that query step (add get_cluster/get_storage_pool/get_network to image-assignment docs if missing). Mechanical check: any `${prev.X.output.Y}` whose step X is not in setup, or whose variable Y is not in that step's extract, is a dangling reference — 0 allowed.

For each parameter, determine: `from_upstream` (API response), `from_query` (query API), `full_coverage` (full list, server diffs), `constructed` (manually assembled), `random_uuid`, `from_config`, `enum_value`, `fixed_value`.

### Step 9: Analyze Assertion Baselines

1. Read standard response format (CommonWebResponse fields)
2. List success scenarios with conditions and assertion points
3. List failure scenarios with trigger conditions and error keys (from `BusinessException` keys)
4. **Verify each failure scenario exists in code** — a documented failure (e.g. "systemSize out of range → checkVDIParamAvailable") may NOT exist if the validation method does not actually check that field. Trace the validation method body before asserting the failure case.
5. **Assertions MUST be HTTP-response-level, never audit-log keys (HARD RULE)** — the assertion point must describe what the HTTP RESPONSE returns: `status==SUCCESS/ERROR`, `msgKey==...`, `content.taskId 非空`, `返回 ...`, `抛 ...Exception`. NEVER assert "记录 XX 审计日志" (`auditLogAPI.recordLog(...)`) — that is a server-side side effect invisible in the response; an assertion on it is useless to automation. When extracting from the method body, distinguish `DefaultWebResponse.Builder.success/fail(...)` (the response) from `auditLogAPI.recordLog(...)` (internal logging) — the former is the assertion, the latter is NOT.
6. **After generating, run a mechanical check** — grep every doc's 成功/失败断言基准: any assertion point that ONLY says "记录 XX 审计/日志" (no `status/msgKey/返回/抛/SUCCESS/ERROR/taskId`) is a generation bug; fix it to the real response status+msgKey by reading the Controller's `DefaultWebResponse.Builder.success/fail` calls.

### Step 10: Analyze Cleanup Mechanism

1. Find the delete endpoint for the created resource
2. Read delete handler's validation logic
3. Document cleanup chain order and failure handling
4. Include force-delete options if available

### Step 11: Analyze Idempotency

1. Check for distributed locks (`LockableExecutor`, `executeWithTryLock`)
2. Check for name uniqueness validation
3. Determine: fully idempotent (read-only) / data-level idempotent (diff-based) / non-idempotent (throws on duplicate)

### Step 12: Cross-Verify the Output (mandatory)

Before writing to Feishu, do a second independent reverse-check of the generated document's **factual claims** (diagram assertions, formulas, class names, field names, downstream paths, processor step names, cited line numbers, input field lists):

1. For every **diagram assertion** (formulas like `free = desktopNum - running - fault`, entity names, field names), grep the actual code and confirm it matches. Do NOT infer from business intuition — e.g. `close` may be `desktopNum - running` while `free` comes from an overview value; a view entity (`RccViewSpaceEntity`) may be queried where you assumed an entity class.
2. For every **downstream/upstream endpoint path**, confirm the class-level `@RequestMapping` + method-level path concatenation exists in a real controller. A path that "sounds right" (e.g. `/rcc/classroomImage/assign`) may not exist — the real entry may be `/rcc/classroom/image` with `/teacher/create`, `/student/create`.
3. For every **Taskflow/BatchHandler step name**, read each processor's actual class and comment (`registry.add(...)` order + processor class) instead of naming steps from what they "should" do (e.g. steps may actually be: push to platform / create platform relation / save locally / add data permission, not "save basics / save VDI details / save USB mapping / save nested JSON").
4. For every **method attribution**, distinguish API interface methods (e.g. `SpaceClassroomPoolUserMgmtAPI.getDeskPoolAllocateInfoDTO`) from SPI implementation public methods (e.g. `PlatformDeskSPIImpl.getDesktopPoolAssignResultDTO`). Do not list API methods as if they were SPI methods.
5. **Re-diff the input field table against the actual request JSON one last time** — every field in the doc's request table must be in the real JSON (or explicitly marked as DTO-optional), and every field in the real JSON must be in the doc's table.
6. Record the cross-check result (each claim: verified / corrected) — e.g. an appended "交叉验证补充" section — so readers can see the output was independently confirmed.

### Step 13: Three-Way Cross-Review (code × document × actual JSON)

When actual request JSON is available, do a systematic three-way review — this is the highest-value check and catches everything Steps 1-12 miss:

1. **Top-level field three-way alignment** — for every field in the actual request JSON: (a) does the request DTO (+ its parent classes) have a matching field with matching type? (b) is it listed in the doc's input table? (c) is it in the md front-matter? Diff ALL THREE directions:
   - JSON has but DTO lacks → framework-injected / front-end pass-through fields (e.g. `business:"RCC"` is framework-injected; `usbTypeIdArr`, `enableClipboard`, `powerPlan` exist in real JSON top-level but have NO field on the request DTO — they are front-end pass-through, server reads them only via `strategyGroupFacadeStr.vdi`)
   - DTO has but JSON lacks → DTO-only/optional fields (e.g. `id`, `haPriority`, `studentAccountPreName` are never in the minimal request)
2. **Nested node three-way alignment** — for each nested JSON node (e.g. `vdi` inside `strategyGroupFacadeStr`): same three-way diff against the actual deserialization target DTO.
3. **CRITICAL: identify the REAL deserialization target, not an assumed one** — trace `JSON.parseObject(str, Xxx.class)` in the API impl (`SpaceDeskStrategyGroupVDIAPIImpl.java:103-105` → `StrategyGroupFacadeDTO` whose `vdi` is `VDIStrategyDTO`, NOT `VDIDeskStrategyDTO`). The wrong DTO makes 8+ fields look "missing" and corrupts the whole review. Always grep the actual `JSON.parseObject` / `JSON.toJSONString` call site.
4. **Type/default cross-check** — spot-check 10 representative fields across JSON type vs Java type vs doc type (e.g. `memory` is Integer at top level but Double in vdi node; `usbTypeIdArr` is string[] in JSON but UUID[] in DTO).
5. **Ghost-field detection** — fields in the doc that exist in neither the real JSON nor the correct DTO (e.g. `enableGpu` in the vdi section: real vdi node has no such field; vGPU is expressed by top-level `vgpuType`+`vgpuExtraInfo`). Mark them as ghost fields; automation must NOT construct/assert them.
6. **Naming-layer check** — doc may use snake_case while real JSON uses camelCase; automation keys MUST be camelCase (server Jackson/fastjson maps camelCase only). snake_case is display-only.

### Step 14: Automation-Consumability Audit (mandatory before handoff)

Assess whether the generated doc is sufficient FOR AUTOMATION (not just for humans):

1. **Request construction layer** — top-level fields and nested nodes must EXACTLY match the real request JSON (0 missing, 0 extra). If no real JSON: mark as "推断未验证".
2. **Assertion layer (the usual gap)** — the response wrapper + business body must be based on a REAL response sample; if only inferred from DTO/echo, mark: "出参基于回显推断，真实响应未验证". msgKey/error codes likewise need real-response verification.
3. **Orchestration layer** — setup `extract.jsonpath` must be verified against real upstream API responses (inferred jsonpath breaks the setup chain).
4. **Polling/cleanup/idempotency** — verify the polling endpoint and terminal states match reality; cleanup pre_check and retry policy must be coherent.
5. **Impact classification** — tag each gap: 🔴 blocks automation (request can't be sent / always fails: wrong keys, ghost fields, missing required/framework fields, wrong nested structure, wrong enum values) / 🟡 indirect (request OK but assertion/orchestration wrong: unverified response, unverified msgKey, unverified jsonpath) / 🟢 doc-only (line numbers, DTO-only optional fields, field order).
6. **Fallback ladder when real JSON is unavailable** (in priority order): ① code-construction inference (Controller @RequestBody DTO + `@JsonInclude(NON_NULL)` → null fields not sent; `FAIL_ON_UNKNOWN_PROPERTIES=false` → extra fields ignored) ② space-test TestDataFactory fixtures (approximate — may have MORE fields than real requests) ③ front-end API calls / YApi-Apifox-Postman collections / gateway logs ④ runtime capture once per endpoint (Charles/Fiddler/devtools) ⑤ doc marking + lenient strategy (don't send optional fields; mark "推断未验证").
7. **Mechanical front-matter validation (STRICT, mandatory)** — lenient parsing hides real bugs. Every generated doc MUST pass: (a) file starts with a lone `---` line; (b) front-matter YAML parses via `yaml.safe_load` on the block between the FIRST `---` and the NEXT standalone `---` line; (c) NO delimiter glue — grep `---# ` (front-matter end marker glued to the body `# POST ...` title) anywhere in the file, and no `------` runs; (d) all data-layer keys present (`api/request/response/setup/upstream/downstream/assertions/cleanup/idempotency`, empty arrays OK for query-only endpoints; `request` may be omitted for pure query/statistics endpoints). Glue like `---# POST` makes `split('---\n',2)[1]` still return a block but `safe_load` fails on it — the check must use the STANDALONE `---` marker, not a substring split. Batch-check: `grep -rn "---#" *.md` must return 0, and a strict safe_load loop over all docs must report 0 failures.

## Batch Deep-Doc Workflow (batch deep-analysis + generation)

For generating a set of endpoints at the SAME depth as a reference "golden" doc (e.g. vdi/create), follow this pipeline. A shallow auto-skeleton is NOT enough — align every endpoint to the golden standard.

### 1. Define the golden template first

Extract the reference doc's exact structure (front-matter keys + body sections) and treat it as the target: front-matter (`version/api/setup/request/response/polling/upstream/downstream/constraints/assertions/cleanup/idempotency/prereq_state`) + body sections (`依赖关系全景图`/`接口基本信息`/`入参详情`/`出参详情`/`上游前置业务`/`内部处理流程`/`下游消费方`/`接口参数约束分析`/`参数取值策略`/`成功失败断言基准`/`环境清理机制`/`前置状态和幂等性标注`).

### 2. Parallel sub-agent deep extraction (the heavy lifting)

Do NOT hand-write each doc. Dispatch parallel read-only sub-agents, one per business domain (e.g. classroom / seat / strategy+desktop / lessonImage), each instructed to:

- Read the Controller method body + the BatchHandler's `processItem()` + StateHandler/StateProcessor transitions
- Extract per endpoint: request DTO fields (with inheritance/annotations/comments), response body fields, upstream (API calls with produces/purpose), flow steps, batch_handler steps (REAL processItem steps, not invented), downstream consumers, constraints (level/field/rule/failure), assertions (success/failure with BusinessException keys), cleanup, idempotency
- Have each sub-agent WRITE its result to a dedicated JSON file (e.g. `deep_<domain>.json`) — returning large JSON inline truncates; writing to disk guarantees completeness

### 3. Generate front-matter with yaml.safe_dump, never hand-assembled YAML

Hand-assembled YAML front-matter breaks on: `@` in values (`@EnableAuthority`), quotes inside double-quoted scalars, `{`/`}` in flow mappings, `$` in `${var}`. Build a Python dict from the deep JSON and serialize with `yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, default_flow_style=False, width=10000)`. Wrap with `---
 ... 
---`. Validate EVERY generated file with `yaml.safe_load` after generation.

### 4. Map upstream/downstream to HTTP endpoints (NOT Java calls)

The `upstream` (前置业务) and `downstream` (消费方) sections MUST list **HTTP interface URLs** (e.g. `POST /rcc/classroom/strategy/create`) or **SPI classes** (`SPI: XxxSPIImpl`), NOT Java method calls (`classroomAPI.validateClassroomConfig()`).

- **Upstream** = HTTP interfaces that must be called BEFORE this endpoint, producing input IDs/enums (business data-flow: which field of the request was created by which other endpoint?). Example: `studentClassroomStrategyId` comes from `POST /rcc/classroom/strategy/create`; `管理员登录` produces SessionContext.
- **Downstream** = HTTP interfaces that consume the data this endpoint writes, or SPI consumers (`SPI: 类名`). Example: `POST /rcc/classroom/seat/batchCreate` consumes the classroom created by `POST /rcc/classroom/create`.
- **Verify every URL exists** by concatenating class-level + method-level `@RequestMapping` in a real Controller. Java API functions (xxxAPI.xxx) are NEVER acceptable in these sections.
- Java method calls may be used as EVIDENCE to derive the mapping, but the output must be HTTP URLs.

### 4b. Attach field-level field_map (cross-interface data-flow contract) — REQUIRED for AI orchestration

**HARD RULE: the generated doc's 上游前置业务/下游消费方 sections MUST render HTTP endpoints from field_map, NEVER the raw internal calls from the deep JSON.** The deep JSON's `upstream/downstream` are often internal service calls (`internal://XxxAPI.method()`), which are NOT callable HTTP endpoints. The doc generator MUST:
1. Load the field_map (fm_*.json) and render 上游/下游 from its `source_api` HTTP URLs (`POST /rcc/xxx`).
2. If an interface has NO HTTP upstream in field_map (pure query/validation, only internal deps), render an explicit note "服务端内部调用（非 HTTP 端点）" instead of listing `internal://...` as if it were an endpoint.
3. NEVER emit `internal://...` in the 上游/下游 body sections. `internal://` may appear only inside a clearly-labeled supplementary note.
4. A doc whose 上游/下游 shows `internal://XxxAPI.method()` is a BUG — regenerate with field_map. Audit must flag it (see Step 7).
5. **Fix BOTH the body AND the front-matter data layer (HARD)** — the doc has two layers: the human-readable body sections AND the machine-consumable front-matter (`setup`/`upstream`/`downstream`/`cleanup`/`polling`). AI orchestration reads the FRONT-MATTER, not the body. Fixing only the body sections while leaving `internal://` in front-matter makes the doc look right to humans but breaks the orchestrator. Every `internal://` in front-matter fields (setup/upstream/downstream/cleanup) must be replaced with the field_map HTTP `source_api`, or relabeled `内部调用:类名` when no HTTP endpoint exists. After fixing the body, re-scan the front-matter YAML for `internal://` in each of these 5 fields — zero tolerance.

HTTP URL alone is NOT enough for AI orchestration. Every upstream/downstream must carry a **field_map**: which upstream RESPONSE field feeds which input field, and which output field feeds which downstream input. Without it, AI falls back to naive same-name matching and silently breaks when names differ (e.g. upstream `classroomStrategyId` → input `studentClassroomStrategyId`).

Per upstream/downstream entry add:
```json
{
  "upstream": [{
    "api": "POST /rcc/classroom/strategy/create",
    "field_map": [
      {"from_jsonpath": "$.content.classroomStrategyId", "to": "studentClassroomStrategyId", "required": true, "note": "策略ID：上游字段名≠入参字段名，需显式映射"}
    ]
  }],
  "downstream": [{
    "api": "POST /rcc/classroom/seat/batchCreate",
    "field_map": [
      {"from": "classroomId", "resolve_via": "异步创建完成后：taskId轮询 → POST /rcc/classroom/getInfo 按名查询取 $.content.classroomId", "to": "classroomId", "required": true}
    ]
  }]
}
```
Rules:
- **from_jsonpath** comes from the upstream interface's RESPONSE DTO (`$.content.xxx`, SK wrapper), NOT a guess. If unknown, mark 推断 — never fabricate a path.
- **resolve_via** is REQUIRED when the producing interface is async (returns only taskId, no business ID) — the orchestrator must poll + query to obtain the ID. Example: create is async, classroomId must be fetched via `taskId 轮询 → getInfo` after completion.
- **Field-name mismatch is the norm** (upstream `classroomStrategyId` → input `studentClassroomStrategyId`; output `classroomId` → downstream input `id`). Naive same-name matching fails — field_map is the contract.
- **Build the map by CROSS-linking**: for each `from_upstream` input field, find the source_api's RESPONSE DTO field (semantic match on 策略ID/教室ID/镜像ID), not by guessing.
- For AI orchestration the field_map contract should live in a standalone machine-readable JSON (single source of truth); the md keeps a human summary table.

### 5. Generate Mermaid 依赖关系全景图 programmatically

`graph LR` with subgraphs: 上游前置业务 (upstream nodes A1..An) → central B (URL + summary + permission) → 内部处理流程 (flow steps C1..Cn) → 下游消费方 (downstream D1..Dn). Edges: `A{i} -->|数据| B`, `B --> C1`, `B -->|数据| D{i}`.

### 6. Validate the batch (not just one sample)

- `yaml.safe_load` front-matter of EVERY file (not one)
- Every body section title present in EVERY file (not one)
- Spot-check 2-3 files for REAL content depth (state machine steps, error codes, permission checks) — empty shells pass section checks but fail depth
- Restore any hand-curated golden docs that the batch generator would overwrite (back them up before regenerating)

### 7. Audit the batch independently (do not self-approve)

The generator + the extracting sub-agents share blind spots. Run an INDEPENDENT mechanical audit of every generated file before delivery:

- **Re-verify permissions from source, not from the deep JSON text** — the deep JSON `auth` field may be a sub-agent's free-text description (e.g. "需登录（SessionContext）；@EnableAuthority 鉴权注解；…") and a naive `'EnableAuthority' in str(auth)` match will FALSELY mark methods that only mention the word in prose. Set `auth` as a BOOLEAN extracted by scanning the method's annotations (grep `@EnableAuthority` in the method signature's preceding lines), never a description string.
- **Cross-check required flags against the body table** — front-matter `required: true` must equal the 必填 column "是" in the body table. A boolean-to-string bug (`'是' in str(True)` → False) silently flips all to "否". Use boolean checks (`'是' if field['required'] else '否'`), then diff front-matter vs body for every field of every file.
- **No URL truncation** — API/upstream/downstream URLs must be stored in full; slicing (`api[:60]`) cuts long URLs mid-path. Truncate only descriptive text (purpose), never URLs.
- **URL normalization** — normalize the endpoint url with a leading `/` (method-level `@RequestMapping("list")` without leading slash must still yield `/rcc/classroom/list`).
- **Produce an audit report** (per-file verdict table: 实质性错误/系统性缺陷/次要问题/已确认正确) so nothing is silently shipped.
- **No `internal://` in 上游/下游 sections** — grep every generated doc: 上游前置业务/下游消费方 body must contain only `POST /`, `管理员登录`, or the "内部调用" note; any `internal://XxxAPI.method()` in these sections is a generation bug (deep JSON leaked through), flag as 实质性错误.
- **No `internal://` in front-matter data layer either** — parse the front-matter YAML and check ALL of `setup`/`upstream`/`downstream`/`cleanup` (the fields the orchestrator reads): zero `internal://` allowed; every entry must be `POST /...` or `内部调用:类名`. Body-only fixes are incomplete — flag any front-matter `internal://` as 实质性错误.

## Document Format

## Document Format

### Section Structure (per interface, H1 separated)

Each interface is an H1 section with this structure:

1. 画板：依赖关系全景图 (Mermaid flowchart)
2. 接口基本信息 (Table: URL, method, permissions, return type)
3. 入参详情 (Table: param, type, required, constraint, description — **based on actual request JSON**)
4. 出参详情 (Table: response fields + wrapper fields)
5. 前置业务依赖 (List each upstream with URL and what it produces)
6. 内部处理流程 (Step-by-step numbered list)
7. 下游消费方 (List each consumer with URL/method)
8. 参数取值策略表 (Table: param, strategy, source, example)
9. 成功/失败断言基准 (Success + failure scenario tables)
10. 环境清理机制 (Cleanup chain + API table + failure handling)
11. 前置状态和幂等性标注 (Precondition table + idempotency analysis)

### prereq_state 节（操作类接口 MUST，查询类可省略）
**操作类接口**（对既有资源下发指令：restart/shutdown/powerOff/forceWakeUp/restore/delete/edit 等）front-matter 必须声明 `prereq_state`，声明操作要求的目标资源状态与达成途径，供编排器 `validate_plan()` 做前置状态校验与自动补步骤：

```yaml
prereq_state:
  resource: desktop          # 目标资源类型
  required_state: RUNNING    # 操作要求的状态
  achieve_via:               # 达成该状态的途径（接口 + 说明）
  - api: POST /rcc/classroom/cmrcef/lesson/start
    note: 学生桌面无独立开机接口，只能通过上课批量开机
```

- 达成途径必须指向**真实 HTTP 接口**（取自 field_map 的 source_api），不得写 `内部调用:`
- 同一类资源的状态规则（如"桌面操作要求 RUNNING"）**同步维护到 `api_md_staging/business_rules.md` 的 `state_prereq` 节**——规则库是编排器的唯一规则源，接口文档的 `prereq_state` 与规则库保持一致
- 新增操作类接口时：先查 `business_rules.md` 是否已有同类规则，有则复用；无则在两处同步新增

### request.body 字段 MUST 声明 value 引用（编排可执行性的前提）

编排器 `_build_step` 只填充带 `value`/`generated_by` 的请求字段，其余裸字段（仅 type/constraint/description）在编排时被跳过 → 步骤 body 为空、接口无法实际执行。生成文档时**每个请求字段 MUST 标注参数来源**（三选一）：

```yaml
request:
  body:
    classroomName:
      type: String
      required: true
      value: ${param.classroom_name}      # ① 用户用例参数（params 节声明同名变量）
    classroomId:
      type: UUID
      required: true
      value: ${prev.query_classroom.output.classroomId}   # ② 前置步骤 extract 产出
    cpu:
      type: Integer
      generated_by: true                  # ③ 生成规则（cpu/memory/systemSize/desktopPreName 等）
```

- 编排器对裸字段有**确定性推断兜底**（字段名 snake_case 命中 params → `${param.x}`；命中 setup extract 变量 → `${prev.x}`；命中生成字段集 → generated），但推断覆盖率约 16%，**不应依赖兜底**，生成时直接写全
- params 节 MUST 与 request.body 的 `${param.*}` 引用一致（引用未声明的变量 = 编排断裂）
- 纯查询/校验接口可省略 value（无请求体或参数由 UI 侧输入）

### 编排器规则库消费机制（orchestrator.validate_plan，确定性非 AI）

编排器加载 `api_md_staging/business_rules.md` 后，对每个编排计划自动执行（无需人工干预）：

1. **资源依赖链自动补**：操作步骤（命中 `state_prereq` 的桌面重启/关机/唤醒/还原等）若 plan 中无该资源的造数接口 → 自动补完整链（`create → seat/batchCreate → image/student/create`），解决"有桌面可操作但没造桌面/分配镜像"的通用缺口
2. **前置状态补步骤**：操作步骤要求目标状态（如桌面 RUNNING）且 plan 无达成途径 → 自动补 `achieve_via` 步骤（如上课开机 `cmrcef/lesson/start`）
3. **依赖顺序修正**：资源依赖链接口若逆序出现 → 按链顺序重排

自动补的步骤标记 `_auto_by_rules: true` 并出现在编排计划的 `rule_added` 列表，可人工确认。规则匹配为**模式匹配**（URL 含 resource 段 + action 段），覆盖所有域的同类操作，无需逐接口列举。

### Organization Rules

1. Each interface's ALL content stays within its H1 section
2. Document ends with one consolidated comparison table (new interface = add column)
3. Supplementary content goes INSIDE the corresponding interface section, never at bottom
4. Methodology/knowledge-graph design content goes in architecture doc, not interface sections
5. **Dual-form md files** (per-interface Markdown + YAML front-matter) should mirror the same section structure; front-matter carries machine-consumable data (setup/polling/assertions/cleanup/idempotency), body carries human-readable content (mermaid/table). Keep both in sync — they come from the same source of truth.

### Mermaid Diagram Pattern

```
graph LR
    subgraph 上游前置业务
        A1["POST /upstream/api\n描述\n→ 产出 xxxId"]
    end
    B["POST /target/endpoint\n描述\n入参: xxxId(必填)\n权限/返回类型"]
    A1 -->|xxxId| B
    subgraph 内部处理流程
        C1["Step1: ..."]
        C2["Step2: ..."]
        C1 --> C2
    end
    B --> C1
    subgraph 下游消费方
        D1["POST /downstream/api\n描述"]
    end
    B -->|数据| D1
```

## Writing to Feishu

- New content: `lark-cli docs +update --doc "<url>" --command overwrite --doc-format markdown --content "<content>"`
- Append: fetch existing content first, combine with new, then overwrite
- Mermaid whiteboard: copy file to workspace first (lark-cli needs relative paths), then `lark-cli docs +whiteboard-update --whiteboard-token "<token>" --input_format mermaid --overwrite --source @diagram.txt`
- Get wiki node info: `lark-cli wiki +node-get --node-token "<url>"` to extract obj_token
- Duplicate-key validation: `pyyaml` silently accepts duplicate YAML keys (last wins) — run a text-level duplicate-key check (per parent path) in addition to `yaml.safe_load` when generating YAML/md front-matter.

## Common Pitfalls

1. **Nested JSON string fields** — `String` fields named `*FacadeStr`/`*JsonStr` contain JSON with nested parameters. Always trace `JSON.parseObject()` deserialization, and extract nested fields **from the real JSON string**, not just the DTO.
2. **DTO fields ≠ request fields** — a field existing in the DTO class does NOT mean it is sent in the request. Real request JSON may omit DTO fields (e.g. `enableGpu`/`vgpuItem`/`vgpuModel` exist in `VDIDeskStrategyDTO.java` but the real request expresses vGPU via top-level `vgpuType`+`vgpuExtraInfo`). Conversely, framework-injected fields (`business: "RCC"`) exist in the request but not in any DTO. Always diff both directions against the actual request JSON.
3. **Do NOT use Python test framework for completeness validation** — the test framework's parameters are NOT complete. Parameter completeness must come from actual request JSON + DTO field extraction.
4. **Nested objects vs sibling switches** — a nested object (e.g. `watermarkInfo` with `enable` inside) and its sibling switch field at the same level (e.g. `enableWatermark` in the vdi node) are DIFFERENT fields; both may be sent. Do not merge or drop either.
5. **Methodology vs interface content** — Constraint extraction patterns and knowledge graph schema are META content, put in architecture doc not interface sections.
6. **Comparison table** — One consolidated table at document end, not per-interface.
7. **Diagram assertions are facts, not intuition** — every formula, entity name, and field name in the 画板/全景图 must be grep-verified against source. E.g. `free = desktopNum - running - fault` may be wrong (actual: `close = desktopNum - running`, `free` from overview); `DesktopPoolEntity` may not exist (actual: view `RccViewSpaceEntity`); a field may be `rccSpaceImageDTOList` not `imageTemplateArr`.
8. **Downstream paths must exist** — a path that "sounds right" (`/rcc/classroomImage/assign`) may not exist; verify class-level + method-level `@RequestMapping` concatenation in a real controller (real entry could be `/rcc/classroom/image` + `/teacher/create`/`/student/create`).
9. **Taskflow/BatchHandler step names must match actual processors** — read `registry.add(...)` order and each processor class; do not name steps from what they "should" do.
10. **Method attribution: API interface vs SPI implementation** — `SpaceClassroomPoolUserMgmtAPI.getDeskPoolAllocateInfoDTO` is an API method; `PlatformDeskSPIImpl.getDesktopPoolAssignResultDTO` is the SPI public method. Do not list API methods as SPI methods in the diagram.
11. **Unenforced DTO annotations** — if the Controller has no `@Valid`, DTO `@NotNull`/`@Range`/`@Pattern` are decorative. Verify the actual validation layer (controller `Assert.notNull`, service `validate*`, `checkVDIParamAvailable`) before documenting constraints or failure scenarios.
12. **Non-existent failure scenarios** — a documented failure case (e.g. "systemSize out of range") may not actually be validated (e.g. `checkVDIParamAvailable` only checks cpu/memory). Trace the validation method body before claiming the failure case exists.
13. **Front-end pass-through fields** — real request JSON may contain MANY fields with NO corresponding DTO field (e.g. 34 of 53 top-level fields in the vdi/create request are pass-through: server reads them only via `strategyGroupFacadeStr.vdi`). Do NOT conclude "doc is wrong" when DTO lacks a JSON field; trace where the server actually reads it (often the nested facadeStr).
14. **Ghost fields in docs** — a doc section may list fields that exist in neither real JSON nor the correct DTO (e.g. `enableGpu` in the vdi node section, or `condition.agencyScope` which lives in the facadeStr top-level `condition` node, not in `vdi`). Mark them "幽灵字段/勿构造" so automation doesn't send or assert them.
15. **Wrong deserialization DTO assumption** — never assume which DTO a JSON string deserializes to; grep the actual `JSON.parseObject(str, X.class)` call site. The wrong assumption (VDIDeskStrategyDTO vs the real VDIStrategyDTO) invalidates nested-field validation.
16. **Doc naming layer ≠ JSON naming layer** — docs may use snake_case (open_usb_read_only) while the real request uses camelCase (openUsbReadOnly). Automation keys must follow the real JSON; document the mapping explicitly.
17. **Never hand-assemble YAML front-matter** — `@EnableAuthority`, quotes, `{}`, `${var}` all break naive f-string YAML. Build a dict and `yaml.safe_dump`. Validate every file with `yaml.safe_load` (validating one sample ≠ valid batch).
18. **Batch generation overwrites golden docs** — the generator may overwrite a hand-verified deep doc (e.g. vdi/create). Back it up before regenerating and restore after.
19. **Deep JSON returned inline gets truncated** — for batch deep analysis, have sub-agents WRITE to JSON files instead of returning content; inline large JSON in tool results is unreliable.
20. **Shallow auto-skeleton ≠ golden depth** — a doc with all 12 section headers but placeholder content ("待补充") does NOT meet the golden standard. Real content = state machine steps, real error codes, real permission checks, real DTO constraints.
21. **Upstream/downstream = HTTP endpoints, NOT Java calls** — 上游前置业务 and 下游消费方 must list HTTP interface URLs (`POST /rcc/classroom/strategy/create`) or SPI classes (`SPI: XxxSPIImpl`), never Java method invocations (`classroomAPI.validateClassroomConfig()`). Derive the mapping from business data-flow (which endpoint produces the input ID / which endpoint consumes the written data) and verify each URL exists in a real Controller's class-level + method-level `@RequestMapping` concatenation.
22. **Structured booleans, never description strings** — fields like `auth`/`required` in the deep JSON MUST be booleans. A free-text `auth` ("需登录；@EnableAuthority 鉴权注解；…") breaks naive `'EnableAuthority' in str(auth)` matching (false positives) and `'是' in str(True)` matching (false negatives). Extract permission by scanning the method's actual annotations; store `True`/`False`.
23. **Never slice URLs in generators** — `api[:60]` cuts long endpoint paths mid-string. Store URLs in full; truncate only human descriptions. Normalize URLs with a leading `/`.
24. **field_map is a cross-interface contract, not per-interface source labels** — labeling each interface's OWN input fields with `source=from_upstream` does NOT give AI the linkage. You must build the BIDIRECTIONAL map: upstream RESPONSE field → this endpoint's input field (`from_jsonpath → to`), and this endpoint's output → downstream input, with `resolve_via` for async producers. A doc with upstream 0 field_map blocks (e.g. create) is incomplete for orchestration even if all other sections are rich.
25. **Same-name matching is the naive fallback and it silently fails** — AI orchestration that matches `classroomStrategyId == studentClassroomStrategyId` by name breaks on every renamed field. The field_map must explicitly carry the from→to link; never assume field names align.
26. **Never render internal:// in 上游/下游 sections (HARD)** — the deep JSON's upstream/downstream are often internal service calls (`internal://XxxAPI.method()`), which are NOT HTTP endpoints and break orchestration (no URL to call). The doc generator MUST render 上游/下游 from field_map's HTTP `source_api`; interfaces with no HTTP upstream must show "服务端内部调用（非 HTTP 端点）" instead of a fake endpoint. Any `internal://` in these sections is a generation bug.
27. **Assertions = HTTP response, NOT audit logs (HARD)** — a sub-agent extracting from the method body may mistake `auditLogAPI.recordLog(...)` (server-side logging) for the response. The assertion MUST be what the response returns: `status==SUCCESS/ERROR` + `msgKey` + `content.taskId` (async). "记录 XX 审计日志" is invisible in the response → useless for automation. Read the Controller's `DefaultWebResponse.Builder.success/fail` to get the real assertion. Mechanical check: any assertion point that only says "记录...审计/日志" (no status/msgKey/返回/抛) is a bug.
28. **Fix internal:// in BOTH body and front-matter data layer (HARD)** — a doc has two layers: human-readable body sections AND machine-consumable front-matter (`setup`/`upstream`/`downstream`/`cleanup`). The orchestrator reads the FRONT-MATTER. Fixing only the body (e.g. via rebuild_updown.py) while leaving `internal://` in front-matter fields makes the doc pass body checks but breaks orchestration — the deepest layer is what automation actually consumes. After body fixes, re-scan the front-matter YAML for `internal://` across all 4 data fields; replace with field_map HTTP `source_api` or relabel `内部调用:类名`.
29. **Response fields must be per-field, complete, and REAL (HARD)** — sub-agents may (a) merge related fields into one row (`vdiDesktopId/vdiDesktopIp/...`), (b) list only a fraction of the DTO's fields (9 of 40), or (c) FABRICATE fields — e.g. a `code: Integer` in the 出参详情 that does not exist (SK `DefaultWebResponse` has only `status/message/msgKey/msgArgArr/content`, NO `code`/`retCode`/`resultCode`). All break automation. Every response field gets its own row incl. inherited fields; framework field names must be REAL (`itemArr`/`total` from `PageQueryResponse.getItemArr()`, not guessed `items`); wrapper must be the standard five. Mechanical check: (i) any 出参详情 row whose field name contains `/` is a bug; (ii) field count must match the DTO (`grep -c "private"`); (iii) grep for `code|retCode|resultCode` in response — any hit is a fabricated field.
30. **Front-matter delimiter glue is invisible to lenient parsing (HARD)** — when re-writing a doc via `'---' + parts[2]` (without a trailing `\n`), the front-matter end marker glues to the body title (`---# POST /...`), producing a YAML syntax error that lenient `split('---\n',2)[1]` may still "pass" for some files. A doc can be 50% corrupted and still report "YAML 0 failures" if the check splits on substrings instead of standalone markers. STRICT check: (a) file starts with lone `---`; (b) `yaml.safe_load` on the block between the first and next standalone `---`; (c) `grep -rn "---#"` returns 0; (d) `re.search(r'^\-{4,}\n', content, re.M)` (runs of 4+ hyphens) returns 0. Also: input rows merged into a single line (field name containing `/`) and placeholder rows like `（框架注入/非请求体字段）` are bugs in 入参详情 too — check the input section with the same per-field rules as output.
31. **Every required field needs a value source (HARD)** — a request.body field with `required: true` but no `value`/`generated_by`/`${param.*}`/`${prev.*}` breaks the automation engine (it cannot construct the request). This is a COMMON gap even after parameterizing `name` — 9 of 10 required fields in a create endpoint may still lack a source. Batch-check: for every create/add/assign endpoint, every required field must have a value or a generation marker.
32. **Query setup steps must filter by name (名称→ID)** — extracting via `itemArr[0]` without name-filter params takes an arbitrary record; add searchKeyword/matchArr/exactMatchArr with the DTO's real field name. No-name interfaces: mark "取第一条（无名称过滤）". Also ensure ID fields in the main request bind to the setup step that produces them (`${prev.get_cluster.output.clusterId}`) and that step EXISTS in setup — add missing cluster/storagePool/network queries to image-assignment docs.
33. **Producer-consumer closure** — every create/add endpoint must assert its produced ID (`$.content.id`/`$.content.taskId`), have polling when async, and its output must be consumed (re-queried by name or via `${prev.*}`) downstream. A producer with unasserted/unconsumed ID is a broken chain.
34. **External platform endpoints are framework-built-in** — `POST /rco/admin/loginAdmin` (login, token into `${context.token}`, 401 auto-relogin) and `/rco/admin/list` are platform-level APIs outside the project; do NOT generate standalone docs for them, define the built-in handling once (see SETUP_PARAM_SPEC §11) and mark every setup login step with "框架内置". `file://` and direct-cluster `https://{cluster_virtual_ip}:9274` URLs are non-HTTP/direct — flag them in an external-endpoint list.
35. **Use-case template + dual-channel parsing reduce AI risk** — structured use-case input (【前置】【操作】【预期】 segments with `${param.*}`/`${prev.*}`) parses with rules (0 AI); free text needs AI. Compile-time check: every entity referenced in 预期 must have a producer in 前置 (else fail fast). Add `verify_after_polling` when task SUCCESS ≠ business done (e.g. image assign SUCCESS ≠ teacher terminal synced).
