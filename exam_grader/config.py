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
                "base_url": "http://localhost:8000/v1",
                "model_name": "deepseek-ocr",
                "timeout": 60,
                "max_tokens": 500,
                "temperature": 0.3,
            },
            "screenshot": {
                "default_interval": 5.0,
                "default_duration": 30.0,
                "save_dir": "./screenshots",
            },
            "prompts": {
                "system_message": """You are an exam paper grading assistant. Your task is to:
1. Analyze the student's answer image
2. Compare it with the reference answer (if provided)
3. Provide a score (0-100)
4. Explain your grading rationale briefly

Format your response as:
Score: [0-100]
Reasoning: [brief explanation]""",
                "user_message_template": """Please grade this student's answer.

{reference_answer_section}

Please provide: 1) Score (0-100), 2) Brief reasoning for your scoring.""",
                "reference_answer_format": """

Reference Answer:
```markdown
{reference_answer}
```""",
                "question_context_format": """

Question Context: {question_context}""",
            },
            "parsing": {
                "score_pattern": "Score:\\s*(\\d+)",
                "reasoning_pattern": "Reasoning:?\\s*(.+)",
                "score_min": 0,
                "score_max": 100,
            },
            "output": {
                "default_dir": "./results",
                "save_screenshots": False,
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
