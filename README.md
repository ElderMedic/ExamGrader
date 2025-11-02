# ExamGrader

Automated exam paper grading tool using Vision Language Models (VLLM).

## Features

- Cross-platform screenshot capture (Mac/Windows/Linux)
- Adjustable screenshot region and periodic capture
- vLLM integration for vision model inference
- Support for reference answers (Markdown format)
- **Flexible configuration system** - customize prompts and parameters via YAML config
- Docker deployment support

## Quick Start

### Docker Deployment (Recommended)

```bash
# Build and deploy
./docker-deploy.sh

# Run single capture
docker run --rm -v $(pwd)/screenshots:/app/screenshots \
  -v $(pwd)/config.yaml:/app/config.yaml \
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

## Configuration

The project uses `config.yaml` for all customizable settings. You can:

1. **Customize Prompts**: Edit `prompts` section to change how the model grades answers
2. **Adjust API Settings**: Modify `api` section for different models or endpoints
3. **Configure Screenshot Behavior**: Update `screenshot` section for capture settings
4. **Change Parsing Rules**: Adjust `parsing` section if model responses change format

### Example: Customizing Prompts

Edit `config.yaml`:

```yaml
prompts:
  system_message: |
    You are a strict exam grader. Grade answers harshly.
    Score range: 0-100 where 100 is perfect.
    
    Format: Score: [0-100]
    Reasoning: [explanation]
```

### Using Custom Config File

```bash
python main.py --config my_config.yaml --mode single
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

# Override config settings
python main.py --mode single \
  --api-base http://other-server:8000/v1 \
  --model other-model

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
??? grader.py          # Main grading logic
??? config.py          # Configuration management

config.yaml            # Configuration file (customizable)
main.py                # Command-line interface
requirements.txt       # Dependencies
```

## Configuration Reference

See `config.yaml` for all available options. Key sections:

- `api`: API endpoint, model name, timeout, temperature
- `prompts`: System/user messages, templates
- `screenshot`: Default intervals, save directories
- `parsing`: Response parsing patterns and limits
- `output`: Default output settings
