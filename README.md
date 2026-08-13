# 无封装测试平台

基于「无封装测试方案」（文档驱动 + AI 即时编排 + 裸脚本运行）实现的测试平台。

## 📚 文档

- **[docs/使用手册.md](docs/使用手册.md)** — 完整使用手册（快速上手/用例规范/参数/执行）
- **[docs/示例用例集.md](docs/示例用例集.md)** — 5 个可直接复制的示例用例（模板+参数）

## 快速启动

```bash
cd autotest
python3 -m pip install -r requirements.txt   # flask/requests/pyyaml/jinja2
python3 run.py
# 打开 http://127.0.0.1:5001
```

> ⚠️ 5000 端口被 macOS AirPlay 占用，平台使用 5001。

## 4 个可视化

| 页面 | 路由 | 功能 |
|---|---|---|
| 首页 | `/` | 平台总览 + 接口统计 |
| 用例输入 | `/use-case` | 结构化模板（【前置】【操作】【预期】）+ 参数配置 + 执行 |
| 接口列表 | `/apis` | 224 接口检索 + 详情（入参/出参/断言） |
| 执行过程 | `/execution` | 用例执行实时日志 + 步骤结果 |
| 模型配置 | `/model` | LLM 配置（Provider/API/模型参数）+ AI 边界说明 |

## 架构（对齐方案 4 模块）

```
app/core/index.py    语义解析与索引（224 接口 → Map/倒排索引/DAG）
app/core/engine.py   场景编排 + 脚本合成 + 执行 + 断言裁判
app/web/app.py       Flask API + 4 可视化路由
app/templates/       页面模板（use_case/apis/execution/model）
```

## 配置

- 接口文档目录：环境变量 `API_MD_DIR`（默认指向 api_md_staging）
- 目标环境：用例输入页 BASE_URL
- LLM：模型配置页（用于自由文本用例解析）

## 关键设计

- **隔离执行**：默认 subprocess 执行生成的裸脚本（独立进程、资源隔离、实时日志捕获）；生产环境可升级 Docker（docker run --rm 挂载只读脚本）
- 用例模板【前置】【操作】【预期】→ 规则解析（0 AI，确定性）
- 参数 `${param.*}` / 前置产出 `${prev.*}` / 上下文 `${context.*}`
- 异步接口轮询（polling 配置驱动，taskId → 终态）
- 断言 `$.status=="SUCCESS"` + msgKey（SK 框架五件套）
- 登录 loginAdmin 框架内置（token 注入 + 401 重登）
