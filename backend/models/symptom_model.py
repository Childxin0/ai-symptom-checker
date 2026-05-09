"""
症状分析 API 的请求 / 响应 Pydantic 模型。
"""

from typing import List

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """POST /api/analyze 请求体。"""

    user_input: str = Field(
        default="",
        description="用户自然语言症状描述（允许空串，由路由返回友好提示）",
    )


class AnalyzeResponse(BaseModel):
    """POST /api/analyze 响应体（与产品示例字段对齐）。"""

    symptoms: List[str] = Field(default_factory=list)
    duration: str = ""
    severity: str = ""
    risk_level: str = "LOW"  # LOW | MEDIUM | HIGH
    possible_department: str = ""
    advice: str = ""
    ai_rationale: str = ""
    rule_triggered: List[str] = Field(default_factory=list)
    explainability: str = ""
    fallback_used: bool = False
