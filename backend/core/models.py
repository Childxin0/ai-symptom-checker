"""
数据模型 - 商业级标准
使用 Pydantic V2，严格类型定义
"""
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


# ==================== 请求模型 ====================

class AnalyzeRequest(BaseModel):
    """症状分析请求"""
    user_input: str = Field(..., min_length=1, max_length=2000, description="用户症状描述")
    session_id: Optional[str] = Field(None, description="会话ID（用于多轮追问）")


class FollowupRequest(BaseModel):
    """追问回答请求"""
    session_id: str = Field(..., description="会话ID")
    followup_answer: str = Field(..., min_length=1, max_length=500, description="追问答案")
    question_index: int = Field(..., ge=0, description="回答的问题索引")


# ==================== 结构化输出模型 ====================

class StructuredSymptoms(BaseModel):
    """第一阶段：症状结构化输出（LLM 生成）"""
    symptoms: List[str] = Field(default_factory=list, description="症状列表")
    duration: str = Field("", description="持续时间")
    severity: str = Field("", description="严重程度：轻度/中度/重度")
    body_location: str = Field("", description="身体部位")
    accompanying_symptoms: List[str] = Field(default_factory=list, description="伴随症状")
    medical_history_mentioned: bool = Field(False, description="是否提及病史")
    symptom_onset: str = Field("", description="发病方式：突发/渐进/不确定")
    temperature: Optional[float] = Field(None, description="体温（如有）")
    additional_context: str = Field("", description="其他重要信息")


# ==================== 响应模型 ====================

class RiskAssessment(BaseModel):
    """风险评估结果"""
    level: Literal["LOW", "MEDIUM", "HIGH", "EMERGENCY"] = Field("LOW", description="风险等级")
    score: int = Field(0, ge=0, le=100, description="风险分数（0-100）")
    triggered_rules: List[str] = Field(default_factory=list, description="触发的规则ID列表")
    rule_explanations: List[str] = Field(default_factory=list, description="规则解释（中文）")


class FollowupQuestion(BaseModel):
    """追问问题"""
    question: str = Field(..., description="追问问题文本")
    category: str = Field(..., description="问题分类：time/severity/location/accompanying")
    options: Optional[List[str]] = Field(None, description="选项列表（如适用）")
    question_type: Literal["yn", "duration", "severity", "location", "open"] = Field(
        "yn",
        description=(
            "问题类型，决定快捷按钮样式："
            "yn=是/否/不确定, duration=时间选项, severity=严重程度,"
            "location=部位选项, open=纯文本输入"
        ),
    )


class AnalysisResult(BaseModel):
    """完整分析结果（返回给前端）"""
    # 会话信息
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # 输入验证
    input_type: Literal["valid_symptom", "insufficient_symptom", "non_medical_input"] = Field(
        "valid_symptom", 
        description="输入类型：valid_symptom=有效症状，insufficient_symptom=信息不足，non_medical_input=非医疗输入"
    )
    input_validation_message: str = Field("", description="输入验证提示信息")
    
    # 结构化症状
    structured: Optional[StructuredSymptoms] = Field(None, description="症状结构化结果（仅当input_type=valid_symptom时有值）")
    
    # 风险评估
    risk: Optional[RiskAssessment] = Field(None, description="风险评估结果（仅当input_type=valid_symptom时有值）")
    
    # AI 生成内容
    advice: str = Field("", description="就诊建议（自然语言）")
    rationale: str = Field("", description="AI 推理过程")
    explainability: str = Field("", description="用户友好的解释说明")
    recommended_department: str = Field("", description="推荐就诊科室")
    urgency_timeline: str = Field("", description="紧急程度时间线")
    
    # 追问系统
    needs_followup: bool = Field(False, description="是否需要追问")
    followup_questions: List[FollowupQuestion] = Field(default_factory=list)
    followup_round: int = Field(0, description="当前追问轮次")
    
    # 元信息
    processing_time_ms: int = Field(0, description="处理耗时（毫秒）")
    llm_used: bool = Field(False, description="是否使用了 LLM")
    fallback_reason: Optional[str] = Field(None, description="降级原因（如有）")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ==================== 会话模型 ====================

class SessionData(BaseModel):
    """会话数据（用于多轮追问）"""
    session_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # 历史记录
    user_inputs: List[str] = Field(default_factory=list)
    analysis_results: List[Dict[str, Any]] = Field(default_factory=list)
    followup_qa_pairs: List[Dict[str, str]] = Field(default_factory=list)
    
    # 累积信息
    all_symptoms: List[str] = Field(default_factory=list)
    current_risk_level: str = "LOW"
    followup_count: int = 0


# 完成
