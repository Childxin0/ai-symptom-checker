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
    """创建降级的结构化数据（基于关键词匹配）
    
    注意：调用方应传入经过预处理（否定句已过滤）的文本，
    以避免将"没有发烧"里的"发烧"误提取为症状。
    """
    text = user_input.lower()

    # ── 精确短语匹配 ──────────────────────────────────────────────
    symptoms = []
    symptom_keywords = [
        # 常见症状（精确短语）
        "头痛", "头疼", "发烧", "发热", "咳嗽", "恶心", "呕吐",
        "腹痛", "胸痛", "胸闷", "心慌", "头晕", "眩晕", "乏力", "疲劳",
        # 呼吸道
        "流鼻涕", "鼻涕", "鼻塞", "打喷嚏", "喉咙痛", "嗓子痛",
        # 消化道
        "腹泻", "拉肚子", "便秘", "胃痛",
        # 外伤
        "出血", "流血", "撞伤", "割伤", "烫伤", "扭伤",
        # 严重症状
        "呼吸困难", "气短", "喘不上气", "昏迷", "晕倒", "抽搐",
        # 其他
        "失眠", "焦虑", "心悸", "心跳快", "高烧", "低烧",
    ]
    for kw in symptom_keywords:
        if kw in text:
            symptoms.append(kw)

    # ── 部位 + 不适感 组合识别（覆盖"头很疼"、"脖子疼"等口语表达）──
    BODY_PART_LABELS = {
        "头": "头痛", "颈": "颈部疼痛", "脖子": "颈部疼痛",
        "喉咙": "喉咙疼痛", "嗓子": "喉咙疼痛",
        "胸": "胸部不适", "心": "心脏不适",
        "腹": "腹部疼痛", "肚子": "腹部疼痛", "胃": "胃部不适",
        "腰": "腰部疼痛", "背": "背部疼痛",
        "腿": "腿部疼痛", "膝": "膝关节疼痛",
        "手": "手部疼痛", "脚": "脚部疼痛",
        "眼": "眼部不适", "耳": "耳部不适",
    }
    DISCOMFORT_QUALIFIERS = {"疼", "痛", "胀", "麻", "酸", "闷", "难受", "不适", "不舒服", "不好"}
    for part, label in BODY_PART_LABELS.items():
        if part in text and any(q in text for q in DISCOMFORT_QUALIFIERS):
            if label not in symptoms:
                symptoms.append(label)

    # ── 呼吸/心脏特殊识别（不适感词可能插在中间，如"呼吸有点困难"）──
    if "呼吸" in text and not any("呼吸困难" in s for s in symptoms):
        symptoms.append("呼吸困难")
    if "心悸" not in symptoms and "心跳" in text:
        symptoms.append("心跳异常")
    
    # 优化持续时间提取
    duration = "未明确说明"
    duration_patterns = [
        (r'(\d+)\s*天', lambda m: f"{m.group(1)}天"),
        (r'(\d+)\s*日', lambda m: f"{m.group(1)}日"),
        (r'(\d+)\s*小时', lambda m: f"{m.group(1)}小时"),
        (r'(\d+)\s*周', lambda m: f"{m.group(1)}周"),
        (r'(\d+)\s*月', lambda m: f"{m.group(1)}月"),
        (r'昨晚|昨天|今天|刚才', lambda m: m.group(0)),
        (r'最近|近期|这几天', lambda m: m.group(0)),
        (r'突然|一直|持续', lambda m: m.group(0)),
    ]
    for pattern, formatter in duration_patterns:
        match = re.search(pattern, text)
        if match:
            duration = formatter(match)
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
        symptoms=symptoms,   # 无匹配时保持空列表，不添加占位词以免产生幻觉症状
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
    
    if risk_level == "EMERGENCY":
        return {
            "advice": "⚠️ 紧急情况！请立即采取行动：\n1. 立即拨打急救电话 120 或 999\n2. 或立即前往最近医院急诊室\n3. 在等待急救时，保持镇静，寻求身边人帮助\n4. 如有生命危险征象，请立即现场急救\n\n不要犹豫，不要拖延，生命第一！",
            "rationale": "系统检测到紧急危险信号。即使在降级模式下，仍明确建议立即采取急救措施。",
            "explainability": "您的描述中包含急症危险信号。为确保生命安全，请立即寻求紧急医疗救助。",
            "recommended_department": "急诊科 / 拨打120",
            "urgency_timeline": "立即"
        }
    elif risk_level == "HIGH":
        return {
            "advice": "检测到可能的危险信号。建议您尽快前往医院急诊或专科门诊就诊。建议在今日内完成就医评估。请不要自行用药，避免掩盖病情。如症状突然加重，请直接前往急诊。",
            "rationale": "系统在降级模式下检测到高危关键词。虽然未能完成完整AI分析，但基于安全优先原则，建议尽快就医。",
            "explainability": "您的描述中包含需要紧急处理的关键词。为确保安全，系统建议您尽快获得专业医疗评估。",
            "recommended_department": "急诊科 / 专科急诊",
            "urgency_timeline": "今日内就医"
        }
    elif risk_level == "MEDIUM":
        return {
            "advice": "您的症状需要专业医生评估。建议在24-48小时内就诊，如症状加重请提前就医。注意观察体温变化和症状是否恶化。",
            "rationale": "系统检测到中等风险信号，虽在降级模式下，但仍建议尽快就医以排除潜在问题。",
            "explainability": "您提到的症状组合需要进一步检查。虽然不是紧急情况，但不建议拖延就医时间。",
            "recommended_department": "内科 / 全科",
            "urgency_timeline": "24-48小时内"
        }
    else:
        return {
            "advice": "目前症状较轻。建议多休息、补充水分，观察症状变化。如果3天内症状未改善或出现加重，请就医。",
            "rationale": "系统未检测到明显危险信号。在降级模式下建议自我观察，但需警惕症状变化。",
            "explainability": "从您的描述来看，症状相对轻微。保持观察即可，但如有新症状出现请及时就医。",
            "recommended_department": "全科 / 保健科",
            "urgency_timeline": "可观察，3天内未改善再就医"
        }


def create_safe_fallback_result(
    user_input: str,
    reason: str = "系统异常"
) -> AnalysisResult:
    """
    最后防线：创建绝对安全的降级结果
    确保无论什么情况都能返回有效数据
    即使在异常情况下，也要尝试通过规则引擎识别高危场景
    """
    # 创建默认结构化数据
    structured = create_fallback_structured(user_input)
    
    # 尝试通过规则引擎评估（即使在异常情况下也要保证安全）
    try:
        from core.risk_engine import get_risk_engine
        risk_engine = get_risk_engine()
        risk = risk_engine.evaluate(user_input, structured)
    except:
        # 如果规则引擎也失败，默认使用保守的MEDIUM
        risk = RiskAssessment(
            level="MEDIUM",
            score=50,
            triggered_rules=["FALLBACK"],
            rule_explanations=["安全降级模式：系统未能完成完整分析"]
        )
    
    # 创建降级分析
    analysis = create_fallback_analysis(risk.level, risk.triggered_rules)
    
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
