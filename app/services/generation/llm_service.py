from collections.abc import Generator

from groq import Groq

from app.core.config import settings


class LLMService:

    def __init__(self):
        self.client = Groq(
            api_key=settings.groq_api_key
        )
        self.model = settings.groq_model

    def generate_stream(
        self,
        prompt: str,
    ) -> Generator[str, None, None]:

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            stream=True,
            temperature=0.2,
        )

        for chunk in stream:

            if not chunk.choices:
                continue

            content = chunk.choices[0].delta.content

            if content:
                yield content