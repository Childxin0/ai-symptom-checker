"""
API 路由 - 商业级标准
支持主分析接口和追问接口
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import time
import asyncio

from core.models import AnalyzeRequest, FollowupRequest, AnalysisResult
from core.llm_service import get_llm_service
from core.risk_engine import get_risk_engine
from core.session_manager import get_session_manager
from core.fallback import create_fallback_structured, create_fallback_analysis, create_safe_fallback_result
from core.config import get_settings

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResult)
async def analyze_symptoms(request: AnalyzeRequest):
    """
    主分析接口 - 症状结构化 + 风险评估
    """
    start_time = time.time()
    settings = get_settings()
    
    try:
        user_input = request.user_input.strip()
        if not user_input:
            raise HTTPException(status_code=400, detail="症状描述不能为空")
        
        llm_service = get_llm_service()
        risk_engine = get_risk_engine()
        session_manager = get_session_manager()
        
        # 第一阶段：症状结构化
        structured, error = await llm_service.structure_symptoms(user_input)
        llm_used = True
        
        if not structured:
            # Layer 1 降级：LLM失败，使用关键词提取
            structured = create_fallback_structured(user_input)
            llm_used = False
        
        # 规则引擎评估（规则优先）
        risk = risk_engine.evaluate(user_input, structured)
        
        # 第二阶段：生成分析和建议
        if llm_used:
            analysis, error = await llm_service.generate_analysis(user_input, structured, risk)
            if not analysis:
                # Layer 2 降级：分析生成失败
                analysis = create_fallback_analysis(risk.level, risk.triggered_rules)
                llm_used = False
        else:
            # 使用降级分析
            analysis = create_fallback_analysis(risk.level, risk.triggered_rules)
        
        # 生成追问（如果需要）
        needs_followup = False
        followup_questions = []
        
        if llm_used and risk.level != "HIGH" and settings.max_followup_rounds > 0:
            followup_questions = await llm_service.generate_followup_questions(
                user_input, structured, risk
            )
            needs_followup = len(followup_questions) > 0
        
        # 构建结果
        result = AnalysisResult(
            session_id=request.session_id or None,  # 新会话会自动生成
            structured=structured,
            risk=risk,
            advice=analysis["advice"],
            rationale=analysis["rationale"],
            explainability=analysis["explainability"],
            recommended_department=analysis["recommended_department"],
            urgency_timeline=analysis["urgency_timeline"],
            needs_followup=needs_followup,
            followup_questions=followup_questions,
            followup_round=0,
            processing_time_ms=int((time.time() - start_time) * 1000),
            llm_used=llm_used,
            fallback_reason=None if llm_used else "LLM不可用或降级"
        )
        
        # 保存会话
        session_manager.create_session(result.session_id)
        session_manager.update_session(
            result.session_id,
            user_input=user_input,
            analysis_result=result.dict()
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        # Layer 3 降级：最后防线
        print(f"分析异常: {e}")
        return create_safe_fallback_result(
            request.user_input,
            reason=f"系统异常: {str(e)[:100]}"
        )


@router.post("/followup", response_model=AnalysisResult)
async def answer_followup(request: FollowupRequest):
    """
    追问接口 - 基于用户回答重新分析
    """
    start_time = time.time()
    
    try:
        session_manager = get_session_manager()
        session = session_manager.get_session(request.session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在或已过期")
        
        if not session_manager.can_followup(request.session_id):
            raise HTTPException(status_code=400, detail="已达到最大追问次数或风险等级不允许追问")
        
        # 合并原始输入和追问回答
        original_input = " ".join(session.user_inputs)
        combined_input = f"{original_input}\n追加信息：{request.followup_answer}"
        
        # 记录追问QA
        if len(session.analysis_results) > 0:
            last_analysis = session.analysis_results[-1]
            if "followup_questions" in last_analysis and request.question_index < len(last_analysis["followup_questions"]):
                question = last_analysis["followup_questions"][request.question_index]
                session_manager.update_session(
                    request.session_id,
                    followup_qa={
                        "question": question["question"],
                        "answer": request.followup_answer
                    }
                )
        
        # 重新分析（使用合并后的信息）
        llm_service = get_llm_service()
        risk_engine = get_risk_engine()
        
        # 结构化
        structured, _ = await llm_service.structure_symptoms(combined_input)
        if not structured:
            structured = create_fallback_structured(combined_input)
        
        # 风险评估
        risk = risk_engine.evaluate(combined_input, structured)
        
        # 生成分析
        analysis, _ = await llm_service.generate_analysis(combined_input, structured, risk)
        if not analysis:
            analysis = create_fallback_analysis(risk.level, risk.triggered_rules)
        
        # 判断是否继续追问
        can_continue = session_manager.can_followup(request.session_id)
        needs_followup = False
        followup_questions = []
        
        if can_continue and risk.level != "HIGH":
            followup_questions = await llm_service.generate_followup_questions(
                combined_input, structured, risk
            )
            needs_followup = len(followup_questions) > 0
        
        # 构建结果
        result = AnalysisResult(
            session_id=request.session_id,
            structured=structured,
            risk=risk,
            advice=analysis["advice"],
            rationale=analysis["rationale"],
            explainability=analysis["explainability"],
            recommended_department=analysis["recommended_department"],
            urgency_timeline=analysis["urgency_timeline"],
            needs_followup=needs_followup,
            followup_questions=followup_questions,
            followup_round=session.followup_count + 1,
            processing_time_ms=int((time.time() - start_time) * 1000),
            llm_used=True,
            fallback_reason=None
        )
        
        # 更新会话
        session_manager.update_session(
            request.session_id,
            user_input=request.followup_answer,
            analysis_result=result.dict()
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"追问异常: {e}")
        return create_safe_fallback_result(
            request.followup_answer if hasattr(request, 'followup_answer') else "",
            reason=f"追问处理异常: {str(e)[:100]}"
        )


@router.get("/health")
async def health_check():
    """健康检查"""
    settings = get_settings()
    return {
        "status": "ok",
        "llm_available": bool(settings.anthropic_api_key),
        "model": settings.anthropic_model
    }


# 完成
