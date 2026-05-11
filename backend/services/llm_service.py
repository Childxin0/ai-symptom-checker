"""
LLM 服务（services 层）- OpenAI-compatible API 调用
规则引擎 + LLM 混合路径：在规则引擎给定的 risk_level 下补充结构化字段与 rationale。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI, APIConnectionError, AuthenticationError, BadRequestError

from config import get_settings
from services.risk_engine import build_rule_first_explainability, build_advice_text

_BACKEND_ROOT = Path(__file__).resolve().parent.parent


def _read_prompt(name: str) -> str:
    p = _BACKEND_ROOT / "prompts" / name
    return p.read_text(encoding="utf-8")


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    """从模型输出中解析 JSON（允许包裹在 markdown 代码块中）。"""
    raw = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if fence:
        raw = fence.group(1).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                return None
    return None


def call_llm_structured(
    user_input: str,
    risk_level: str,
    rule_triggered: List[str],
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    调用 LLM（OpenAI-compatible），返回 (parsed_json_or_none, error_message_or_none)。
    """
    settings = get_settings()

    if not settings.llm_api_key:
        print("[LLM] LLM call failed: LLM_API_KEY 未配置")
        return None, "未配置 LLM_API_KEY"

    system = _read_prompt("system_prompt.txt")
    structure_instr = _read_prompt("structure_prompt.txt")

    user_block = f"""{structure_instr}

【用户描述】
{user_input}

【规则引擎结果（必须遵守，不得自行降低风险等级）】
- risk_level = {risk_level}
- rule_triggered = {json.dumps(rule_triggered, ensure_ascii=False)}

请严格输出一个 JSON 对象（不要 Markdown），字段如下：
{{
  "symptoms": string[],
  "duration": string,
  "severity": string,
  "possible_department": string,
  "advice": string,
  "ai_rationale": string,
  "explainability": string
}}

要求：
1. symptoms 为中文短语数组，尽量覆盖用户提到的症状。
2. risk_level 已由规则确定，不要在 JSON 中再次输出 risk_level 字段；explainability 中须点名触发规则 ID。
3. 若 risk_level 为 HIGH，advice 必须包含「请立即就医」或「拨打急救电话」之一。
4. explainability 用自然中文解释为何是该等级，并与 rule_triggered 呼应。
"""

    client = OpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        timeout=settings.llm_timeout,
    )

    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            max_tokens=2048,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_block},
            ],
        )
        text_out = response.choices[0].message.content or ""
    except AuthenticationError as e:
        print(f"[LLM] LLM call failed: API Key 无效或已过期 → {e}")
        return None, str(e)
    except APIConnectionError as e:
        print(f"[LLM] LLM call failed: 无法连接到 {settings.llm_base_url}，请检查 LLM_BASE_URL → {e}")
        return None, str(e)
    except BadRequestError as e:
        print(f"[LLM] LLM call failed: 请求参数错误，请检查 LLM_MODEL={settings.llm_model} → {e}")
        return None, str(e)
    except Exception as e:
        print(f"[LLM] LLM call failed: {type(e).__name__}: {e}")
        return None, str(e)

    parsed = _extract_json_object(text_out)
    if not parsed:
        print(f"[LLM] LLM call failed: JSON 解析失败，原始输出: {text_out[:200]}")
        return None, "JSON 解析失败"
    return parsed, None


def merge_llm_with_rules(
    llm: Dict[str, Any],
    risk_level: str,
    risk_score: int,
    rule_triggered: List[str],
    hints_zh: List[str],
    user_input: str,
) -> Dict[str, Any]:
    """
    合并 LLM 输出与规则引擎结论。
    规则引擎结果优先，LLM仅补充描述性内容。
    """
    advice_from_rules = build_advice_text(risk_level, hints_zh)
    advice_from_llm = str(llm.get("advice", "")).strip()

    if risk_level in ("EMERGENCY", "HIGH"):
        advice = advice_from_rules
        if advice_from_llm:
            advice += f"\n\n补充说明：{advice_from_llm}"
    else:
        advice = advice_from_llm if advice_from_llm else advice_from_rules
        if risk_level == "MEDIUM":
            must = ("就诊", "就医", "医生", "评估")
            if not any(k in advice for k in must):
                advice = advice_from_rules

    explainability = build_rule_first_explainability(
        risk_level=risk_level,
        risk_score=risk_score,
        rule_triggered=rule_triggered,
        hints_zh=hints_zh,
        user_input_snippet=user_input[:120],
    )

    explain_from_llm = str(llm.get("explainability", "")).strip()
    if explain_from_llm and risk_level == "LOW":
        explainability += f"\n\nAI补充分析：{explain_from_llm}"

    return {
        "symptoms": llm.get("symptoms") or [],
        "duration": str(llm.get("duration", "未知或未描述")),
        "severity": str(llm.get("severity", "未知")),
        "possible_department": str(llm.get("possible_department", "内科 / 全科")),
        "advice": advice,
        "ai_rationale": str(llm.get("ai_rationale", "")),
        "explainability": explainability,
    }
