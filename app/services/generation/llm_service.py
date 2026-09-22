import httpx

from app.core.config import settings


class LLMService:

    def __init__(self):
        self.url = f"{settings.ollama_url}/api/generate"
        self.model = settings.ollama_model

    def generate(
        self,
        prompt: str,
    ) -> str:

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        response = httpx.post(
            self.url,
            json=payload,
            timeout=120.0,
        )

        response.raise_for_status()

        data = response.json()

        return data["response"].strip()