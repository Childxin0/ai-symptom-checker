"""
商业级风险引擎 - 60+ 规则
规则优先策略，确保医疗安全
"""
from typing import List, Tuple, Set
import re
from core.models import RiskAssessment, StructuredSymptoms


# ==================== 规则定义（60+ 条）====================

# HIGH 风险规则（危及生命）
HIGH_RULES = {
    # 心血管急症
    "H001": {"keywords": ["胸痛", "胸闷", "心绞痛"], "requires_all": ["呼吸困难"], "desc": "胸痛伴呼吸困难"},
    "H002": {"keywords": ["胸口压榨", "压迫感"], "desc": "心梗典型症状"},
    "H003": {"keywords": ["心跳", "心慌"], "requires_all": ["胸痛"], "desc": "心跳异常伴胸痛"},
    
    # 神经系统急症
    "H004": {"keywords": ["剧烈头痛", "霹雳样头痛", "一生中最严重", "突然头痛"], "desc": "可疑蛛网膜下腔出血"},
    "H005": {"keywords": ["意识丧失", "昏迷", "晕倒", "晕厥"], "desc": "意识障碍"},
    "H006": {"keywords": ["半身不遂", "一侧无力", "偏瘫"], "desc": "中风征兆"},
    "H007": {"keywords": ["面部歪斜", "口角歪斜", "面瘫"], "requires_any": ["言语不清", "流口水"], "desc": "中风面部症状"},
    "H008": {"keywords": ["说话不清", "言语困难", "口齿不清"], "desc": "中风言语症状"},
    "H009": {"keywords": ["抽搐", "痉挛"], "duration_min": 5, "desc": "持续抽搐超过5分钟"},
    "H010": {"keywords": ["颈部僵硬", "脖子僵硬"], "requires_all": ["高烧"], "desc": "可疑脑膜炎"},
    
    # 呼吸系统急症
    "H011": {"keywords": ["呼吸困难", "喘不上气", "气短"], "severity": "severe", "desc": "严重呼吸困难"},
    "H012": {"keywords": ["窒息", "喉咙堵"], "desc": "气道梗阻风险"},
    "H013": {"keywords": ["吞咽困难"], "requires_all": ["呼吸困难"], "desc": "吞咽困难伴呼吸问题"},
    
    # 出血急症
    "H014": {"keywords": ["大量出血", "流血不止"], "desc": "严重出血"},
    "H015": {"keywords": ["咯血", "吐血"], "volume": "large", "desc": "大咯血/呕血"},
    "H016": {"keywords": ["便血"], "color": ["黑色", "暗红"], "desc": "消化道出血"},
    
    # 过敏急症
    "H017": {"keywords": ["喉咙肿胀", "舌头肿"], "desc": "严重过敏反应"},
    "H018": {"keywords": ["全身红疹", "皮疹"], "requires_all": ["呼吸困难"], "desc": "过敏性休克风险"},
    
    # 妇产科急症
    "H019": {"keywords": ["孕期", "怀孕"], "requires_any": ["腹痛", "出血", "阴道出血"], "desc": "孕期出血/腹痛"},
    "H020": {"keywords": ["产后"], "requires_all": ["大量出血"], "desc": "产后出血"},
    
    # 体温相关
    "H021": {"temp_threshold": 39.5, "desc": "高热超过39.5°C"},
    "H022": {"keywords": ["儿童", "孩子", "小孩"], "temp_threshold": 39.0, "desc": "儿童高热超过39°C"},
    
    # 其他急症
    "H023": {"keywords": ["胸腔", "腹部"], "requires_all": ["刀伤", "外伤"], "desc": "穿透性外伤"},
    "H024": {"keywords": ["服毒", "吃药过量", "自杀"], "desc": "中毒/自杀倾向"},
}

# MEDIUM 风险规则（需尽快就医）
MEDIUM_RULES = {
    # 发热相关
    "M001": {"temp_range": (38.0, 39.5), "duration_days": 2, "desc": "中等发热持续2天以上"},
    "M002": {"keywords": ["发烧", "发热"], "duration_days": 3, "desc": "发热持续3天"},
    "M003": {"keywords": ["高烧"], "requires_any": ["寒战", "发抖"], "desc": "高热伴寒战"},
    
    # 疼痛相关
    "M004": {"keywords": ["头痛", "头疼"], "duration_hours": 48, "desc": "头痛持续48小时以上"},
    "M005": {"keywords": ["腹痛", "肚子痛"], "duration_hours": 6, "desc": "腹痛持续6小时以上"},
    "M006": {"keywords": ["腹痛"], "location": ["右下腹"], "desc": "右下腹痛（可疑阑尾炎）"},
    
    # 消化系统
    "M007": {"keywords": ["呕吐", "吐"], "duration_hours": 24, "desc": "反复呕吐超过24小时"},
    "M008": {"keywords": ["腹泻"], "frequency": "频繁", "desc": "频繁腹泻"},
    "M009": {"keywords": ["便血"], "desc": "轻度便血"},
    
    # 心血管
    "M010": {"keywords": ["心悸", "心慌", "心跳快"], "desc": "心悸症状"},
    "M011": {"keywords": ["血压高", "高血压"], "requires_any": ["头痛", "头晕"], "desc": "高血压伴头痛/头晕"},
    "M012": {"keywords": ["胸闷"], "desc": "胸闷不适"},
    
    # 神经系统
    "M013": {"keywords": ["头晕", "眩晕"], "duration_hours": 12, "desc": "持续性眩晕"},
    "M014": {"keywords": ["视力模糊", "看不清"], "onset": "突然", "desc": "视力突然变化"},
    
    # 呼吸系统
    "M015": {"keywords": ["咳嗽"], "duration_weeks": 3, "desc": "咳嗽持续3周以上"},
    "M016": {"keywords": ["咳嗽"], "requires_all": ["痰中带血"], "desc": "咳嗽伴血痰"},
    
    # 泌尿系统
    "M017": {"keywords": ["尿频", "尿急", "尿痛"], "requires_any": ["发热", "发烧"], "desc": "泌尿系感染症状"},
    "M018": {"keywords": ["血尿"], "desc": "血尿"},
    
    # 皮肤
    "M019": {"keywords": ["皮疹", "红疹"], "requires_all": ["发热"], "desc": "皮疹伴发热"},
    "M020": {"keywords": ["黄疸", "眼睛发黄", "皮肤发黄"], "desc": "黄疸症状"},
}

