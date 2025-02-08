from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, Field
from functools import lru_cache


class LLMSettings(BaseModel):
    temperature: float = Field(0.7, ge=0.0, le=1.5)
    max_tokens: int = Field(4000, ge=1, le=4096)
    max_retries: int = Field(3, ge=1, le=10)
    default_model: str
    name: str


class OpenAISettings(LLMSettings):
    api_key: str
    default_model: str = Field("gpt-4o")
    embedding_model: str = Field("text-embedding-3-small")
    name: str = Field("openai")


class PostgresSettings(BaseModel):
    url: str
    name: str = Field("postgres")
    password: str = Field("postgres")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")
    postgres: PostgresSettings
    openai: OpenAISettings


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore
