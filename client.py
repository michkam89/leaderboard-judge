from __future__ import annotations
from typing import Any, Type

import instructor
from openai import OpenAI
from pydantic import BaseModel


class JudgeClient:
    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._client = instructor.patch(
            OpenAI(api_key=api_key, base_url=base_url),
            mode=instructor.Mode.MD_JSON,
        )
        self._model = model

    def judge(
        self,
        messages: list[dict],
        response_model: Type[BaseModel],
        temperature: float = 0.0,
    ) -> Any:
        return self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            response_model=response_model,
            temperature=temperature,
        )
