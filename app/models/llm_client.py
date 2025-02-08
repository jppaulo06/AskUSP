from typing import Any, Type, TypeVar
import instructor
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from instructor import Instructor
from config.settings import LLMSettings


T = TypeVar("T", bound=Any)


class LLMClient:
    def __init__(self, LLMSettings: LLMSettings):
        self.provider_settings = LLMSettings
        self.client = self._initialize_client()

    async def create_completion(
        self, response_model: Type[T], messages: list[dict[str, str]], **kwargs
    ) -> T:
        return await self.client.chat.completions.create(
            model=kwargs.get("model", self.provider_settings.default_model),
            temperature=kwargs.get("temperature", self.provider_settings.temperature),
            max_retries=kwargs.get("max_retries", self.provider_settings.max_retries),
            max_tokens=kwargs.get("max_tokens", self.provider_settings.max_tokens),
            response_model=response_model,
            messages=messages,
        )

    def _initialize_client(self) -> Instructor:
        client_initializers = {
            "openai": lambda s: instructor.from_openai(AsyncOpenAI(api_key=s.api_key)),
            "anthropic": lambda s: instructor.from_anthropic(
                AsyncAnthropic(api_key=s.api_key)
            ),
            "llama": lambda s: instructor.from_openai(
                AsyncOpenAI(base_url=s.base_url, api_key=s.api_key),
                mode=instructor.Mode.JSON,
            ),
        }
        initializer = client_initializers.get(self.provider_settings.name)
        if not initializer:
            raise ValueError(f"Unsupported LLM provider: {self.provider_settings.name}")
        return initializer(self.provider_settings)
