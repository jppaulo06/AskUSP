from typing import List
import pandas as pd
from pydantic import BaseModel, Field
from config.settings import LLMSettings
from ..models.llm_client import LLMClient


class SynthesizedResponse(BaseModel):
    thought_process: List[str] = Field(
        description="List of thoughts that the AI assistant had while synthesizing the answer"
    )
    answer: str = Field(description="The synthesized answer to the user's question")
    enough_context: bool = Field(
        description="Whether the assistant has enough context to answer the question"
    )


class Synthesizer:
    def __init__(self, llm_settings: LLMSettings, system_prompt: str):
        self.llm = LLMClient(llm_settings)
        self.system_prompt = system_prompt

    async def generate_response(
        self, question: str, context: pd.DataFrame
    ) -> SynthesizedResponse:
        context_str = self._dataframe_to_json(context)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"# User question:\n{question}"},
            {
                "role": "assistant",
                "content": f"# Retrieved information:\n{context_str}",
            },
        ]
        return await self.llm.create_completion(
            response_model=SynthesizedResponse,
            messages=messages,
        )

    def _dataframe_to_json(self, context: pd.DataFrame) -> str:
        res = context.to_json(orient="records", indent=2)
        if not isinstance(res, str):
            raise ValueError("Failed to convert DataFrame to JSON string")
        return res
