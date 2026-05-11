"""
Fallback：LLM 不可用或 JSON 解析失败时，基于规则引擎输出完整、安全的默认响应。
"""

from __future__ import annotations

import re
from typing import List

from models.symptom_model import AnalyzeResponse
from services.risk_engine import build_rule_first_explainability, build_advice_text

# 常见症状词根，用于无 LLM 时的浅层抽取（演示用）
_SYMPTOM_LEXICON = (
    "头痛",
    "头疼",
    "发烧",
    "发热",
    "恶心",
    "呕吐",
    "腹痛",
    "胃痛",
    "腹泻",
    "咳嗽",
    "胸闷",
    "胸痛",
    "心悸",
    "心慌",
    "呼吸困难",
    "头晕",
    "乏力",
    "咽痛",
    "鼻塞",
    "流鼻涕",
)


def extract_duration_snippet(user_input: str) -> str:
    """粗粒度提取持续时间片段。"""
    m = re.search(r"\d+\s*[天日周小时分钟]", user_input)
    return m.group(0) if m else "未知或未描述"


def extract_symptoms_heuristic(user_input: str, max_n: int = 12) -> List[str]:
    """从原文中匹配已知症状词，去重保序。"""
    found: List[str] = []
    for w in _SYMPTOM_LEXICON:
        if w in user_input and w not in found:
            found.append(w)
        if len(found) >= max_n:
            break
    return found


def default_department(risk_level: str) -> str:
    """根据风险等级推荐科室。"""
    if risk_level == "EMERGENCY":
        return "急诊 / 拨打120"
    if risk_level == "HIGH":
        return "急诊 / 专科急诊"
    if risk_level == "MEDIUM":
        return "内科 / 全科"
    return "全科 / 保健门诊"


def build_fallback_response(
    user_input: str,
    risk_level: str,
    risk_score: int,
    rule_triggered: List[str],
    hints_zh: List[str],
    reason: str = "",
) -> AnalyzeResponse:
    """
    组装 fallback 响应（fallback_used=True）。
    即使LLM不可用，也能通过规则引擎正确识别高危场景。
    """
    symptoms = extract_symptoms_heuristic(user_input)
    
    # 使用新的产品化 explainability
    explain = build_rule_first_explainability(
        risk_level=risk_level,
        risk_score=risk_score,
        rule_triggered=rule_triggered,
        hints_zh=hints_zh,
        user_input_snippet=user_input[:120],
    )
    
    if reason:
        explain = f"{explain}\n\n（系统说明：{reason}）"

    # 使用新的建议生成逻辑
    advice = build_advice_text(risk_level, hints_zh)

    return AnalyzeResponse(
        symptoms=symptoms if symptoms else ["待结构化补充"],
        duration=extract_duration_snippet(user_input),
        severity="紧急" if risk_level == "EMERGENCY" else ("较重" if risk_level == "HIGH" else ("中等" if risk_level == "MEDIUM" else "较轻")),
        risk_level=risk_level,
        risk_score=risk_score,
        possible_department=default_department(risk_level),
        advice=advice,
        ai_rationale=f"当前无法调用大模型进行深度分析，风险评估完全基于规则引擎。触发规则：{', '.join(rule_triggered) if rule_triggered else '无'}。",
        rule_triggered=list(rule_triggered),
        explainability=explain,
        fallback_used=True,
    )
