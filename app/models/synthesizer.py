from typing import AsyncGenerator, TypeVar, Generic
import pandas as pd
from config.settings import LLMSettings
from ..models.llm_client import LLMClient


T = TypeVar("T")


class Synthesizer(Generic[T]):
    def __init__(
        self, llm_settings: LLMSettings, system_prompt: str, response_model: type[T]
    ):
        self.llm = LLMClient(llm_settings)
        self.system_prompt = system_prompt
        self.response_model = response_model

    def generate_response(
        self, question: str, context: pd.DataFrame
    ) -> AsyncGenerator[T, None]:
        context_str = self._dataframe_to_json(context)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"# User question:\n{question}"},
            {
                "role": "assistant",
                "content": f"# Retrieved information:\n{context_str}",
            },
        ]
        return self.llm.create_partial(
            response_model=self.response_model,
            messages=messages,
        )

    def _dataframe_to_json(self, context: pd.DataFrame) -> str:
        res = context.to_json(orient="records", indent=2)
        if not isinstance(res, str):
            raise ValueError("Failed to convert DataFrame to JSON string")
        return res
