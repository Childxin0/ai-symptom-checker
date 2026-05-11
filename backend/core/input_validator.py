"""
输入意图识别模块 v2 — LLM 驱动 + 规则兜底

架构（三层）：
  Layer 1  快速规则预筛
           只拦截"主题明确为技术/求职/学习"且不含身体症状信号的输入
           → 命中且无症状信号 → non_medical_input（不调用 LLM，0ms 延迟）
           → 命中但有症状信号（混合输入）→ 进入 Layer 2

  Layer 2  LLM 意图分类
           调用 Claude 判断，覆盖关键词库无法覆盖的长尾场景
           （妇科口语/儿童老人/方言/混合输入/心理健康危机等）

  Layer 3  关键词 Fallback
           LLM 不可用或调用失败时，回退原关键词规则保证系统可用
"""
from __future__ import annotations

import re
from typing import Literal, Tuple

from core.text_preprocessor import preprocess_for_matching

InputType = Literal["valid_symptom", "insufficient_symptom", "non_medical_input"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Layer 1 — 明确非医疗词（快速规则预筛）
# 仅包含与健康完全无关的技术/求职/产品关键词
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_CLEARLY_NON_MEDICAL: frozenset = frozenset({
    # 编程/技术
    "代码", "编程", "python", "java", "javascript", "typescript",
    "react", "vue", "angular", "nextjs", "nuxt",
    "api", "数据库", "前端", "后端", "部署", "vercel", "github",
    "docker", "kubernetes", "git", "npm", "pip", "kubectl",
    "readme", "函数", "变量", "算法", "debug", "bug",
    # 求职/职场
    "简历", "面试技巧", "求职", "公司运营", "团队管理",
    "绩效考核", "晋升计划", "kpi", "okr",
    # 产品/设计
    "prd", "产品经理", "需求文档", "架构设计", "技术方案",
    "roadmap", "sprint", "小程序设计",
    # 学习/教育
    "课程学习", "考试题", "论文写作", "作业帮助",
    # 打招呼（纯问候无内容）
    "你好", "谢谢", "再见",
    # 系统操作
    "系统安装", "软件配置",
})

# 若输入同时含有以下症状信号词，则不拦截（混合输入优先健康）
_SYMPTOM_SIGNALS: frozenset = frozenset({
    "疼", "痛", "酸", "胀", "麻", "痒",
    "晕", "恶心", "发烧", "发热", "咳嗽", "呕吐",
    "喘", "呼吸", "胸闷", "心慌", "出血", "流血",
    "难受", "不舒服", "不适",
    "疲劳", "乏力", "累",
    "失眠", "睡不着", "焦虑", "抑郁",
    "月经", "白带", "怀孕", "痛经",
    "头", "胸", "腹", "肚子", "胃", "背", "腰",
    "脖子", "肩", "眼", "耳", "牙", "腿",
    # 言语/神经（中风等）
    "说话", "言语",
    # 意识状态（药物过量/中毒）
    "意识", "昏沉", "嗜睡",
    # 儿童/老人代称
    "孩子", "小孩", "宝宝", "老人",
})


def _has_clearly_non_medical(text: str) -> bool:
    t = text.lower()
    for kw in _CLEARLY_NON_MEDICAL:
        if kw.lower() in t:
            return True
    # 明确非医疗 pattern
    non_medical_patterns = [
        r"如何.*部署",
        r"怎么.*配置",
        r"帮我.*写.*简历",
        r"帮我.*写.*代码",
        r".*简历.*",
        r".*面试.*技巧",
        r"学.*编程",
        r".*代码.*实现",
        r"什么是.*（架构|协议|框架|算法|设计模式）",
    ]
    for pat in non_medical_patterns:
        if re.search(pat, text):
            return True
    return False


def _has_symptom_signal(text: str) -> bool:
    for kw in _SYMPTOM_SIGNALS:
        if kw in text:
            return True
    return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Layer 3 — 关键词 Fallback（LLM 不可用时）
# 保留原有关键词逻辑
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SYMPTOM_KEYWORDS = frozenset({
    "疼", "痛", "酸", "胀", "麻", "痒", "刺痛", "绞痛", "钝痛", "隐痛",
    "难受", "不舒服", "不适", "不好", "感觉不对",
    "发烧", "发热", "咳嗽", "咳", "喘", "呕吐", "吐", "拉肚子", "腹泻",
    "恶心", "头晕", "眩晕", "乏力", "疲劳", "累",
    "流鼻涕", "鼻塞", "打喷嚏", "嗓子", "喉咙",
    "出血", "流血", "昏迷", "晕倒", "抽搐", "呼吸困难", "呼吸", "窒息",
    "胸痛", "胸闷", "心慌", "心悸",
    "头", "胸", "腹", "肚子", "胃", "背", "腰", "腿", "手", "脚",
    "眼睛", "眼", "耳", "鼻", "嘴", "牙", "颈", "脖子", "肩",
    "皮肤", "阴道", "尿道",
    "体温", "度", "℃", "血压", "心跳", "血糖",
    "肿", "红", "热", "冷", "麻木", "无力", "僵硬", "发黄", "发紫", "苍白",
    "伤", "摔", "撞", "扭", "割", "烫", "烧", "咬",
    "失眠", "睡不着", "入睡", "睡眠", "焦虑", "紧张", "抑郁", "烦躁",
    "情绪", "恐慌", "心情",
    # 泌尿妇科 / 生殖健康
    "尿", "月经", "例假", "大姨妈", "生理期", "经期", "经血", "经痛", "痛经",
    "白带", "分泌物", "阴道", "外阴", "排卵",
    "怀孕", "妊娠", "备孕", "停经", "闭经",
    "疹", "皮疹", "痘", "斑", "癣", "湿疹", "荨麻疹",
    "便", "大便", "粪", "黑便", "柏油",
    # 神经/言语症状（中风等老人/儿童场景）
    "说话", "言语", "表达", "口齿",
    # 意识状态（药物过量/中毒场景）
    "意识", "昏沉", "嗜睡",
    # 儿童/老人场景
    "孩子", "小孩", "婴儿", "宝宝", "老人", "老年人", "父母",
})

EMERGENCY_KEYWORDS = frozenset({
    "车祸", "撞车", "被车撞", "交通事故", "坠落", "摔下", "高处跌落",
    "大出血", "大量出血", "流血不止", "止不住血", "出血很多",
    "呼吸困难", "喘不上气", "窒息", "憋气",
    "胸痛", "胸口痛", "心口痛", "压榨", "压榨感",
    "出冷汗", "冷汗", "大汗",
    "昏迷", "意识不清", "意识模糊", "神志不清", "晕倒", "叫不醒", "不省人事",
    "抽搐", "痉挛", "口吐白沫",
    "自杀", "想死", "不想活", "割腕", "结束生命",
    # 药物过量 / 中毒（全量覆盖，不依赖 LLM）
    "中毒", "误服", "吃错药", "药物过量", "安眠药",
    "吃了很多药", "吃了大量药", "吃了一大把药", "服药过多",
    "吞药", "吞了很多药", "吞了大量药",
    "吐血", "呕血", "咯血",
    "骨折", "骨头断",
    "产后大出血",
})

HEALTH_CONCERN_PHRASES = frozenset({
    "不舒服", "难受", "不好", "不对劲", "怪", "异常",
    "不太好", "感觉不适", "有点问题", "哪里不对",
    "身体", "健康", "病", "症状",
    "感觉不", "感觉有", "感觉很",
    "焦虑", "抑郁", "紧张", "烦躁", "失眠", "睡不着",
    "恐慌", "心情", "情绪", "压力",
    "发黄", "发紫", "水肿", "浮肿", "消瘦", "变瘦",
    # 生殖/妇科
    "月经", "例假", "大姨妈", "生理期", "经期", "经血", "经痛", "痛经",
    "怀孕", "妊娠", "备孕", "停经", "闭经", "排卵",
    "白带", "阴道", "外阴", "子宫", "卵巢",
})


def _keyword_fallback(text: str) -> Tuple[InputType, str]:
    """Layer 3：关键词规则兜底"""
    # 紧急症状直接通过
    for kw in EMERGENCY_KEYWORDS:
        if kw in text:
            return "valid_symptom", ""

    has_symptom = any(kw in text for kw in SYMPTOM_KEYWORDS)
    has_health = any(p in text for p in HEALTH_CONCERN_PHRASES)
    word_count = len(text)

    if has_symptom or has_health:
        # 判断是否信息充分
        vague = {"不舒服", "难受", "不适", "不好", "怪", "异常"}
        specific = sum(1 for kw in SYMPTOM_KEYWORDS if kw in text and kw not in vague)
        if specific >= 2:
            return "valid_symptom", ""
        detail_patterns = [
            r"\d+",
            r"(很|非常|特别|极其|有点|轻微|严重|剧烈)",
            r"(天|日|小时|分钟|周|月)",
            r"(左|右|上|下|前|后|中)",
            r"(一直|持续|反复|偶尔|突然|最近|已经|好几)",
        ]
        has_detail = any(re.search(p, text) for p in detail_patterns)
        if specific >= 1 and has_detail:
            return "valid_symptom", ""
        if word_count < 10:
            return "insufficient_symptom", "请补充更多信息：具体哪里不舒服？持续多久了？"
        return "insufficient_symptom", "请补充具体症状：部位？时间？程度？"

    return "non_medical_input", "未识别到症状相关内容。请描述您的具体身体不适。"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 主入口（async）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def validate_input(user_input: str) -> Tuple[InputType, str]:
    """
    三层意图识别入口（async）

    Layer 1  快速规则预筛 — 纯非医疗且无症状信号 → non_medical_input（0ms）
    Layer 2  LLM 意图分类 — Claude 精准判断
    Layer 3  关键词 Fallback — LLM 不可用时保底
    """
    if not user_input or not user_input.strip():
        return "non_medical_input", "请输入您的症状描述"

    # 预处理文本供规则匹配（否定句过滤 + 英文映射）
    text = preprocess_for_matching(user_input)

    # ── Layer 1：快速规则预筛 ─────────────────────────────────────────
    if _has_clearly_non_medical(text):
        if not _has_symptom_signal(text):
            return (
                "non_medical_input",
                "当前输入不像症状描述。本系统用于医疗症状初筛，请描述您的身体不适。",
            )
        # 有症状信号 → 混合输入，跳过规则拦截，交给 LLM

    # ── Layer 2：LLM 意图分类 ─────────────────────────────────────────
    try:
        from core.llm_service import get_llm_service
        llm_service = get_llm_service()
        input_type, confidence, reason = await llm_service.classify_intent(user_input)

        if input_type == "non_medical_input":
            return (
                "non_medical_input",
                "当前输入不像症状描述。本系统用于医疗症状初筛，请描述您的身体不适。",
            )
        elif input_type == "insufficient_symptom":
            return (
                "insufficient_symptom",
                "请补充更多信息：具体哪里不舒服？持续多久了？严重程度如何？",
            )
        else:  # valid_symptom
            return "valid_symptom", ""

    except Exception as e:
        print(f"[InputValidator] LLM 分类失败，回退关键词规则: {e}")

    # ── Layer 3：关键词 Fallback ──────────────────────────────────────
    return _keyword_fallback(text)


# ── 向后兼容：同步版本供测试脚本使用 ────────────────────────────────────
def validate_input_sync(user_input: str) -> Tuple[InputType, str]:
    """同步包装，仅供测试/脚本调用"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 在已有事件循环内（FastAPI）不应调用此版本
            raise RuntimeError("请在 async 上下文中使用 await validate_input()")
        return loop.run_until_complete(validate_input(user_input))
    except RuntimeError:
        # 完全兜底：直接跑关键词规则
        text = preprocess_for_matching(user_input)
        if _has_clearly_non_medical(text) and not _has_symptom_signal(text):
            return "non_medical_input", "非医疗输入"
        return _keyword_fallback(text)
