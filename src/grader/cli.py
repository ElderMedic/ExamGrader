"""Command line interface for the exam grading helper."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from .screenshot import CaptureRegion, ScreenshotConfig, ScreenshotTaker
from .vllm_client import GradingRequest, GradingResponse, VLLMGrader


app = typer.Typer(help="Automated exam grading helper using vLLM")


def _load_text(path: Optional[Path]) -> Optional[str]:
    if not path:
        return None
    return path.read_text(encoding="utf-8")


def _resolve_text(text_opt: Optional[str], file_opt: Optional[Path]) -> Optional[str]:
    return text_opt if text_opt is not None else _load_text(file_opt)


def _build_region(x: int, y: int, width: Optional[int], height: Optional[int]) -> CaptureRegion:
    return CaptureRegion(left=x, top=y, width=width, height=height)


def _make_request(
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


def _print_response(response: GradingResponse, *, separator: bool = False) -> None:
    if separator:
        typer.echo("=" * 40)
    typer.echo(f"Model raw output: {response.raw_output}")
    if response.score is not None:
        typer.echo(f"Parsed score: {response.score}")
    if response.reason:
        typer.echo(f"Rationale: {response.reason}")


def _prepare_config(
    *,
    x: int,
    y: int,
    width: Optional[int],
    height: Optional[int],
    interval: float,
    output_dir: Optional[Path],
) -> ScreenshotConfig:
    return ScreenshotConfig(
        region=_build_region(x, y, width, height),
        interval_seconds=interval,
        output_dir=output_dir,
    )


def _prepare_context(
    *,
    question_text: Optional[str],
    question_file: Optional[Path],
    reference_text: Optional[str],
    reference_file: Optional[Path],
) -> tuple[Optional[str], Optional[str]]:
    question = _resolve_text(question_text, question_file)
    reference = _resolve_text(reference_text, reference_file)
    return question, reference


def _evaluate_image(
    grader: VLLMGrader,
    image,
    *,
    question: Optional[str],
    reference: Optional[str],
    max_score: float,
    instructions: Optional[str],
    separator: bool = False,
) -> None:
    request = _make_request(
        image,
        question=question,
        reference=reference,
        max_score=max_score,
        instructions=instructions,
    )
    response = grader.grade(request)
    _print_response(response, separator=separator)


@app.command()
def once(
    model: str = typer.Option("deepseek-ai/deepseek-ocr", help="Path of the vLLM model"),
    x: int = typer.Option(0, help="Screenshot region left offset"),
    y: int = typer.Option(0, help="Screenshot region top offset"),
    width: Optional[int] = typer.Option(None, help="Screenshot region width"),
    height: Optional[int] = typer.Option(None, help="Screenshot region height"),
    output_dir: Optional[Path] = typer.Option(None, help="Directory to persist captures"),
    question_text: Optional[str] = typer.Option(None, help="Question text"),
    question_file: Optional[Path] = typer.Option(None, help="Path to question markdown"),
    reference_text: Optional[str] = typer.Option(None, help="Reference answer text"),
    reference_file: Optional[Path] = typer.Option(None, help="Path to reference markdown"),
    max_score: float = typer.Option(6.0, help="Maximum score"),
    extra_instructions: Optional[str] = typer.Option(None, help="Additional instructions for the model"),
) -> None:
    """Capture once and grade the answer."""

    question, reference = _prepare_context(
        question_text=question_text,
        question_file=question_file,
        reference_text=reference_text,
        reference_file=reference_file,
    )

    config = _prepare_config(
        x=x,
        y=y,
        width=width,
        height=height,
        interval=1.0,
        output_dir=output_dir,
    )

    with ScreenshotTaker(config) as taker, VLLMGrader(model=model) as grader:
        image = taker.capture_once()
        _evaluate_image(
            grader,
            image,
            question=question,
            reference=reference,
            max_score=max_score,
            instructions=extra_instructions,
        )


@app.command()
def loop(
    model: str = typer.Option("deepseek-ai/deepseek-ocr", help="Path of the vLLM model"),
    interval: float = typer.Option(10.0, help="Screenshot interval in seconds"),
    x: int = typer.Option(0, help="Screenshot region left offset"),
    y: int = typer.Option(0, help="Screenshot region top offset"),
    width: Optional[int] = typer.Option(None, help="Screenshot region width"),
    height: Optional[int] = typer.Option(None, help="Screenshot region height"),
    output_dir: Optional[Path] = typer.Option(None, help="Directory to persist captures"),
    question_text: Optional[str] = typer.Option(None, help="Question text"),
    question_file: Optional[Path] = typer.Option(None, help="Path to question markdown"),
    reference_text: Optional[str] = typer.Option(None, help="Reference answer text"),
    reference_file: Optional[Path] = typer.Option(None, help="Path to reference markdown"),
    max_score: float = typer.Option(6.0, help="Maximum score"),
    extra_instructions: Optional[str] = typer.Option(None, help="Additional instructions for the model"),
    limit: Optional[int] = typer.Option(None, help="Optional iteration limit for debugging"),
) -> None:
    """Capture repeatedly and grade answers at intervals."""

    question, reference = _prepare_context(
        question_text=question_text,
        question_file=question_file,
        reference_text=reference_text,
        reference_file=reference_file,
    )

    config = _prepare_config(
        x=x,
        y=y,
        width=width,
        height=height,
        interval=interval,
        output_dir=output_dir,
    )

    with ScreenshotTaker(config) as taker, VLLMGrader(model=model) as grader:
        try:
            taker.capture_with_callback(
                lambda image: _evaluate_image(
                    grader,
                    image,
                    question=question,
                    reference=reference,
                    max_score=max_score,
                    instructions=extra_instructions,
                    separator=True,
                ),
                limit=limit,
            )
        except KeyboardInterrupt:
            typer.echo("Loop interrupted by user.")


if __name__ == "__main__":
    app()
