"""
会话管理 - 支持多轮追问
使用内存存储（商业版可换成 Redis）
"""
from typing import Optional, Dict
from datetime import datetime, timedelta
from core.models import SessionData
from core.config import get_settings


class SessionManager:
    """会话管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionData] = {}
        self.settings = get_settings()
    
    def create_session(self, session_id: str) -> SessionData:
        """创建新会话"""
        session = SessionData(session_id=session_id)
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """获取会话"""
        session = self.sessions.get(session_id)
        
        if session:
            # 检查是否超时
            timeout = timedelta(minutes=self.settings.session_timeout_minutes)
            if datetime.now() - session.updated_at > timeout:
                del self.sessions[session_id]
                return None
        
        return session
    
    def update_session(
        self,
        session_id: str,
        user_input: Optional[str] = None,
        analysis_result: Optional[dict] = None,
        followup_qa: Optional[Dict[str, str]] = None
    ) -> None:
        """更新会话数据"""
        session = self.get_session(session_id)
        if not session:
            return
        
        if user_input:
            session.user_inputs.append(user_input)
        
        if analysis_result:
            session.analysis_results.append(analysis_result)
            
            # 更新累积症状
            if "structured" in analysis_result and "symptoms" in analysis_result["structured"]:
                for symptom in analysis_result["structured"]["symptoms"]:
                    if symptom not in session.all_symptoms:
                        session.all_symptoms.append(symptom)
            
            # 更新风险等级
            if "risk" in analysis_result and "level" in analysis_result["risk"]:
                session.current_risk_level = analysis_result["risk"]["level"]
        
        if followup_qa:
            session.followup_qa_pairs.append(followup_qa)
            session.followup_count += 1
        
        session.updated_at = datetime.now()
    
    def can_followup(self, session_id: str) -> bool:
        """检查是否可以继续追问"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        # 检查追问次数限制
        if session.followup_count >= self.settings.max_followup_rounds:
            return False
        
        # HIGH 风险不追问
        if session.current_risk_level == "HIGH":
            return False
        
        return True
    
    def cleanup_old_sessions(self) -> None:
        """清理过期会话（定期调用）"""
        timeout = timedelta(minutes=self.settings.session_timeout_minutes)
        now = datetime.now()
        
        expired_ids = [
            sid for sid, session in self.sessions.items()
            if now - session.updated_at > timeout
        ]
        
        for sid in expired_ids:
            del self.sessions[sid]


# 单例
_session_manager = None

def get_session_manager() -> SessionManager:
    """获取会话管理器单例"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


# 完成
