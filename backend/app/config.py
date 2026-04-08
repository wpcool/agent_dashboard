from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://asktable:asktable@localhost:5432/asktable"
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI Provider: anthropic, qwen, openai
    AI_PROVIDER: str = "qwen"
    ANTHROPIC_API_KEY: str = ""
    QWEN_API_KEY: str = ""
    QWEN_MODEL: str = "qwen-max"
    OPENAI_API_KEY: str = ""

    # AI 配置
    AI_MODEL: str = "qwen-max"
    AI_MAX_TOKENS: int = 4000
    AI_TEMPERATURE: float = 0.1
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # 查询配置
    QUERY_TIMEOUT: int = 30
    QUERY_MAX_ROWS: int = 1000

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
