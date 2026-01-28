"""配置管理模块"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""

    # Claude API 配置
    claude_api_key: str = Field(..., alias="CLAUDE_API_KEY")
    claude_base_url: str = Field(
        default="https://code.newcli.com/claude/aws", alias="CLAUDE_BASE_URL"
    )
    claude_model: str = Field(
        default="claude-opus-4-5", alias="CLAUDE_MODEL"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
