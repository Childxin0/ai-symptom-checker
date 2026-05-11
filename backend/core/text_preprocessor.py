"""
文本预处理模块 - 在关键词/规则匹配前统一处理输入文本
涵盖：
  1. 医疗英文词 → 中文映射
  2. 口语化表达 → 标准医疗词映射
  3. 否定句过滤（防止"没有发烧"误命中"发烧"规则）
此模块输出仅供内部规则匹配使用，不展示给用户。
"""
import re

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 医疗英文 → 中文（长短语优先，避免子串误覆盖）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MEDICAL_EN_CN: dict = {
    # 呼吸循环
    "chest pain": "胸痛",
    "chest tightness": "胸闷",
    "shortness of breath": "呼吸困难",
    "short of breath": "呼吸困难",
    "difficulty breathing": "呼吸困难",
    "can't breathe": "呼吸困难",
    "heart attack": "心脏病发作",
    "palpitations": "心悸",
    "palpitation": "心悸",
    "heart racing": "心跳加速",
    "cold sweat": "出冷汗",
    # 神经系统
    "stroke": "中风",
    "seizure": "抽搐",
    "fainted": "晕倒",
    "faint": "晕倒",
    "unconscious": "意识不清",
    "headache": "头痛",
    "severe headache": "剧烈头痛",
    "migraine": "偏头痛",
    "dizzy": "头晕",
    "dizziness": "头晕",
    "vertigo": "眩晕",
    # 消化
    "nausea": "恶心",
    "vomiting": "呕吐",
    "diarrhea": "腹泻",
    "abdominal pain": "腹痛",
    "stomach pain": "胃痛",
    "stomachache": "胃痛",
    "bloating": "腹胀",
    # 感染/发热
    "fever": "发烧",
    "chills": "寒战",
    "cough": "咳嗽",
    "sore throat": "喉咙痛",
    # 出血
    "bleeding": "出血",
    "blood in urine": "血尿",
    "coughing up blood": "咯血",
    # 通用疼痛
    "pain": "疼痛",
    "ache": "疼痛",
    "fatigue": "疲劳",
    "weakness": "无力",
    "swelling": "肿胀",
    "rash": "皮疹",
}

# 按长度降序排序，确保长词组先替换
_EN_CN_SORTED = sorted(MEDICAL_EN_CN.items(), key=lambda x: -len(x[0]))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 口语化表达 → 标准医疗词（精确子串替换）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COLLOQUIAL_MAP: dict = {
    # 心脏/心悸
    "心脏要跳出来": "心悸心跳很快",
    "心脏快跳出来": "心悸心跳很快",
    "心脏跳得很快": "心悸心跳很快",
    "心跳乱": "心悸",
    "心慌慌": "心慌",
    "心跳很厉害": "心悸",
    # 头痛（区分霹雳样/爆炸感 → EMERGENCY，普通剧烈 → HIGH）
    "脑袋要炸了": "突然剧烈头痛",    # 匹配 thunderclap_headache_emergency
    "头要裂开": "突然剧烈头痛",
    "头要炸了": "突然剧烈头痛",
    "头感觉快炸了": "突然剧烈头痛",
    "头痛欲裂": "剧烈头痛",
    # 呼吸
    "喘不上来气": "呼吸困难",
    "气接不上": "呼吸困难",
    "喘不过气来": "呼吸困难",
    "气喘不上": "呼吸困难",
    # 晕厥/眩晕（"快晕过去" → 晕过去，触发 syncope_emergency 的"晕过去"关键词）
    "快晕过去": "晕过去",
    "感觉要晕过去": "晕过去",
    "眼前发黑站不稳": "眩晕站不稳",
    "眼前发黑": "眩晕",
    "天旋地转站不稳": "眩晕站不稳",
    # 恶心
    "胃要翻了": "恶心",
    "要吐了": "恶心呕吐",
    # 胸痛
    "胸口像被压住": "胸口压榨感",
    "胸口压着一块石头": "胸口压榨感",
    "胸口像压了块大石": "胸口压榨感",
}

_COLLOQUIAL_SORTED = sorted(COLLOQUIAL_MAP.items(), key=lambda x: -len(x[0]))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 否定句过滤
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 否定前缀，按长度降序，避免"没有"被"没"先匹配
_NEGATION_PREFIXES = ["没有", "不是", "未出现", "没发现", "无", "没", "未"]


def filter_negations(text: str) -> str:
    """
    从文本中移除否定修饰的短语，防止"没有发烧"误命中"发烧"规则。
    此函数仅用于规则匹配前的预处理，不影响原始文本展示。

    例：'我没有发烧，但头很疼' → '我，但头很疼'
    """
    result = text
    for prefix in _NEGATION_PREFIXES:
        # 匹配: 否定前缀 + 1~8个非标点/非空白字符
        pattern = re.compile(
            re.escape(prefix) + r'[^\s，。！？、,!?]{1,8}',
            re.UNICODE
        )
        result = pattern.sub('', result)
    return result


def get_negated_terms(text: str) -> set:
    """
    从原始文本中提取被否定的词组（用于LLM结果后处理）。
    
    例：'我没有发烧，但头很疼' → {'发烧'}
        '没有胸痛，呼吸困难' → {'胸痛'}
        '不是头疼，是脖子疼' → {'头疼'}
    
    Returns:
        lowercased negated term strings
    """
    negated: set = set()
    for prefix in _NEGATION_PREFIXES:
        pattern = re.compile(
            re.escape(prefix) + r'([^\s，。！？、,!?]{1,8})',
            re.UNICODE
        )
        for match in pattern.finditer(text.lower()):
            negated.add(match.group(1))
    return negated


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 统一预处理入口
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def preprocess_for_matching(text: str) -> str:
    """
    为规则/关键词匹配准备的预处理文本（不展示给用户）。
    执行顺序：
      1. 小写化
      2. 英文医疗词 → 中文
      3. 口语化表达 → 标准术语
      4. 否定句过滤
    """
    processed = text.lower()

    # 1. 英文医疗词替换（长优先）
    for en, cn in _EN_CN_SORTED:
        if en in processed:
            processed = processed.replace(en, cn)

    # 2. 口语化表达替换（长优先）
    for colloquial, standard in _COLLOQUIAL_SORTED:
        if colloquial in processed:
            processed = processed.replace(colloquial, standard)

    # 3. 否定句过滤
    processed = filter_negations(processed)

    return processed
