from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "GeoPrompt RL Backend"
    app_env: str = "dev"
    app_debug: bool = True

    database_url: str = (
        "mysql+pymysql://root:root@127.0.0.1:3306/geoprompt?charset=utf8mb4"
    )

    encryption_key: str = Field(
        default="",
        description="Fernet key for encrypting custom model API keys in the database. "
                    "Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'",
    )

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    default_model_id: int | None = Field(default=None)
    default_judge_model_id: int | None = Field(default=None)

    experiment_concurrency: int = Field(default=8, ge=1, le=32)
    llm_call_timeout: int = Field(default=60, ge=10, le=300)


@lru_cache
def get_settings() -> Settings:
    return Settings()
