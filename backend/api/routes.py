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
from core.input_validator import validate_input
from core.text_preprocessor import get_negated_terms, preprocess_for_matching

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
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 输入意图识别：过滤非症状文本
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        input_type, validation_message = await validate_input(user_input)
        
        if input_type == "non_medical_input":
            # 非医疗输入：不进行分析，直接返回提示
            processing_time = int((time.time() - start_time) * 1000)
            result = AnalysisResult(
                input_type=input_type,
                input_validation_message=validation_message,
                structured=None,
                risk=None,
                advice="",
                rationale="",
                explainability="",
                recommended_department="",
                urgency_timeline="",
                processing_time_ms=processing_time,
                llm_used=False,
            )
            if request.session_id:
                result.session_id = request.session_id
            return result
        
        elif input_type == "insufficient_symptom":
            # 信息不足：生成追问
            processing_time = int((time.time() - start_time) * 1000)
            
            # 生成基础追问问题（附带 question_type 决定前端按钮样式）
            from core.models import FollowupQuestion
            followup_questions = [
                FollowupQuestion(
                    question="请描述具体的不适部位（如：头部、胸部、腹部等）",
                    category="location",
                    question_type="location",
                ),
                FollowupQuestion(
                    question="症状持续了多久？",
                    category="time",
                    question_type="duration",
                ),
                FollowupQuestion(
                    question="症状的严重程度如何？",
                    category="severity",
                    question_type="severity",
                ),
                FollowupQuestion(
                    question="是否有其他伴随症状？（如：发热、恶心、头晕等）",
                    category="accompanying",
                    question_type="yn",
                ),
            ]
            
            result = AnalysisResult(
                input_type=input_type,
                input_validation_message=validation_message,
                structured=None,
                risk=None,
                advice="",
                rationale="",
                explainability="",
                recommended_department="",
                urgency_timeline="",
                needs_followup=True,
                followup_questions=followup_questions,
                processing_time_ms=processing_time,
                llm_used=False,
            )
            if request.session_id:
                result.session_id = request.session_id
            return result
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 有效症状输入：进入完整分析流程
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        llm_service = get_llm_service()
        risk_engine = get_risk_engine()
        session_manager = get_session_manager()
        
        # 预计算：预处理后的文本（否定句已过滤），供 fallback 使用
        preprocessed_input = preprocess_for_matching(user_input)

        # 第一阶段：症状结构化
        structured, error = await llm_service.structure_symptoms(user_input)
        llm_used = True

        if not structured:
            # Layer 1 降级：LLM失败，用预处理后的文本提取关键词（否定词已移除）
            structured = create_fallback_structured(preprocessed_input)
            llm_used = False
        else:
            # LLM 路径：对 LLM 结果做否定句后处理（防止 LLM 偶发错误提取被否定症状）
            negated = get_negated_terms(user_input)
            if negated:
                def _is_negated(symptom_str: str) -> bool:
                    s = symptom_str.lower()
                    return any(neg in s for neg in negated)
                if structured.symptoms:
                    structured.symptoms = [s for s in structured.symptoms if not _is_negated(s)]
                if structured.accompanying_symptoms:
                    structured.accompanying_symptoms = [
                        s for s in structured.accompanying_symptoms if not _is_negated(s)
                    ]

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
        result_kwargs = {
            "input_type": "valid_symptom",  # 已通过验证，是有效症状
            "input_validation_message": "",
            "structured": structured,
            "risk": risk,
            "advice": analysis["advice"],
            "rationale": analysis["rationale"],
            "explainability": analysis["explainability"],
            "recommended_department": analysis["recommended_department"],
            "urgency_timeline": analysis["urgency_timeline"],
            "needs_followup": needs_followup,
            "followup_questions": followup_questions,
            "followup_round": 0,
            "processing_time_ms": int((time.time() - start_time) * 1000),
            "llm_used": llm_used,
            "fallback_reason": None if llm_used else "LLM不可用或降级"
        }
        
        # 如果提供了session_id，使用它；否则让模型自动生成
        if request.session_id:
            result_kwargs["session_id"] = request.session_id
            
        result = AnalysisResult(**result_kwargs)
        
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