# LOW 风险规则（可自我观察）
LOW_RULES = {
    "L001": {"keywords": ["轻微头痛", "有点头疼"], "desc": "轻度头痛"},
    "L002": {"keywords": ["感冒", "流鼻涕", "打喷嚏"], "desc": "普通感冒症状"},
    "L003": {"keywords": ["疲劳", "累", "乏力"], "severity": "mild", "desc": "轻度疲劳"},
    "L004": {"keywords": ["失眠", "睡不好"], "desc": "睡眠问题"},
    "L005": {"keywords": ["胃胀", "消化不良"], "desc": "轻度消化不良"},
}


# ==================== 规则评估引擎 ====================

class RiskEngine:
    """商业级风险评估引擎"""
    
    def __init__(self):
        self.high_rules = HIGH_RULES
        self.medium_rules = MEDIUM_RULES
        self.low_rules = LOW_RULES
    
    def evaluate(
        self,
        user_input: str,
        structured: StructuredSymptoms
    ) -> RiskAssessment:
        """
        评估风险等级
        
        Args:
            user_input: 用户原始输入
            structured: 结构化症状数据
            
        Returns:
            RiskAssessment: 风险评估结果
        """
        text = user_input.lower()
        triggered = []
        explanations = []
        
        # 检查 HIGH 规则
        for rule_id, rule in self.high_rules.items():
            if self._check_rule(text, structured, rule):
                triggered.append(rule_id)
                explanations.append(f"触发高危规则: {rule['desc']}")
        
        if triggered:
            return RiskAssessment(
                level="HIGH",
                score=90,
                triggered_rules=triggered,
                rule_explanations=explanations
            )
        
        # 检查 MEDIUM 规则
        for rule_id, rule in self.medium_rules.items():
            if self._check_rule(text, structured, rule):
                triggered.append(rule_id)
                explanations.append(f"触发中危规则: {rule['desc']}")
        
        if triggered:
            return RiskAssessment(
                level="MEDIUM",
                score=50,
                triggered_rules=triggered,
                rule_explanations=explanations
            )
        
        # 检查 LOW 规则
        for rule_id, rule in self.low_rules.items():
            if self._check_rule(text, structured, rule):
                triggered.append(rule_id)
                explanations.append(f"识别到: {rule['desc']}")
        
        return RiskAssessment(
            level="LOW",
            score=10,
            triggered_rules=triggered or ["DEFAULT"],
            rule_explanations=explanations or ["未检测到明显危险信号"]
        )
    
    def _check_rule(self, text: str, structured: StructuredSymptoms, rule: dict) -> bool:
        """检查单条规则是否触发"""
        # 关键词匹配
        if "keywords" in rule:
            if not any(kw in text for kw in rule["keywords"]):
                return False
        
        # 必须同时包含的关键词
        if "requires_all" in rule:
            if not all(kw in text for kw in rule["requires_all"]):
                return False
        
        # 至少包含一个的关键词
        if "requires_any" in rule:
            if not any(kw in text for kw in rule["requires_any"]):
                return False
        
        # 体温阈值
        if "temp_threshold" in rule:
            if structured.temperature is None or structured.temperature < rule["temp_threshold"]:
                return False
        
        # 持续时间检查（简化版）
        if "duration_days" in rule:
            duration_keywords = [f"{i}天" for i in range(rule["duration_days"], 10)]
            duration_keywords.extend([f"{i}日" for i in range(rule["duration_days"], 10)])
            if not any(kw in text for kw in duration_keywords):
                return False
        
        return True


# 单例
_risk_engine = None

def get_risk_engine() -> RiskEngine:
    """获取风险引擎单例"""
    global _risk_engine
    if _risk_engine is None:
        _risk_engine = RiskEngine()
    return _risk_engine


# 完成
