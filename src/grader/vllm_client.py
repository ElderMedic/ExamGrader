"""vLLM client for DeepSeek-OCR based grading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

from PIL import Image
from vllm import LLM, SamplingParams


@dataclass
class GradingRequest:
    image: Image.Image
    question: Optional[str] = None
    reference_answer: Optional[str] = None
    max_score: float = 6.0
    extra_instructions: Optional[str] = None


@dataclass
class GradingResponse:
    raw_output: str
    score: Optional[float]
    reason: Optional[str]


def build_prompt_text(request: GradingRequest) -> str:
    pieces = [
        "?????????????????",
        f"????? {request.max_score} ??",
        "????????????????????????",
        "?????? JSON ???{\"score\": float, \"reason\": string}?",
        "score ??? 0 ??????reason ????????????",
    ]

    if request.question:
        pieces.append("???????\n" + request.question)

    if request.reference_answer:
        pieces.append("?????Markdown????\n" + request.reference_answer)

    if request.extra_instructions:
        pieces.append("?????" + request.extra_instructions)

    return "\n\n".join(pieces)


class VLLMGrader:
    """Wraps ``vllm.LLM`` to evaluate handwritten answers."""

    def __init__(
        self,
        model: str = "deepseek-ai/deepseek-ocr",
        *,
        temperature: float = 0.1,
        max_tokens: int = 512,
        top_p: float = 0.95,
        tensor_parallel_size: int = 1,
        trust_remote_code: bool = True,
        **llm_kwargs,
    ) -> None:
        self.model = model
        self.sampling_params = SamplingParams(
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )
        self.llm = LLM(
            model=model,
            tensor_parallel_size=tensor_parallel_size,
            trust_remote_code=trust_remote_code,
            **llm_kwargs,
        )

    def grade(self, request: GradingRequest) -> GradingResponse:
        image = request.image.convert("RGB")
        prompt = build_prompt_text(request)

        outputs = self.llm.generate(
            [
                {
                    "prompt": prompt,
                    "multi_modal_data": {"image": [image]},
                }
            ],
            self.sampling_params,
        )

        text = outputs[0].outputs[0].text.strip()
        score, reason = self._parse_response(text)
        return GradingResponse(raw_output=text, score=score, reason=reason)

    def _parse_response(self, text: str) -> tuple[Optional[float], Optional[str]]:
        try:
            obj = json.loads(self._extract_json(text))
        except (json.JSONDecodeError, ValueError):
            return None, None

        score = obj.get("score")
        reason = obj.get("reason")
        try:
            if score is not None:
                score = float(score)
        except (TypeError, ValueError):
            score = None
        if reason is not None:
            reason = str(reason)
        return score, reason

    @staticmethod
    def _extract_json(text: str) -> str:
        text = text.strip()
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Missing JSON object in response")
        return text[start : end + 1]

    def close(self) -> None:
        self.llm = None

    def __enter__(self) -> "VLLMGrader":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

