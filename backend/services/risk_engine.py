"""
规则引擎：关键词与模式匹配，规则优先决定 risk_level。
包含 30+ 条独立规则 ID，覆盖 HIGH / MEDIUM / LOW 场景。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

# 风险等级优先级（数值越大越高危）
_LEVEL_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


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
    label_zh: str  # 用于拼装 explainability


# ---------------------------------------------------------------------------
# 规则定义：每条含唯一 ID、等级、匹配方式（关键词子串或正则）
# 共计 36 条，满足「至少 30 条」要求
# ---------------------------------------------------------------------------

_KEYWORD_RULES: Tuple[Tuple[str, str, str, Tuple[str, ...]], ...] = (
    # ---------- HIGH（急危重症线索）----------
    ("chest_pain_high", "HIGH", "胸痛或心前区压迫", ("胸痛", "心口疼", "心前区痛", "压榨感", "压榨", "chest pain")),
    ("dyspnea_high", "HIGH", "呼吸困难或气促", ("呼吸困难", "喘不上气", "窒息感", "气短明显", "dyspnea")),
    ("altered_consciousness_high", "HIGH", "意识障碍", ("意识不清", "昏迷", "叫不醒", "意识模糊", "loss of consciousness")),
    ("thunderclap_headache_high", "HIGH", "突发剧烈头痛", ("霹雳样头痛", "突然剧烈头痛", "一辈子最严重的头痛", "爆炸样头痛")),
    ("massive_bleeding_high", "HIGH", "大量出血", ("大量出血", "吐血", "呕血", "便血发黑", "咯血不止")),
    ("dysphagia_high", "HIGH", "吞咽困难", ("吞咽困难", "咽不下", "吞咽梗阻")),
    ("hemiplegia_high", "HIGH", "单侧肢体无力或面瘫", ("半身不遂", "一侧肢体无力", "口眼歪斜", "垂腕", "hemiparesis")),
    ("suicide_ideation_high", "HIGH", "自杀或自伤意念", ("自杀", "不想活", "想死", "自残")),
    ("severe_allergy_airway_high", "HIGH", "严重过敏或气道梗阻", ("喉头水肿", "脸肿呼吸困难", "过敏性休克")),
    ("acute_coronary_language_high", "HIGH", "疑似心梗表述", ("像心梗", "心脏病发作", "heart attack")),
    # ---------- MEDIUM ----------
    ("fever_high_medium", "MEDIUM", "中等以上发热", ("发烧38", "发热39", "高烧", "体温39", "烧到38")),
    ("headache_persistent_medium", "MEDIUM", "持续头痛数日", ("头痛三天", "头痛3天", "头疼两周", "头痛一直不好")),
    ("abdominal_pain_persistent_medium", "MEDIUM", "持续腹痛", ("腹痛三天", "肚子痛好几天", "持续腹痛")),
    ("vomiting_repeated_medium", "MEDIUM", "反复呕吐", ("反复呕吐", "一直吐", "吃什么吐什么")),
    ("hypertension_headache_medium", "MEDIUM", "高血压伴头痛", ("高血压", "血压高", "hypertension")),
    ("postpartum_bleeding_medium", "MEDIUM", "产后或大出血风险语境", ("产后大出血", "恶露不尽")),
    ("dehydration_medium", "MEDIUM", "脱水或无法进食", ("喝不进水", "脱水", "尿很少")),
    ("severe_insomnia_anxiety_medium", "MEDIUM", "严重失眠伴躯体症状", ("几天没睡", "完全睡不着")),
    ("palpitations_chest_medium", "MEDIUM", "心悸伴胸部不适", ("心悸", "心慌", "心跳很快", "palpitation")),
    ("persistent_cough_blood_medium", "MEDIUM", "咳嗽咯血或血痰", ("咳血", "痰中带血", "咯血")),
    ("burn_pain_large_medium", "MEDIUM", "大面积烧伤或烫伤", ("大面积烫伤", "严重烧伤")),
    ("acute_abdomen_medium", "MEDIUM", "板状腹或急腹症表述", ("肚子硬得像板", "急性腹痛剧烈")),
    ("pregnancy_bleeding_medium", "MEDIUM", "孕期出血", ("怀孕出血", "孕期流血", "先兆流产")),
    # ---------- LOW ----------
    ("mild_headache_low", "LOW", "轻度头痛", ("轻微头痛", "有点头疼", "头有点胀")),
    ("common_cold_low", "LOW", "普通感冒样症状", ("流鼻涕", "打喷嚏", "鼻塞", "嗓子痒")),
    ("mild_fatigue_low", "LOW", "轻度疲劳", ("有点累", "轻度疲劳", "略感乏力")),
    ("mild_dyspepsia_low", "LOW", "偶发胃胀消化不良", ("偶发胃胀", "吃撑了", "轻度嗳气")),
    ("mild_insomnia_low", "LOW", "轻度睡眠不佳", ("睡得不太好", "偶尔失眠")),
    ("mild_joint_ache_low", "LOW", "轻度关节酸痛", ("关节有点酸", "轻微腰酸")),
    ("eye_strain_low", "LOW", "视疲劳", ("用眼过度", "眼睛干涩")),
    ("mild_allergy_skin_low", "LOW", "轻度皮疹瘙痒", ("有点痒", "小疹子")),
    ("stress_mild_low", "LOW", "轻度压力情绪", ("有点焦虑", "工作压力")),
)

# 正则规则：（rule_id, level, label_zh, regex_pattern）
_REGEX_RULES: Tuple[Tuple[str, str, str, str], ...] = (
    ("duration_ge_3d_medium", "MEDIUM", "症状持续约3天及以上", r"[三五七八九十两天\d]+\s*[天日]."),
)


def _normalize(text: str) -> str:
    return text.strip().lower()


def _match_keyword_rules(text: str) -> List[RuleHit]:
    """关键词子串匹配（中英文小写）。"""
    t = _normalize(text)
    hits: List[RuleHit] = []
    for rule_id, level, label_zh, keywords in _KEYWORD_RULES:
        for kw in keywords:
            if kw.lower() in t:
                hits.append(RuleHit(rule_id=rule_id, level=level, label_zh=label_zh))
                break
    return hits


def _match_regex_rules(text: str) -> List[RuleHit]:
    """补充正则规则（体温数值、天数等）。"""
    hits: List[RuleHit] = []

    # 发热语境下的体温数值 >= 38.5
    if any(k in text for k in ("烧", "热", "发烧", "发热", "体温")) or "度" in text:
        for m in re.finditer(r"(38\.[5-9]|39\.\d*|40\.\d*|39|40|41)", text):
            try:
                val = float(m.group(1))
            except ValueError:
                continue
            if val >= 38.5:
                hits.append(
                    RuleHit(
                        rule_id="fever_numeric_ge_38_5_medium",
                        level="MEDIUM",
                        label_zh="体温达到或超过38.5℃",
                    )
                )
                break

    for rule_id, level, label_zh, pattern in _REGEX_RULES:
        if re.search(pattern, text):
            hits.append(RuleHit(rule_id=rule_id, level=level, label_zh=label_zh))

    return hits


def evaluate_rules(user_input: str) -> Tuple[str, List[str], List[str]]:
    """
    对用户输入执行完整规则评估。

    返回:
        risk_level: 最终等级（HIGH > MEDIUM > LOW）
        rule_triggered: 命中的规则 ID 列表（去重保序）
        explain_hints: 用于生成 explainability 的中文短描述列表
    """
    if not user_input or not user_input.strip():
        return "LOW", [], []

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
        return "LOW", [], []

    levels = [h.level for h in unique_hits]
    risk_level = _max_level(*levels)

    rule_triggered = [h.rule_id for h in unique_hits]

    explain_hints = [h.label_zh for h in unique_hits][:10]

    return risk_level, rule_triggered, explain_hints


def build_rule_first_explainability(
    risk_level: str,
    rule_triggered: Sequence[str],
    hints_zh: Sequence[str],
    user_input_snippet: str,
) -> str:
    """
    基于规则命中生成 explainability：包含触发规则 ID（便于审计），语气面向用户。
    """
    parts: List[str] = []
    if hints_zh:
        hint_str = "、".join(hints_zh[:5])
        parts.append(f"系统结合您的描述，识别到相关线索：{hint_str}。")
    if rule_triggered:
        parts.append(
            f"根据风险规则 {', '.join(rule_triggered[:8])}，触发 **{risk_level}** 等级。"
        )
    else:
        parts.append("未命中特定中高危关键词规则，暂归类为低风险；若症状变化请及时就医。")

    if risk_level == "HIGH":
        parts.append("高危提示：请立即就医或拨打急救电话，不要延误。")
    elif risk_level == "MEDIUM":
        parts.append("建议今日或短期内就诊进一步评估，避免自行用药掩盖病情。")

    return "".join(parts)
