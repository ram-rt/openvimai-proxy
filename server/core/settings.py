from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import HttpUrl, Field

class Settings(BaseSettings):
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_base: HttpUrl = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    cache_db: str = "cache.duckdb"
    telemetry_db: str = "telemetry.duckdb"
    cache_ttl_minutes: int = 60
    ctx_tokens: int = 8192
    cutoff_ratio: float = 0.92
    jwt_secret: str = Field(default="CHANGE_ME", alias="JWT_SECRET_KEY")
    jwt_algo: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
