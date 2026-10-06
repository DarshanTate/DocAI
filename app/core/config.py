from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DocAI"
    app_version: str = "0.1.0"
    environment: str = "development"

    secret_key: str

    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "docai_chunks"


    groq_api_key: str
    groq_model: str = "openai/gpt-oss-20b"

    storage_backend: str = "local"

    s3_bucket: str = ""
    s3_region: str = "auto"
    s3_endpoint_url: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:3b"

    max_file_size_mb: int = 50

    allowed_extensions: str = (
        "pdf,docx,xlsx,csv,pptx,txt"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_extension_set(self) -> set[str]:
        return {
            extension.strip().lower()
            for extension in self.allowed_extensions.split(",")
        }


settings = Settings()