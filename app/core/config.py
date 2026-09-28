from pydantic_settings import BaseSettings, SettingsConfigDict

ollama_url: str = "http://localhost:11434"
ollama_model: str = "qwen2.5-coder:3b"


class Settings(BaseSettings):
    app_name: str = "DocAI"
    app_version: str = "0.1.0"
    environment: str = "development"
    secret_key: str

    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "docai_chunks"

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"

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