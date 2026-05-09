"""
配置管理 - 商业级标准
从环境变量加载配置，支持多环境
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置（从 .env 加载）"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # Anthropic API 配置
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    anthropic_timeout: float = 30.0  # 商业级超时设置
    
    # API 配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    
    # 业务配置
    max_followup_rounds: int = 3  # 最多追问轮数
    session_timeout_minutes: int = 30  # 会话超时时间
    
    @property
    def cors_origins_list(self) -> List[str]:
        """解析 CORS 来源列表"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 完成
