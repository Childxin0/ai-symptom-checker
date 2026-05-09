"""
Fallback：LLM 不可用或 JSON 解析失败时，基于规则引擎输出完整、安全的默认响应。
"""

from __future__ import annotations

import re
from typing import List

from models.symptom_model import AnalyzeResponse
from services.risk_engine import build_rule_first_explainability

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
    if risk_level == "HIGH":
        return "急诊 / 胸痛中心"
    if risk_level == "MEDIUM":
        return "内科 / 全科"
    return "全科 / 保健门诊"


def default_advice(risk_level: str) -> str:
    """高风险必须包含就医与急救提示。"""
    if risk_level == "HIGH":
        return (
            "请立即就医或拨打急救电话；在等待救助期间避免剧烈活动，勿自行驾车。"
            "若出现胸痛、呼吸困难或意识异常加重，务必急诊处理。"
        )
    if risk_level == "MEDIUM":
        return (
            "建议今日或短期内线下就诊，监测体温与症状变化；避免自行联合用药。"
            "若加重请及时急诊。"
        )
    return "建议留意症状变化，规律作息与补水；若持续或加重请预约门诊。"


def build_fallback_response(
    user_input: str,
    risk_level: str,
    rule_triggered: List[str],
    hints_zh: List[str],
    reason: str = "",
) -> AnalyzeResponse:
    """组装 fallback 响应（fallback_used=True）。"""
    symptoms = extract_symptoms_heuristic(user_input)
    explain = build_rule_first_explainability(
        risk_level=risk_level,
        rule_triggered=rule_triggered,
        hints_zh=hints_zh,
        user_input_snippet=user_input[:120],
    )
    if reason:
        explain = f"{explain}（说明：{reason}）"

    return AnalyzeResponse(
        symptoms=symptoms if symptoms else ["待结构化补充"],
        duration=extract_duration_snippet(user_input),
        severity="中等" if risk_level == "MEDIUM" else ("较重" if risk_level == "HIGH" else "较轻"),
        risk_level=risk_level,
        possible_department=default_department(risk_level),
        advice=default_advice(risk_level),
        ai_rationale=f"当前无法调用大模型深化推理；分层完全依据规则引擎结果。触发规则：{', '.join(rule_triggered) if rule_triggered else '无'}。",
        rule_triggered=list(rule_triggered),
        explainability=explain,
        fallback_used=True,
    )
