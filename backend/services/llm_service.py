"""
Claude API 调用与 Prompt 加载：在规则引擎给定的 risk_level 下补充结构化字段与 rationale。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from anthropic import Anthropic

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
        # 尝试截取第一个 { 到最后一个 }
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                return None
    return None


def call_claude_structured(
    user_input: str,
    risk_level: str,
    rule_triggered: List[str],
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    调用 Claude，返回 (parsed_json_or_none, error_message_or_none)。
    """
    settings = get_settings()
    if not settings.anthropic_api_key:
        return None, "未配置 ANTHROPIC_API_KEY"

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

    client = Anthropic(api_key=settings.anthropic_api_key)
    try:
        msg = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=2048,
            temperature=0.2,
            system=system,
            messages=[{"role": "user", "content": user_block}],
        )
    except Exception as e:  # noqa: BLE001 — 统一交由上层降级
        return None, str(e)

    text_out = ""
    for block in msg.content:
        if block.type == "text":
            text_out += block.text

    parsed = _extract_json_object(text_out)
    if not parsed:
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
    强制 advice 满足高危/急症话术要求。
    """
    # 建议文本：优先使用规则引擎生成的标准建议
    advice_from_rules = build_advice_text(risk_level, hints_zh)
    advice_from_llm = str(llm.get("advice", "")).strip()
    
    # 对于EMERGENCY和HIGH，使用规则引擎的标准建议确保安全
    if risk_level in ("EMERGENCY", "HIGH"):
        advice = advice_from_rules
        if advice_from_llm:
            # LLM补充的建议作为附加信息
            advice += f"\n\n补充说明：{advice_from_llm}"
    else:
        # MEDIUM和LOW可以使用LLM建议，但要检查合理性
        advice = advice_from_llm if advice_from_llm else advice_from_rules
        if risk_level == "MEDIUM":
            must = ("就诊", "就医", "医生", "评估")
            if not any(k in advice for k in must):
                advice = advice_from_rules

    # Explainability：使用新的产品化解释
    explain_from_llm = str(llm.get("explainability", "")).strip()
    explainability = build_rule_first_explainability(
        risk_level=risk_level,
        risk_score=risk_score,
        rule_triggered=rule_triggered,
        hints_zh=hints_zh,
        user_input_snippet=user_input[:120],
    )
    
    # 如果LLM提供了额外解释，可以附加（但不影响主要解释）
    if explain_from_llm and risk_level == "LOW":
        # 只在LOW风险时附加LLM的解释
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
