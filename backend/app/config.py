from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Seft-Agent API"
    app_env: str = "dev"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/seft_agent"
    llm_api_key: str = ""
    embedding_model: str = "bge-m3"


settings = Settings()
