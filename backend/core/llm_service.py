"""
LLM 服务 - 真实 Anthropic Claude 调用
两阶段 Pipeline：症状结构化 → 风险解释生成
"""
import json
import re
from typing import Optional, Tuple
from anthropic import Anthropic, AsyncAnthropic
import asyncio

from core.config import get_settings
from core.models import StructuredSymptoms, RiskAssessment, FollowupQuestion


class LLMService:
    """LLM 调用服务（商业级）"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        if self.settings.anthropic_api_key:
            self.client = Anthropic(api_key=self.settings.anthropic_api_key)
    
    async def structure_symptoms(self, user_input: str) -> Tuple[Optional[StructuredSymptoms], Optional[str]]:
        """
        第一阶段：症状结构化
        
        Returns:
            (StructuredSymptoms | None, error_message | None)
        """
        if not self.client:
            return None, "未配置 ANTHROPIC_API_KEY"
        
        prompt = f"""你是医疗初筛系统的症状分析助手。请将用户的症状描述转换为结构化JSON。

用户描述：
{user_input}

请输出严格的JSON格式（不要markdown代码块）：
{{
  "symptoms": ["列出识别到的所有症状"],
  "duration": "持续时间描述",
  "severity": "轻度/中度/重度/未知",
  "body_location": "身体部位",
  "accompanying_symptoms": ["伴随症状列表"],
  "medical_history_mentioned": true/false,
  "symptom_onset": "突发/渐进/不确定",
  "temperature": 体温数值（如有）或null,
  "additional_context": "其他重要信息"
}}

要求：
1. symptoms 必须包含所有提到的症状
2. 从文本中提取体温数值（如"38.5度"→38.5）
3. 准确判断发病方式和严重程度
4. 只输出JSON，不要额外解释"""

        try:
            message = self.client.messages.create(
                model=self.settings.anthropic_model,
                max_tokens=1024,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # 提取JSON
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                return StructuredSymptoms(**data), None
            else:
                return None, "LLM返回格式错误"
                
        except Exception as e:
            return None, f"LLM调用失败: {str(e)}"
    
    async def generate_analysis(
        self,
        user_input: str,
        structured: StructuredSymptoms,
        risk: RiskAssessment
    ) -> Tuple[Optional[dict], Optional[str]]:
        """
        第二阶段：生成风险解释和建议
        
        Returns:
            (analysis_dict | None, error_message | None)
            analysis_dict 包含: advice, rationale, explainability, recommended_department, urgency_timeline
        """
        if not self.client:
            return None, "未配置 ANTHROPIC_API_KEY"
        
        symptoms_text = "、".join(structured.symptoms) if structured.symptoms else "无明显症状"
        rules_text = "\n".join(risk.rule_explanations) if risk.rule_explanations else "无"
        
        prompt = f"""你是医疗初筛AI。基于以下信息生成专业的分析报告。

【用户原始描述】
{user_input}

【结构化症状】
症状列表：{symptoms_text}
持续时间：{structured.duration}
严重程度：{structured.severity}
体温：{structured.temperature}°C（如有）
发病方式：{structured.symptom_onset}

【规则引擎判定】
风险等级：{risk.level}
触发规则：
{rules_text}

请生成JSON格式的分析报告（不要markdown代码块）：
{{
  "advice": "详细的就诊建议（自然语言，150-300字）",
  "rationale": "AI推理过程（说明为什么得出该结论，100-200字）",
  "explainability": "面向普通用户的解释（通俗易懂，150-250字）",
  "recommended_department": "推荐科室（如'心内科'、'急诊科'）",
  "urgency_timeline": "紧急程度（如'立即就医'、'24小时内'、'3天内'、'可观察'）"
}}

重要要求：
1. advice 必须根据风险等级给出明确建议：
   - HIGH: 必须包含"立即就医"或"拨打120"
   - MEDIUM: 建议"尽快就医"或"24-48小时内就诊"
   - LOW: 可建议"观察"但需告知何时应就医
   
2. explainability 要点名触发的规则，用通俗语言解释

3. 所有内容用中文，语气专业但易懂

4. 只输出JSON，不要额外文字"""

        try:
            message = self.client.messages.create(
                model=self.settings.anthropic_model,
                max_tokens=2048,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # 提取JSON
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                return data, None
            else:
                return None, "LLM返回格式错误"
                
        except Exception as e:
            return None, f"LLM调用失败: {str(e)}"
    
    async def generate_followup_questions(
        self,
        user_input: str,
        structured: StructuredSymptoms,
        risk: RiskAssessment
    ) -> list[FollowupQuestion]:
        """
        生成追问问题
        
        Returns:
            追问问题列表（最多2个）
        """
        if not self.client or risk.level == "HIGH":
            return []  # HIGH 不追问，直接就医
        
        prompt = f"""你是医疗初筛AI。基于当前信息，生成1-2个关键追问问题。

【用户描述】
{user_input}

【已知症状】
{", ".join(structured.symptoms) if structured.symptoms else "无"}

【当前风险】
{risk.level}

请生成JSON格式的追问问题（不要markdown）：
[
  {{
    "question": "追问问题文本（自然语言）",
    "category": "time/severity/location/accompanying",
    "options": ["选项1", "选项2", "选项3"] 或 null（如果是开放问题）
  }}
]

要求：
1. 最多2个问题
2. 问题要有助于判断风险等级
3. category 必须是 time/severity/location/accompanying 之一
4. 如果适合用选项回答，提供3个选项
5. 只输出JSON数组"""

        try:
            message = self.client.messages.create(
                model=self.settings.anthropic_model,
                max_tokens=512,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # 提取JSON数组
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                return [FollowupQuestion(**q) for q in data[:2]]  # 最多2个
            else:
                return []
                
        except Exception as e:
            print(f"生成追问失败: {e}")
            return []


# 单例
_llm_service = None

def get_llm_service() -> LLMService:
    """获取LLM服务单例"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


# 完成
