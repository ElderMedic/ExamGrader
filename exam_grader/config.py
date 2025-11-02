"""Configuration management for ExamGrader"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """Configuration manager for ExamGrader"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration
        
        Args:
            config_path: Path to config file. If None, uses default config.yaml in project root
        """
        if config_path is None:
            # Try to find config.yaml in project root
            current_dir = Path(__file__).parent.parent
            config_path = current_dir / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Failed to load config from {self.config_path}: {e}")
                return self._default_config()
        else:
            print(f"Config file not found at {self.config_path}, using defaults")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            "api": {
                "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
                "model_name": "qwen3-vl-flash",
                "api_key": None,  # Will use DASHSCOPE_API_KEY environment variable if not set
                "timeout": 60,
                "max_tokens": 2000,
                "temperature": 0.0,  # 0.0 for deterministic grading
                "top_p": 1.0,
                "seed": None,
            },
            "screenshot": {
                "default_interval": 5.0,
                "default_duration": 30.0,
                "save_dir": "./screenshots",
                "default_monitor": None,  # None means first monitor (index 1)
                "default_region": None,  # None means full screen
            },
            "prompts": {
                "system_message": """你是一个试卷评分助手。你的任务是：
1. 分析学生的答案图片，理解学生手写字迹的内容
2. 仔细阅读参考答案中的评分标准和要求
3. 根据参考答案中的评分标准给出相应的分数
4. 简要说明你的评分理由，不用分析为什么正确，只说明为什么扣分

⚠️ 重要提示 - 必须严格遵守：
- **必须严格按照参考答案中的"评分标准"部分进行评分**
- **仔细阅读参考答案中的"评分细则"，逐项对照学生答案**
- **严格按照参考答案中的"扣分规则"执行**
- **分数范围完全由参考答案中的"满分"确定，不要假设是百分制**
- **如果参考答案中有具体的给分/扣分说明，必须严格按照执行**

请按以下格式回复：
识别的学生答案: [从图片中识别出的学生答案内容]
分数: [实际分数]
评分理由: [简要说明]""",
                "user_message_template": """请对这名学生的答案进行评分。

════════════════════════════════════════════════════════════
📋 以下是参考答案和评分标准（这是评分的唯一依据）：
════════════════════════════════════════════════════════════

{reference_answer_section}

════════════════════════════════════════════════════════════

📝 评分步骤：
1. 先识别并输出学生的答案内容
2. 逐项对照参考答案中的"评分标准"部分
3. 严格按照"评分细则"中的每一条规则给分
4. 严格遵循"扣分规则"
5. 根据对照结果给出最终分数
6. 说明扣分原因（只说明为什么扣分，不用说明为什么正确）""",
                "reference_answer_format": """

⚠️ 参考答案和评分标准（这是评分的唯一依据，必须严格遵守）：
```markdown
{reference_answer}
```

请特别注意：
- 严格按照上述参考答案中的"评分标准"和"评分细则"进行评分
- 严格遵守"扣分规则"
- 不要自行添加评分规则""",
                "question_context_format": """

题目上下文：{question_context}""",
            },
            "parsing": {
                "student_answer_pattern": "(?:识别的学生答案|Recognized Student Answer|学生答案)[：:]\\s*(.+?)(?=\\n\\s*(?:分数|Score)|\\n\\s*(?:评分理由|Reasoning)|$)",
                "score_pattern": "(?:分数|Score):\\s*(\\d+(?:\\.\\d+)?)",
                "reasoning_pattern": "(?:评分理由|Reasoning):?\\s*(.+)",
                "score_min": 0,
                "score_max": None,  # None means no upper limit, will use reference answer if specified
            },
            "output": {
                "default_dir": "./results",
                "save_screenshots": False,
                "auto_save_records": True,  # Automatically save grading records in periodic mode
                "records_dir": "./results",
            },
            "reference_answer": {
                "default_file": "examples/reference_answer.md",  # Default reference answer file path
            },
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key path
        
        Args:
            key_path: Dot-separated path (e.g., 'api.base_url')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key_path.split('.')
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration"""
        return self._config.get("api", {})
    
    def get_prompts(self) -> Dict[str, str]:
        """Get prompt templates"""
        return self._config.get("prompts", {})
    
    def get_parsing_config(self) -> Dict[str, Any]:
        """Get parsing configuration"""
        return self._config.get("parsing", {})
    
    def get_screenshot_config(self) -> Dict[str, Any]:
        """Get screenshot configuration"""
        return self._config.get("screenshot", {})
    
    def reload(self):
        """Reload configuration from file"""
        self._config = self._load_config()
    
    def save(self, output_path: Optional[str] = None):
        """Save current configuration to file"""
        if output_path is None:
            output_path = self.config_path
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
