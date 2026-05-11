"""
症状分析路由：规则优先 + Claude 结构化补充 + Fallback。
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from models.symptom_model import AnalyzeRequest, AnalyzeResponse
from services.fallback import build_fallback_response
from services.llm_service import call_claude_structured, merge_llm_with_rules
from services.risk_engine import evaluate_rules, build_advice_text

router = APIRouter(tags=["symptom"])


@router.post("/analyze")
async def analyze_symptoms(body: AnalyzeRequest):
    """
    主流程：规则引擎 → Claude 结构化 → 失败则 Fallback。
    全程避免未捕获异常泄漏为 HTTP 500。
    """
    try:
        text = (body.user_input or "").strip()
        if not text:
            fb = build_fallback_response(
                "",
                "LOW",
                0,
                [],
                [],
                reason="未填写症状内容",
            )
            fb.advice = "请先输入您的不适描述（部位、性质、持续时间等），再进行分析。"
            fb.explainability = "尚未接收到有效文本，无法触发规则与模型。"
            return JSONResponse(status_code=200, content=fb.model_dump())

        # 规则引擎评估（现在返回4个值包括risk_score）
        risk_level, risk_score, rule_triggered, hints = evaluate_rules(text)

        llm_json, err = call_claude_structured(text, risk_level, rule_triggered)

        if llm_json:
            merged = merge_llm_with_rules(
                llm_json,
                risk_level=risk_level,
                risk_score=risk_score,
                rule_triggered=rule_triggered,
                hints_zh=hints,
                user_input=text,
            )
            symptoms_raw = merged.get("symptoms")
            if isinstance(symptoms_raw, list):
                symptoms = [str(s).strip() for s in symptoms_raw if str(s).strip()]
            else:
                symptoms = []

            return AnalyzeResponse(
                symptoms=symptoms or ["（模型未抽取到独立症状词）"],
                duration=str(merged.get("duration", "未知或未描述")),
                severity=str(merged.get("severity", "未知")),
                risk_level=risk_level,
                risk_score=risk_score,
                possible_department=str(merged.get("possible_department", "内科 / 全科")),
                advice=str(merged.get("advice", "")),
                ai_rationale=str(merged.get("ai_rationale", "")),
                rule_triggered=list(rule_triggered),
                explainability=str(merged.get("explainability", "")),
                fallback_used=False,
            )

        # LLM失败，使用fallback
        fb = build_fallback_response(
            text,
            risk_level,
            risk_score,
            rule_triggered,
            hints,
            reason=err or "模型不可用",
        )
        return JSONResponse(status_code=200, content=fb.model_dump())

    except Exception as exc:  # noqa: BLE001 — 兜底返回 200
        fb = build_fallback_response(
            getattr(body, "user_input", "") or "",
            "MEDIUM",
            55,
            [],
            [],
            reason=f"系统兜底：{exc!s}",
        )
        return JSONResponse(status_code=200, content=fb.model_dump())
