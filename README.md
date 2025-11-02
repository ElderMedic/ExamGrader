# ExamGrader

Automated exam paper grading tool using Vision Language Models via OpenAI compatible API.

## Features

- Cross-platform screenshot capture (Mac/Windows/Linux)
- Adjustable screenshot region and periodic capture
- OpenAI compatible API integration (supports Alibaba Cloud DashScope, etc.)
- Support for reference answers (Markdown format)
- **Flexible configuration system** - customize prompts and parameters via YAML config
- Default model: qwen3-vl-flash

## Quick Start

### Local Installation (Recommended)

#### Using mamba (Recommended)

```bash
# Activate mamba environment
mamba activate test  # or create new: mamba create -n exam-grader python=3.11

# Install dependencies
pip install -r requirements.txt

# Set API key (required)
export DASHSCOPE_API_KEY="sk-xxx"  # Get from https://www.alibabacloud.com/help/zh/model-studio/get-api-key

# Run single capture
python main.py --mode single
```

#### Using uv

```bash
# Install with uv
uv pip install -r requirements.txt

# Set API key
export DASHSCOPE_API_KEY="sk-xxx"

# Run
python main.py --mode single
```

#### Using pip

```bash
pip install -r requirements.txt
export DASHSCOPE_API_KEY="sk-xxx"
python main.py --mode single
```

## Configuration

### API Key Setup

The API key can be set in three ways (priority order):
1. Command line argument: `--api-key sk-xxx`
2. Configuration file: `config.yaml` -> `api.api_key`
3. Environment variable: `DASHSCOPE_API_KEY`

```bash
# Recommended: Use environment variable
export DASHSCOPE_API_KEY="sk-xxx"
```

For Alibaba Cloud DashScope:
- Singapore region: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` (default)
- Beijing region: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- Get API Key: https://www.alibabacloud.com/help/zh/model-studio/get-api-key

### API Parameters for Deterministic Grading

For **factual accuracy and reproducibility** in grading, configure these parameters in `config.yaml`:

```yaml
api:
  temperature: 0.0    # Critical: Set to 0.0 for deterministic, reproducible outputs
  max_tokens: 2000   # Set large enough to ensure complete responses
  top_p: 1.0         # Usually set to 1.0 with temperature=0.0
  seed: 12345        # Optional: Set a fixed number for reproducibility (or null for random)
```

**Parameter Recommendations:**

| Parameter | Recommended Value | Explanation |
|-----------|------------------|-------------|
| `temperature` | **0.0** | Zero temperature = deterministic output. Same input always produces same output. Critical for fair grading. |
| `max_tokens` | **2000-4000** | Large enough to capture full student answer recognition, scoring, and reasoning. Adjust based on question complexity. |
| `top_p` | **1.0** | With temperature=0.0, this parameter has minimal effect, but 1.0 ensures all tokens are considered. |
| `seed` | **Fixed number** (e.g., 12345) | Optional but recommended: Fixed seed ensures reproducibility across runs. Set to `null` if you don't need it. |

**Why These Settings Matter:**

- **temperature = 0.0**: Eliminates randomness. Essential for fair, consistent grading where the same answer should always get the same score.
- **max_tokens**: Too small = responses may be truncated. Too large = unnecessary API costs. 2000-4000 is usually sufficient.
- **seed**: When combined with temperature=0.0, ensures complete reproducibility even across different API calls.

**Example Configuration:**
```yaml
api:
  temperature: 0.0     # Zero randomness for consistent grading
  max_tokens: 2000     # Sufficient for complete responses
  top_p: 1.0           # Standard with temperature=0.0
  seed: 42             # Fixed seed for reproducibility
```

### Configuration File

The project uses `config.yaml` for all customizable settings. You can:

1. **Customize Prompts**: Edit `prompts` section to change how the model grades answers
2. **Adjust API Settings**: Modify `api` section for different models or endpoints
3. **Configure Screenshot Behavior**: 
   - `default_monitor`: Set default monitor index (1 for first, 2 for second, 0 for all combined)
   - `default_region`: Set default capture region `[left, top, width, height]` (null for full screen)
   - `default_interval` and `default_duration`: For periodic capture
4. **Change Parsing Rules**: Adjust `parsing` section if model responses change format

### Screenshot Configuration

#### Fixed Region Capture

To capture a specific fixed area instead of full screen:

**Method 1: Command line**
```bash
# Capture 800x600 area starting at position (100, 100)
python main.py --mode single --region "100,100,800,600"
```

**Method 2: Config file**
Edit `config.yaml`:
```yaml
screenshot:
  default_region: [100, 100, 800, 600]  # [left, top, width, height]
```

#### Multi-Monitor Support

**List available monitors:**
```bash
python main.py --list-monitors
```

**Select specific monitor:**
```bash
# First monitor (default)
python main.py --mode single

# Second monitor
python main.py --mode single --monitor 2

# All monitors combined (spans all displays)
python main.py --mode single --monitor 0
```

**Set default monitor in config.yaml:**
```yaml
screenshot:
  default_monitor: 2  # Use second monitor by default
```

**Note:** Monitor indices:
- `0`: All monitors combined (full desktop spanning)
- `1`: First physical monitor (default)
- `2`: Second physical monitor
- `3+`: Additional monitors

### Example: Customizing Prompts

Edit `config.yaml`:

```yaml
prompts:
  system_message: |
    你是一个试卷评分助手。根据参考答案中的评分标准进行评分。
```

### Reference Answer File Format

参考答案文件应包含以下部分来指定分数要求：

```markdown
# Reference Answer for Question [X]

## 题目信息
- **题号**: 第X题
- **满分**: [分数]分  # 例如：6分、10分、25分等
- **题型**: [题型名称]

## 标准答案
[标准答案内容]

## 评分标准 (Scoring Criteria)

**满分**: [分数]分

**评分细则**:
- **第(1)问**: [分数]分 - [评分要求]
- **第(2)问**: [分数]分 - [评分要求]
- ...

**扣分规则**:
- [具体扣分规则]
- 最低0分

## 评分要点
[需要关注的关键点]
```

**重要提示**:
- 务必在参考答案文件中明确指定**满分**和**评分细则**
- 系统会根据参考答案中的评分标准进行评分，而不是固定的百分制
- 分数可以是整数或小数（如 3.5 分）
- 查看 `examples/reference_answer.md` 获取完整示例

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

# Custom region (fixed area capture)
python main.py --mode single --region "100,100,800,600"

# Capture from specific monitor (first monitor = 1, second = 2, etc.)
python main.py --mode single --monitor 2

# List available monitors
python main.py --list-monitors

# Combine region and monitor selection
python main.py --mode single --monitor 1 --region "100,100,800,600"

# Override config settings
python main.py --mode single \
  --api-base https://dashscope.aliyuncs.com/compatible-mode/v1 \
  --model qwen-vl-plus \
  --api-key sk-xxx

# Save results
python main.py --mode periodic \
  --save-screenshots --output results.json
```

## Requirements

- Python 3.11+
- OpenAI compatible API endpoint (default: Alibaba Cloud DashScope)
- Vision model (default: qwen3-vl-flash)
- API key for the service

## Project Structure

```
exam_grader/
??? screenshot.py      # Screenshot capture
??? vllm_client.py    # OpenAI compatible API client
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
