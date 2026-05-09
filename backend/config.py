"""
环境变量与全局配置（Anthropic API、模型名称等）。
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """从环境变量或 .env 加载配置。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    # 本地开发前端地址，用于 CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    llm_timeout_seconds: float = 45.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
