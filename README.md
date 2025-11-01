# ExamGrader

Automated exam paper grading tool using Vision Language Models (VLLM).

## Features

- Cross-platform screenshot capture (Mac/Windows/Linux)
- Adjustable screenshot region and periodic capture
- vLLM integration for vision model inference
- Support for reference answers (Markdown format)
- Docker deployment support

## Quick Start

### Docker Deployment (Recommended)

```bash
# Build and deploy
./docker-deploy.sh

# Run single capture
docker run --rm -v $(pwd)/screenshots:/app/screenshots \
  -e VLLM_API_BASE=http://host.docker.internal:8000/v1 \
  exam-grader:latest python main.py --mode single

# Using docker-compose
docker-compose run --rm exam-grader python main.py --mode single
```

### Local Installation

```bash
pip install -r requirements.txt
python main.py --mode single
```

## Usage

```bash
# Single capture
python main.py --mode single

# Periodic capture (every 5s for 30s)
python main.py --mode periodic --interval 5 --duration 30

# With reference answer
python main.py --mode single \
  --reference-answer examples/reference_answer.md

# Custom region
python main.py --mode single --region "100,100,800,600"

# Save results
python main.py --mode periodic \
  --save-screenshots --output results.json
```

## Requirements

- Python 3.11+
- vLLM server running (default: http://localhost:8000/v1)
- Vision model (e.g., deepseek-ocr)

## Project Structure

```
exam_grader/
??? screenshot.py      # Screenshot capture
??? vllm_client.py    # VLLM API client
??? grader.py         # Main grading logic
```
