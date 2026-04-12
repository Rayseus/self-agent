from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Self-Agent API"
    app_env: str = "dev"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/self_agent"

    @property
    def sqlalchemy_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url

    gemini_api_key: str = ""
    embedding_model: str = "models/gemini-embedding-001"
    llm_model: str = "models/gemini-2.5-flash"
    embedding_dim: int = 3072
    proxy_url: str = ""
    cors_origins: str = "*"


settings = Settings()
