"""
三层降级策略 - 确保永不返回500
"""
from core.models import StructuredSymptoms, RiskAssessment, AnalysisResult
import re


def extract_temperature(text: str) -> float | None:
    """从文本中提取体温"""
    patterns = [
        r'(\d{2}\.?\d?)\s*[度℃]',
        r'体温\s*(\d{2}\.?\d?)',
        r'发烧\s*(\d{2}\.?\d?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                temp = float(match.group(1))
                if 35 < temp < 43:  # 合理范围
                    return temp
            except:
                pass
    return None


def create_fallback_structured(user_input: str) -> StructuredSymptoms:
    """创建降级的结构化数据（基于关键词匹配）"""
    text = user_input.lower()
    
    # 简单症状识别
    symptoms = []
    symptom_keywords = [
        "头痛", "头疼", "发烧", "发热", "咳嗽", "恶心", "呕吐",
        "腹痛", "胸痛", "胸闷", "心慌", "头晕", "乏力"
    ]
    for kw in symptom_keywords:
        if kw in text:
            symptoms.append(kw)
    
    # 提取持续时间
    duration = "未知"
    duration_patterns = [r'(\d+)\s*[天日]', r'(\d+)\s*小时']
    for pattern in duration_patterns:
        match = re.search(pattern, text)
        if match:
            duration = match.group(0)
            break
    
    # 判断严重程度
    severity = "未知"
    if any(w in text for w in ["严重", "剧烈", "很痛"]):
        severity = "重度"
    elif any(w in text for w in ["有点", "轻微"]):
        severity = "轻度"
    else:
        severity = "中度"
    
    return StructuredSymptoms(
        symptoms=symptoms if symptoms else ["待详细分析"],
        duration=duration,
        severity=severity,
        body_location="",
        accompanying_symptoms=[],
        medical_history_mentioned=False,
        symptom_onset="不确定",
        temperature=extract_temperature(user_input),
        additional_context="降级模式：基于关键词匹配"
    )


def create_fallback_analysis(
    risk_level: str,
    triggered_rules: list[str]
) -> dict:
    """创建降级的分析结果"""
    
    if risk_level == "HIGH":
        return {
            "advice": "检测到可能的危险信号。建议您立即前往急诊或拨打120急救电话。请不要延误，在等待期间保持安静，避免剧烈活动。",
            "rationale": "系统在降级模式下检测到高危关键词。虽然未能完成完整AI分析，但基于安全优先原则，建议立即就医。",
            "explainability": "您的描述中包含需要紧急处理的关键词。为确保安全，系统建议您尽快获得专业医疗评估。",
            "recommended_department": "急诊科",
            "urgency_timeline": "立即就医"
        }
    elif risk_level == "MEDIUM":
        return {
            "advice": "您的症状需要专业医生评估。建议在24-48小时内就诊，如症状加重请提前就医。注意观察体温变化和症状是否恶化。",
            "rationale": "系统检测到中等风险信号，虽在降级模式下，但仍建议尽快就医以排除潜在问题。",
            "explainability": "您提到的症状组合需要进一步检查。虽然不是紧急情况，但不建议拖延就医时间。",
            "recommended_department": "内科/全科",
            "urgency_timeline": "24-48小时内"
        }
    else:
        return {
            "advice": "目前症状较轻。建议多休息、补充水分，观察症状变化。如果3天内症状未改善或出现加重，请就医。",
            "rationale": "系统未检测到明显危险信号。在降级模式下建议自我观察，但需警惕症状变化。",
            "explainability": "从您的描述来看，症状相对轻微。保持观察即可，但如有新症状出现请及时就医。",
            "recommended_department": "全科/保健科",
            "urgency_timeline": "可观察，3天内未改善再就医"
        }


def create_safe_fallback_result(
    user_input: str,
    reason: str = "系统异常"
) -> AnalysisResult:
    """
    最后防线：创建绝对安全的降级结果
    确保无论什么情况都能返回有效数据
    """
    # 创建默认结构化数据
    structured = create_fallback_structured(user_input)
    
    # 创建保守的风险评估（默认MEDIUM以确保安全）
    risk = RiskAssessment(
        level="MEDIUM",
        score=50,
        triggered_rules=["FALLBACK"],
        rule_explanations=["安全降级模式：系统未能完成完整分析"]
    )
    
    # 创建降级分析
    analysis = create_fallback_analysis("MEDIUM", ["FALLBACK"])
    
    return AnalysisResult(
        structured=structured,
        risk=risk,
        advice=analysis["advice"],
        rationale=analysis["rationale"],
        explainability=analysis["explainability"],
        recommended_department=analysis["recommended_department"],
        urgency_timeline=analysis["urgency_timeline"],
        needs_followup=False,
        followup_questions=[],
        followup_round=0,
        processing_time_ms=0,
        llm_used=False,
        fallback_reason=reason
    )


# 完成
