"""Command line interface for the exam grading helper."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from .screenshot import CaptureRegion, ScreenshotConfig, ScreenshotTaker
from .vllm_client import GradingRequest, VLLMGrader


app = typer.Typer(help="Automated exam grading helper using vLLM")


def _load_text(path: Optional[Path]) -> Optional[str]:
    if not path:
        return None
    return path.read_text(encoding="utf-8")


def _build_region(x: int, y: int, width: Optional[int], height: Optional[int]) -> CaptureRegion:
    region = CaptureRegion(left=x, top=y, width=width, height=height)
    return region


def _build_request(
    image,
    *,
    question: Optional[str],
    reference: Optional[str],
    max_score: float,
    instructions: Optional[str],
) -> GradingRequest:
    return GradingRequest(
        image=image,
        question=question,
        reference_answer=reference,
        max_score=max_score,
        extra_instructions=instructions,
    )


def _run_once(
    grader: VLLMGrader,
    taker: ScreenshotTaker,
    *,
    question: Optional[str],
    reference: Optional[str],
    max_score: float,
    instructions: Optional[str],
) -> None:
    image = taker.capture_once()
    request = _build_request(
        image,
        question=question,
        reference=reference,
        max_score=max_score,
        instructions=instructions,
    )
    response = grader.grade(request)
    typer.echo(f"????: {response.raw_output}")
    if response.score is not None:
        typer.echo(f"????: {response.score}")
    if response.reason:
        typer.echo(f"????: {response.reason}")


@app.command()
def once(
    model: str = typer.Option("deepseek-ai/deepseek-ocr", help="vLLM ???????"),
    x: int = typer.Option(0, help="???????"),
    y: int = typer.Option(0, help="???????"),
    width: Optional[int] = typer.Option(None, help="??????"),
    height: Optional[int] = typer.Option(None, help="??????"),
    interval: float = typer.Option(10.0, help="?????? loop ??????"),
    output_dir: Optional[Path] = typer.Option(None, help="???????"),
    question_text: Optional[str] = typer.Option(None, help="????"),
    question_file: Optional[Path] = typer.Option(None, help="??????"),
    reference_text: Optional[str] = typer.Option(None, help="???? Markdown ??"),
    reference_file: Optional[Path] = typer.Option(None, help="???? Markdown ??"),
    max_score: float = typer.Option(6.0, help="????"),
    extra_instructions: Optional[str] = typer.Option(None, help="?????"),
) -> None:
    """????????????"""

    reference = reference_text or _load_text(reference_file)
    question = question_text or _load_text(question_file)

    config = ScreenshotConfig(
        region=_build_region(x, y, width, height),
        interval_seconds=interval,
        output_dir=output_dir,
    )

    with ScreenshotTaker(config) as taker:
        grader = VLLMGrader(model=model)
        _run_once(
            grader,
            taker,
            question=question,
            reference=reference,
            max_score=max_score,
            instructions=extra_instructions,
        )


@app.command()
def loop(
    model: str = typer.Option("deepseek-ai/deepseek-ocr", help="vLLM ???????"),
    interval: float = typer.Option(10.0, help="?????????"),
    x: int = typer.Option(0, help="???????"),
    y: int = typer.Option(0, help="???????"),
    width: Optional[int] = typer.Option(None, help="??????"),
    height: Optional[int] = typer.Option(None, help="??????"),
    output_dir: Optional[Path] = typer.Option(None, help="???????"),
    question_text: Optional[str] = typer.Option(None, help="????"),
    question_file: Optional[Path] = typer.Option(None, help="??????"),
    reference_text: Optional[str] = typer.Option(None, help="???? Markdown ??"),
    reference_file: Optional[Path] = typer.Option(None, help="???? Markdown ??"),
    max_score: float = typer.Option(6.0, help="????"),
    extra_instructions: Optional[str] = typer.Option(None, help="?????"),
    limit: Optional[int] = typer.Option(None, help="???????????"),
) -> None:
    """?????????????????"""

    reference = reference_text or _load_text(reference_file)
    question = question_text or _load_text(question_file)

    config = ScreenshotConfig(
        region=_build_region(x, y, width, height),
        interval_seconds=interval,
        output_dir=output_dir,
    )

    with ScreenshotTaker(config) as taker:
        grader = VLLMGrader(model=model)

        def _callback(image):
            request = _build_request(
                image,
                question=question,
                reference=reference,
                max_score=max_score,
                instructions=extra_instructions,
            )
            response = grader.grade(request)
            typer.echo("=" * 40)
            typer.echo(f"????: {response.raw_output}")
            if response.score is not None:
                typer.echo(f"????: {response.score}")
            if response.reason:
                typer.echo(f"????: {response.reason}")

        try:
            taker.capture_with_callback(_callback, limit=limit)
        except KeyboardInterrupt:
            typer.echo("????????")


if __name__ == "__main__":
    app()
