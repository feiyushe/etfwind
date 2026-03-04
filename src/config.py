"""配置管理模块"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""

    # Claude API 配置
    claude_api_key: str = Field(..., alias="CLAUDE_API_KEY")
    claude_base_url: str = Field(
        default="https://api.anthropic.com", alias="CLAUDE_BASE_URL"
    )
    claude_model: str = Field(
        default="claude-sonnet-4-6", alias="CLAUDE_MODEL"
    )

    # AI Fallback 配置（当主 API 返回内容安全拒绝时自动降级）
    ai_fallback_base_url: str = Field(
        default="", alias="AI_FALLBACK_BASE_URL"
    )
    ai_fallback_api_key: str = Field(
        default="", alias="AI_FALLBACK_API_KEY"
    )
    ai_fallback_model: str = Field(
        default="claude-sonnet-4-6", alias="AI_FALLBACK_MODEL"
    )

    # 企业微信推送配置
    wechat_webhook_url: str = Field(
        default="", alias="WECHAT_WEBHOOK_URL"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
