"""
急症识别与风险分层引擎 - 医疗初筛产品级
包含完整的 RED FLAG 体系，覆盖 9 大高危类别，支持自然语言理解和多信号叠加。
规则优先决定 risk_level，确保医疗安全。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

# 风险等级优先级（数值越大越高危）
_LEVEL_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "EMERGENCY": 3}


def _max_level(*levels: str) -> str:
    """取最高风险等级。"""
    best = "LOW"
    for lv in levels:
        if _LEVEL_RANK.get(lv, 0) > _LEVEL_RANK.get(best, 0):
            best = lv
    return best


@dataclass
class RuleHit:
    """单条规则命中结果。"""

    rule_id: str
    level: str
    label_zh: str  # 用户友好的中文描述
    category: str  # 风险类别


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RED FLAG 规则体系 - 系统化急症识别
# 
# 规则设计原则：
# 1. 覆盖真实医疗初筛中的高危信号
# 2. 支持自然语言口语化表达
# 3. 区分强度修饰词（"大量"、"严重"、"剧烈"等）
# 4. 考虑症状组合和特殊人群
# 5. 可扩展、可维护、可解释
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_KEYWORD_RULES: Tuple[Tuple[str, str, str, str, Tuple[str, ...]], ...] = (
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # EMERGENCY 级别 - 需要立即急救/拨打急救电话
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # 【1. 外伤/事故/暴力损伤】
    ("trauma_accident_emergency", "EMERGENCY", "遭遇事故或外伤", "外伤急症",
     ("车祸", "撞车", "被车撞", "交通事故", "坠落", "摔下", "高处跌落", "撞击头部", "头部受伤")),
    
    ("trauma_violence_emergency", "EMERGENCY", "暴力伤害", "外伤急症",
     ("刀伤", "被砍", "被刺", "被打", "暴力", "枪伤", "刀砍")),
    
    ("fracture_severe_emergency", "EMERGENCY", "严重骨折或肢体损伤", "外伤急症",
     ("骨头断了", "骨折", "断骨", "骨头露出", "肢体变形", "胳膊断", "腿断")),
    
    # 【2. 出血/失血风险】
    ("bleeding_massive_emergency", "EMERGENCY", "大量出血或失血", "出血急症",
     ("大出血", "大量出血", "流血不止", "血流不止", "止不住血", "出血很多", "流了很多血", "血流如注")),
    
    ("bleeding_gi_severe_emergency", "EMERGENCY", "严重消化道出血", "出血急症",
     ("吐血", "呕血", "呕出血", "黑便", "便血发黑", "柏油样便", "大量便血")),
    
    ("bleeding_respiratory_emergency", "EMERGENCY", "咯血不止", "出血急症",
     ("咯血不止", "大量咯血", "咳出大量血")),
    
    ("bleeding_pregnancy_emergency", "EMERGENCY", "孕产妇严重出血", "出血急症",
     ("产后大出血", "怀孕大量出血", "孕期大出血", "流产大出血")),
    
    # 【3. 呼吸循环系统危急】
    ("respiratory_failure_emergency", "EMERGENCY", "严重呼吸困难", "呼吸循环急症",
     ("喘不上气", "呼吸困难", "憋气", "窒息", "喉咙堵", "上不来气", "快不能呼吸", "呼吸很困难")),
    
    ("chest_pain_ami_emergency", "EMERGENCY", "疑似急性心梗", "呼吸循环急症",
     ("胸痛压榨", "胸口压榨", "压迫感胸痛", "胸口像被压住", "心口剧痛", "胸痛出冷汗", "胸闷喘不上气")),
    
    ("syncope_emergency", "EMERGENCY", "晕厥或休克", "呼吸循环急症",
     ("晕倒", "晕过去", "昏倒", "休克", "站不起来", "突然倒地")),
    
    # 【4. 神经系统急症】
    ("consciousness_loss_emergency", "EMERGENCY", "意识障碍", "神经系统急症",
     ("意识不清", "昏迷", "叫不醒", "不省人事", "意识模糊", "神志不清")),
    
    ("stroke_emergency", "EMERGENCY", "中风征兆", "神经系统急症",
     ("半身不遂", "一侧无力", "偏瘫", "口眼歪斜", "面瘫", "口角歪斜", "说话不清", "言语不清", "舌头歪",
      "一侧肢体无力", "手脚没力气", "突然说不出话")),
    
    ("thunderclap_headache_emergency", "EMERGENCY", "霹雳样剧烈头痛", "神经系统急症",
     ("霹雳样头痛", "爆炸样头痛", "一生中最严重的头痛", "突然剧烈头痛", "这辈子最疼的头痛", "像爆炸一样的头痛")),
    
    ("seizure_emergency", "EMERGENCY", "持续抽搐", "神经系统急症",
     ("抽搐", "痉挛", "抽风", "全身抽动", "口吐白沫")),
    
    # 【5. 严重过敏/中毒】
    ("anaphylaxis_emergency", "EMERGENCY", "严重过敏反应", "过敏急症",
     ("过敏性休克", "喉头水肿", "舌头肿大", "喉咙肿胀", "全身红疹呼吸困难", "脸肿呼吸困难")),
    
    ("poisoning_emergency", "EMERGENCY", "中毒", "中毒急症",
     ("中毒", "误服", "吃错药", "农药", "误食", "喝了农药", "吃了很多药", "药物过量")),
    
    # 【6. 精神心理危机】
    ("suicide_emergency", "EMERGENCY", "自杀自伤倾向", "心理危机",
     ("自杀", "想死", "不想活", "活不下去", "自残", "想结束生命", "准备自杀", "割腕")),
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # HIGH 级别 - 高危风险，需要尽快就医
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # 心血管高危
    ("chest_pain_high", "HIGH", "胸痛伴呼吸困难", "心血管",
     ("胸痛", "心口疼", "心前区痛", "胸闷痛", "胸口痛")),
    
    ("chest_discomfort_high", "HIGH", "胸部严重不适", "心血管",
     ("胸闷", "胸部压迫", "胸口发紧", "心口堵")),
    
    # 神经系统高危
    ("severe_headache_high", "HIGH", "严重头痛", "神经系统",
     ("剧烈头痛", "头痛难忍", "头痛很厉害", "头要炸了", "头痛得很厉害", "痛得很厉害")),
    
    ("neurological_symptoms_high", "HIGH", "神经系统异常", "神经系统",
     ("视力突然模糊", "复视", "看东西重影", "突然看不清", "眼前发黑", "肢体麻木")),
    
    # 急腹症
    ("acute_abdomen_high", "HIGH", "急性腹痛", "急腹症",
     ("剧烈腹痛", "腹痛难忍", "肚子剧痛", "腹痛剧烈", "腹部刀割样痛", "撕裂样腹痛")),
    
    ("peritonitis_high", "HIGH", "腹膜刺激征", "急腹症",
     ("肚子硬得像板", "腹部板状", "按肚子很痛", "腹部僵硬", "按压更痛", "按压痛", "右下腹疼痛")),
    
    # 出血（中等程度）
    ("bleeding_moderate_high", "HIGH", "中等出血", "出血",
     ("出血", "流血", "有血", "出了血")),
    
    ("hemoptysis_high", "HIGH", "咯血", "出血",
     ("咯血", "咳血", "痰中带血", "咳出血")),
    
    ("hematuria_high", "HIGH", "血尿", "出血",
     ("尿血", "小便带血", "血尿")),
    
    # 呼吸系统
    ("dyspnea_high", "HIGH", "呼吸困难", "呼吸系统",
     ("气短", "气促", "喘", "呼吸急促", "透不过气")),
    
    ("airway_obstruction_high", "HIGH", "气道梗阻风险", "呼吸系统",
     ("吞咽困难", "咽不下", "喉咙堵", "喉咙有异物")),
    
    # 高热/感染
    ("high_fever_high", "HIGH", "高热", "感染",
     ("高烧", "烧得很高", "发高烧", "体温很高")),
    
    ("meningitis_signs_high", "HIGH", "脑膜炎征象", "感染",
     ("颈部僵硬", "颈项强直", "脖子僵硬", "头痛发热呕吐")),
    
    # 孕产妇特殊风险
    ("pregnancy_risk_high", "HIGH", "孕期危险征象", "孕产妇",
     ("怀孕腹痛", "孕期出血", "阴道出血怀孕", "先兆流产", "宫缩频繁")),
    
    # 儿童特殊风险
    ("pediatric_emergency_high", "HIGH", "儿童高危症状", "儿童",
     ("婴儿", "新生儿", "小孩高烧", "孩子抽搐", "宝宝")),
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MEDIUM 级别 - 中等风险，建议尽快就医
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    ("fever_medium", "MEDIUM", "中等发热", "发热",
     ("发烧", "发热", "体温升高", "烧")),
    
    ("persistent_pain_medium", "MEDIUM", "持续疼痛", "疼痛",
     ("一直痛", "持续疼", "连续痛", "疼了好几天", "痛好久")),
    
    ("vomiting_medium", "MEDIUM", "反复呕吐", "消化系统",
     ("反复呕吐", "一直吐", "吐个不停", "吃什么吐什么", "呕吐不止")),
    
    ("diarrhea_severe_medium", "MEDIUM", "严重腹泻", "消化系统",
     ("拉肚子很厉害", "腹泻严重", "水样便", "一直拉肚子")),
    
    ("dehydration_medium", "MEDIUM", "脱水征象", "体液失衡",
     ("脱水", "喝不进水", "尿很少", "口唇干裂", "皮肤很干")),
    
    ("palpitations_medium", "MEDIUM", "心悸心慌", "心血管",
     ("心悸", "心慌", "心跳快", "心跳很快", "心跳加速", "感觉心跳")),
    
    ("hypertension_symptoms_medium", "MEDIUM", "高血压症状", "心血管",
     ("血压高", "高血压", "头晕头痛", "血压升高")),
    
    ("urinary_symptoms_medium", "MEDIUM", "泌尿系统症状", "泌尿系统",
     ("尿频", "尿急", "尿痛", "排尿困难", "小便不适")),
    
    ("jaundice_medium", "MEDIUM", "黄疸", "肝胆",
     ("黄疸", "眼睛发黄", "皮肤发黄", "尿黄得很")),
    
    ("rash_fever_medium", "MEDIUM", "皮疹伴发热", "皮肤/感染",
     ("皮疹发热", "红疹发烧", "出疹子")),
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # LOW 级别 - 低风险，可自我观察
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    ("mild_headache_low", "LOW", "轻度头痛", "轻症",
     ("轻微头痛", "有点头疼", "头有点胀", "头疼不厉害", "一点点头痛")),
    
    ("common_cold_low", "LOW", "普通感冒症状", "轻症",
     ("流鼻涕", "打喷嚏", "鼻塞", "嗓子痒", "轻微咳嗽", "有点咳")),
    
    ("mild_fatigue_low", "LOW", "轻度疲劳", "轻症",
     ("有点累", "轻度疲劳", "略感乏力", "有些疲惫", "感觉累")),
    
    ("mild_dyspepsia_low", "LOW", "轻度消化不良", "轻症",
     ("胃胀", "吃撑了", "消化不良", "有点胀气", "胃不太舒服")),
    
    ("mild_insomnia_low", "LOW", "轻度睡眠问题", "轻症",
     ("睡得不太好", "偶尔失眠", "有点失眠", "入睡困难")),
    
    ("mild_pain_low", "LOW", "轻微疼痛", "轻症",
     ("有点疼", "轻微疼痛", "一点点痛", "不太疼")),
    
    ("eye_strain_low", "LOW", "视疲劳", "轻症",
     ("眼睛累", "眼睛干", "用眼过度", "眼睛酸")),
    
    ("mild_anxiety_low", "LOW", "轻度焦虑", "轻症",
     ("有点焦虑", "有点紧张", "工作压力", "压力大")),
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 正则规则：补充数值、时间、强度判断
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_REGEX_RULES: Tuple[Tuple[str, str, str, str, str], ...] = (
    # 持续时间判断
    ("duration_long_medium", "MEDIUM", "症状持续3天以上", "时间因素",
     r"(三|四|五|六|七|八|九|十|\d+)\s*(天|日|周)"),
    
    # 体温相关
    ("fever_high_value", "HIGH", "体温≥39℃", "发热",
     r"(39|40|41)\.?\d*\s*[度℃]"),
    
    ("fever_medium_value", "MEDIUM", "体温38-39℃", "发热",
     r"38\.\d*\s*[度℃]"),
    
    # 强度修饰词（增强风险）
    ("intensity_severe", "MEDIUM", "症状强度严重", "强度因素",
     r"(很|非常|特别|极其|超级|剧烈|严重|厉害)\s*(痛|疼|难受|不舒服|严重)"),
    
    # 趋势词（恶化）
    ("trend_worsening", "MEDIUM", "症状加重趋势", "趋势因素",
     r"(越来越|更加|加重|恶化|严重了|不好|变重)"),
    
    # 止不住、不停等持续性表达
    ("continuous_severe", "HIGH", "持续不止", "持续性",
     r"(止不住|停不下|一直|不停|持续|不断)"),
)


def _normalize(text: str) -> str:
    """标准化文本：小写、去除多余空格。"""
    return text.strip().lower()


def _match_keyword_rules(text: str) -> List[RuleHit]:
    """
    关键词子串匹配（中英文小写）。
    支持自然语言口语化表达。
    """
    t = _normalize(text)
    hits: List[RuleHit] = []
    for rule_id, level, label_zh, category, keywords in _KEYWORD_RULES:
        for kw in keywords:
            if kw.lower() in t:
                hits.append(RuleHit(
                    rule_id=rule_id,
                    level=level,
                    label_zh=label_zh,
                    category=category
                ))
                break
    return hits


def _match_regex_rules(text: str) -> List[RuleHit]:
    """
    正则规则匹配：体温数值、持续时间、强度修饰词等。
    增强自然语言理解能力。
    """
    hits: List[RuleHit] = []

    for rule_id, level, label_zh, category, pattern in _REGEX_RULES:
        if re.search(pattern, text):
            hits.append(RuleHit(
                rule_id=rule_id,
                level=level,
                label_zh=label_zh,
                category=category
            ))

    return hits


def _calculate_risk_score(risk_level: str, num_hits: int, has_multiple_categories: bool) -> int:
    """
    根据风险等级和命中规则数量计算风险分数。
    
    计分原则：
    - EMERGENCY: 90-100分
    - HIGH: 70-90分
    - MEDIUM: 40-70分
    - LOW: 10-40分
    - 多个规则叠加会提高分数
    - 跨类别症状组合会提高分数
    """
    base_scores = {
        "EMERGENCY": 95,
        "HIGH": 80,
        "MEDIUM": 55,
        "LOW": 20,
    }
    
    score = base_scores.get(risk_level, 10)
    
    # 多规则叠加加分（每个额外规则+2分，上限+10）
    if num_hits > 1:
        bonus = min((num_hits - 1) * 2, 10)
        score = min(score + bonus, 100)
    
    # 跨类别组合加分
    if has_multiple_categories and risk_level in ("MEDIUM", "HIGH"):
        score = min(score + 5, 100)
    
    return score


def evaluate_rules(user_input: str) -> Tuple[str, int, List[str], List[str]]:
    """
    对用户输入执行完整规则评估。

    返回:
        risk_level: 最终等级（EMERGENCY > HIGH > MEDIUM > LOW）
        risk_score: 风险分数 0-100
        rule_triggered: 命中的规则 ID 列表（去重保序）
        explain_hints: 用于生成 explainability 的中文短描述列表
    """
    if not user_input or not user_input.strip():
        return "LOW", 0, [], []

    keyword_hits = _match_keyword_rules(user_input)
    regex_hits = _match_regex_rules(user_input)
    all_hits: List[RuleHit] = keyword_hits + regex_hits

    # 去重（同一 rule_id 只保留一次）
    seen: set = set()
    unique_hits: List[RuleHit] = []
    for h in all_hits:
        if h.rule_id not in seen:
            seen.add(h.rule_id)
            unique_hits.append(h)

    if not unique_hits:
        return "LOW", 10, [], []

    # 取最高风险等级
    levels = [h.level for h in unique_hits]
    risk_level = _max_level(*levels)

    # 检查是否跨类别
    categories = {h.category for h in unique_hits}
    has_multiple_categories = len(categories) > 1

    # 计算风险分数
    risk_score = _calculate_risk_score(risk_level, len(unique_hits), has_multiple_categories)

    rule_triggered = [h.rule_id for h in unique_hits]
    explain_hints = [h.label_zh for h in unique_hits][:10]

    return risk_level, risk_score, rule_triggered, explain_hints


def build_rule_first_explainability(
    risk_level: str,
    risk_score: int,
    rule_triggered: Sequence[str],
    hints_zh: Sequence[str],
    user_input_snippet: str,
) -> str:
    """
    生成产品化的可解释性文本 - 用户友好的自然语言，不暴露技术细节。
    
    设计原则：
    - 说明识别到了什么风险信号
    - 解释为什么影响风险等级
    - 明确下一步建议
    - 语气专业、克制、不吓人
    """
    parts: List[str] = []
    
    if risk_level == "EMERGENCY":
        parts.append("⚠️ 系统识别到紧急危险信号：")
        if hints_zh:
            signals = "、".join(hints_zh[:3])
            parts.append(f"{signals}。")
        parts.append("\n\n这些症状可能提示急危重症，存在生命危险。")
        parts.append("请立即采取以下措施：")
        parts.append("\n• 拨打急救电话（120/999）")
        parts.append("\n• 或立即前往最近医院急诊")
        parts.append("\n• 在等待过程中保持冷静，寻求身边人帮助")
        parts.append("\n• 如有意识不清、呼吸困难等情况，请立即实施急救")
        
    elif risk_level == "HIGH":
        parts.append("⚠️ 系统识别到高危风险信号：")
        if hints_zh:
            signals = "、".join(hints_zh[:4])
            parts.append(f"{signals}。")
        parts.append("\n\n这些症状提示可能存在较严重的健康问题，建议尽快就医评估。")
        parts.append("建议：")
        parts.append("\n• 尽快前往医院急诊或专科门诊")
        parts.append("\n• 不要拖延，避免病情加重")
        parts.append("\n• 就诊时向医生详细描述症状发生的时间、特点和变化")
        
    elif risk_level == "MEDIUM":
        parts.append("系统识别到需要关注的症状：")
        if hints_zh:
            signals = "、".join(hints_zh[:4])
            parts.append(f"{signals}。")
        parts.append("\n\n这些症状提示可能需要医疗评估和处理。")
        parts.append("建议：")
        parts.append("\n• 建议在24-48小时内就诊")
        parts.append("\n• 可先通过线上问诊咨询专业医生")
        parts.append("\n• 注意观察症状变化，如加重请及时就医")
        parts.append("\n• 避免自行用药掩盖症状")
        
    else:  # LOW
        if hints_zh:
            parts.append(f"系统识别到轻度症状：{hints_zh[0]}。")
        else:
            parts.append("根据您的描述，未识别到明显的危险信号。")
        parts.append("\n\n建议：")
        parts.append("\n• 可以先自我观察1-2天")
        parts.append("\n• 注意休息，保持良好的生活习惯")
        parts.append("\n• 如症状持续或加重，建议就医评估")
        parts.append("\n• 出现新的症状或不适，请及时就诊")
    
    # 免责声明（所有等级都包含）
    parts.append("\n\n" + "─" * 40)
    parts.append("\n💡 重要提醒：本系统仅提供初步风险评估，不能替代专业医疗诊断。如有疑问或症状加重，请及时就医。急危重症请立即拨打120或前往急诊。")
    
    return "".join(parts)


def build_advice_text(risk_level: str, hints_zh: Sequence[str]) -> str:
    """
    生成就诊建议文本 - 与风险等级一致。
    """
    if risk_level == "EMERGENCY":
        return (
            "⚠️ 紧急情况！请立即采取行动：\n\n"
            "1. 立即拨打急救电话 120 或 999\n"
            "2. 或立即前往最近医院急诊室\n"
            "3. 在等待急救时，保持镇静，寻求身边人帮助\n"
            "4. 如有生命危险征象（意识不清、呼吸困难、大出血等），请立即现场急救\n\n"
            "不要犹豫，不要拖延，生命第一！"
        )
    elif risk_level == "HIGH":
        return (
            "您的症状提示存在较高健康风险，建议：\n\n"
            "• 尽快前往医院急诊或专科门诊就诊\n"
            "• 建议在今日内完成就医评估\n"
            "• 不要自行用药，避免掩盖病情\n"
            "• 就诊时详细描述症状的发生时间、特点和变化过程\n"
            "• 如症状突然加重，请直接前往急诊"
        )
    elif risk_level == "MEDIUM":
        return (
            "您的症状需要医疗关注，建议：\n\n"
            "• 在24-48小时内就诊，进行进一步评估\n"
            "• 可优先考虑线上问诊咨询专业医生\n"
            "• 密切观察症状变化，记录症状特点\n"
            "• 如症状加重或出现新症状，请及时就医\n"
            "• 避免自行用药，以免延误诊断"
        )
    else:  # LOW
        return (
            "您的症状目前看来较为轻微，建议：\n\n"
            "• 可以先进行1-2天的自我观察\n"
            "• 注意休息，保持充足睡眠\n"
            "• 保持良好的饮食和生活习惯\n"
            "• 适当多喝水，避免过度劳累\n"
            "• 如症状持续3天以上或加重，建议就医评估\n"
            "• 出现新的症状或不适，请及时就诊"
        )
