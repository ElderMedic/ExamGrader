# ExamGrader

Automated exam paper grading tool using Vision Language Models (VLLM).

## Features

- ? Cross-platform screenshot capture (Mac and Windows)
- ? Adjustable screenshot region and size
- ? Periodic screenshot capture with configurable intervals
- ? Integration with vLLM for vision language model inference
- ? Support for reference answers (Markdown format)
- ? Automatic scoring and reasoning extraction

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure vLLM server is running with a vision language model (e.g., deepseek-ocr):
```bash
# Example: Start vLLM server
python -m vllm.entrypoints.openai.api_server \
    --model deepseek-ai/deepseek-ocr \
    --host 0.0.0.0 \
    --port 8000
```

## Usage

### Basic Usage

Single capture and grade:
```bash
python main.py --mode single
```

Periodic capture and grade:
```bash
python main.py --mode periodic --interval 5 --duration 30
```

### With Reference Answer

```bash
python main.py --mode single \
    --reference-answer examples/reference_answer.md \
    --question-context "Question 1: Explain the concept..."
```

### Custom Screenshot Region

```bash
python main.py --mode single \
    --region "100,100,800,600"
```

### Save Results

```bash
python main.py --mode periodic \
    --interval 5 --duration 30 \
    --save-screenshots \
    --output results.json
```

## Testing

Run basic tests (no vLLM server required):
```bash
python tests/test_exam_grader.py --basic
```

Run full test suite:
```bash
python -m pytest tests/
```

## Project Structure

```
exam_grader/
??? __init__.py
??? screenshot.py      # Screenshot capture functionality
??? vllm_client.py     # VLLM API client
??? grader.py          # Main grading logic

tests/
??? test_exam_grader.py

main.py                # Command-line interface
requirements.txt       # Dependencies
```

## API Reference

### ScreenshotCapture

- `capture_full_screen()` - Capture entire screen
- `capture_region(left, top, width, height)` - Capture specific region
- `capture_periodically(interval, duration, region, callback)` - Periodic capture

### VLLMClient

- `grade_answer(image, reference_answer, question_context)` - Grade an answer image

### ExamGrader

- `grade_single_answer(image, reference_answer, question_context)` - Grade single image
- `capture_and_grade(region, reference_answer, question_context)` - Capture and grade
- `periodic_grading(...)` - Periodic capture and grading

## Notes

- Screenshot region coordinates are in pixels (left, top, width, height)
- Reference answers should be in Markdown format
- The model response should include "Score: [0-100]" and "Reasoning: ..." for proper parsing
- Ensure vLLM server is running before using grading functionality
