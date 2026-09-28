import json
from collections.abc import Generator

import httpx

from app.core.config import settings


class LLMService:
    def __init__(self):
        self.url = f"{settings.ollama_url}/api/generate"
        self.model = settings.ollama_model

    def generate_stream(self, prompt: str) -> Generator[str, None, None]:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
        }

        with httpx.stream(
            "POST",
            self.url,
            json=payload,
            timeout=120.0,
        ) as response:

            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue

                data = json.loads(line)

                chunk = data.get("response", "")

                if chunk:
                    yield chunk

                if data.get("done"):
                    break