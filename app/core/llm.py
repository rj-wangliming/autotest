# -*- coding: utf-8 -*-
"""通道 B：LLM 用例解析（自由文本 → 接口意图序列）

AI 介入边界（对齐方案）：
- 本模块只做「自然语言 → 接口 URL 序列」的消歧（1 次批量调用）
- body/extract/polling 填充仍走接口文档（orchestrator._build_step），脚本合成 0 AI
- LLM 输出强校验：api 必须命中索引，不在索引内的丢弃并告警
"""
import json
import re


class LlmClient:
    """OpenAI 兼容 LLM 客户端（openai/deepseek/qwen/ollama 通用）"""

    def __init__(self, config):
        self.provider = config.get("provider", "openai")
        self.base_url = (config.get("base_url") or "").rstrip("/")
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "deepseek-chat")
        self.temperature = config.get("temperature", 0.1)
        self.max_tokens = config.get("max_tokens", 2048)
        self.timeout = 60

    @property
    def configured(self):
        return bool(self.base_url and self.api_key and self.model)

    def chat(self, system, user):
        """调用 chat/completions，返回文本"""
        if not self.configured:
            raise RuntimeError("LLM 未配置：请在「模型配置」页填写 provider/base_url/api_key/model")
        import requests  # 延迟导入，与 executor.py 一致（不阻塞模块加载）
        url = self.base_url + "/chat/completions"
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key
        resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        if resp.status_code != 200:
            raise RuntimeError("LLM 调用失败 HTTP %s: %s" % (resp.status_code, resp.text[:300]))
        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("LLM 返回无 choices: %s" % json.dumps(data, ensure_ascii=False)[:300])
        return choices[0].get("message", {}).get("content", "")

    def parse_use_case(self, sections, api_catalog, param_names=None):
        """结构化用例（前置/操作/预期，前置可空）→ 接口意图序列

        sections: {"前置":[...], "操作":[...], "预期":[...]}
        api_catalog: [{url, name}, ...] 接口清单（来自 index）
        返回: {"steps":[{"section":"pre|action","api":url,"step_name":str,"reason":str}],
               "assertions":[str]}
        """
        system = (
            "你是 RCC-Space 接口自动化测试的用例编排器。"
            "用户用例是业务/UI 操作描述（如\"点击XX按钮\"\"勾选XX\"\"列表中选择多个XX并执行XX\"），你要映射到后端 API。"
            "给定接口清单（url + 中文名 + body 字段），把【前置】和【执行/操作】的每个步骤映射到一个接口 url，必须从清单选取，不得编造。"
            "用例文本若明确含量化条件（时长/数量/规格等，如\"保持开机30分钟\"\"创建3台\"），把该值作为固定值写入对应字段的 param_map；其余参数从全局参数清单选取。对每个步骤的必填 body 字段，用 param_map 声明来源："
            "前置步骤产出用 ${prev.<step_name>.output.<field>}；全局参数用 ${param.<参数名>}；固定值直接写。"
            "若某查询步骤需产出数组（如多个ID供后续批量操作），用 extract_override 声明 JSONPath（如 $.content.itemArr[*].id）覆盖默认产出。"
            "若某步骤是纯环境状态描述且无需调接口即可满足，可省略；若需查询确认，映射为查询/list 接口。"
            "为每个步骤起唯一的英文 snake_case 名 step_name。保留出现顺序与所属段（section=pre|action）。"
            "把【预测/预期】转为断言表达式列表（如 $.status==SUCCESS）。"
            "只输出 JSON，不要 markdown 代码块，不要解释。"
            "JSON：{\"steps\":[{\"section\":\"pre|action\",\"api\":\"url\","
            "\"step_name\":\"snake_case\",\"reason\":\"理由\","
            "\"param_map\":{\"字段\":\"${prev.xx.output.yy}|${param.zz}|值\"},"
            "\"extract_override\":{\"产出名\":\"$.jsonpath\"}}],"
            "\"assertions\":[\"断言\"]}。"
        )
        system += (
            "全局参数清单（${param.<参数名>} 只能从清单选取，不得编造清单外名字）："
            + ("、".join(param_names) if param_names else "（空）") + "。"
        )
        catalog_text = "\n".join(
            "%s  |  %s  |  body: %s" % (
                a["url"], (a["name"] or "")[:50],
                ", ".join(a.get("fields") or []) if a.get("fields") else "无"
            ) for a in api_catalog
        )
        # 三段拼接（前置可空：为空则不出现该段）
        parts = []
        if sections.get("前置"):
            parts.append("【前置】\n" + "\n".join(sections["前置"]))
        if sections.get("操作"):
            parts.append("【操作】\n" + "\n".join(sections["操作"]))
        if sections.get("预期"):
            parts.append("【预期】\n" + "\n".join(sections["预期"]))
        user_text = "\n\n".join(parts) if parts else "（空用例）"
        user = "接口清单：\n%s\n\n用户用例：\n%s" % (catalog_text, user_text)
        raw = self.chat(system, user)
        return self._extract_json(raw)

    @staticmethod
    def _extract_json(text):
        """从 LLM 输出中提取 JSON（容错：去 markdown 代码块）"""
        text = text.strip()
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
        if m:
            text = m.group(1)
        if not text.startswith("{"):
            s, e = text.find("{"), text.rfind("}")
            if s != -1 and e != -1:
                text = text[s:e + 1]
        try:
            return json.loads(text)
        except Exception as e:
            raise RuntimeError("LLM 输出 JSON 解析失败: %s; 原文: %s" % (e, text[:200]))
