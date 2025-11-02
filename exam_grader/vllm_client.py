"""VLLM client for calling vision language models"""

import base64
import io
import re
from typing import Optional, Dict, Any
from PIL import Image
import requests
from .config import Config


class VLLMClient:
    """Client for calling Vision Language Models via vLLM API"""
    
    def __init__(self, api_base: Optional[str] = None, 
                 model_name: Optional[str] = None,
                 config: Optional[Config] = None):
        """Initialize VLLM client
        
        Args:
            api_base: Base URL for vLLM API (overrides config if provided)
            model_name: Model name (overrides config if provided)
            config: Config instance (creates default if None)
        """
        self.config = config or Config()
        api_config = self.config.get_api_config()
        
        self.api_base = (api_base or api_config.get("base_url", "http://localhost:8000/v1")).rstrip('/')
        self.model_name = model_name or api_config.get("model_name", "deepseek-ocr")
        self.timeout = api_config.get("timeout", 60)
        self.max_tokens = api_config.get("max_tokens", 500)
        self.temperature = api_config.get("temperature", 0.3)
        
    def _encode_image(self, image: Image.Image) -> str:
        """Encode PIL Image to base64 string"""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    def _build_messages(self, image: Image.Image, 
                       reference_answer: Optional[str] = None,
                       question_context: Optional[str] = None) -> list:
        """Build messages for the vision model"""
        img_base64 = self._encode_image(image)
        prompts = self.config.get_prompts()
        
        # Build system message
        system_message = prompts.get("system_message", "")
        if question_context:
            question_format = prompts.get("question_context_format", "\n\nQuestion Context: {question_context}")
            system_message += question_format.format(question_context=question_context)
        
        # Build user message
        user_template = prompts.get("user_message_template", "Please grade this student's answer.")
        
        reference_answer_section = ""
        if reference_answer:
            ref_format = prompts.get("reference_answer_format", "\n\nReference Answer:\n```markdown\n{reference_answer}\n```")
            reference_answer_section = ref_format.format(reference_answer=reference_answer)
        
        text_content = user_template.format(reference_answer_section=reference_answer_section)
        
        return [
            {"role": "system", "content": system_message},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}},
                    {"type": "text", "text": text_content}
                ]
            }
        ]
    
    def grade_answer(self, image: Image.Image,
                    reference_answer: Optional[str] = None,
                    question_context: Optional[str] = None,
                    **kwargs) -> Dict[str, Any]:
        """Grade a student's answer image"""
        payload = {
            "model": self.model_name,
            "messages": self._build_messages(image, reference_answer, question_context),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                json=payload,
                timeout=kwargs.get("timeout", self.timeout)
            )
            response.raise_for_status()
            
            content = response.json()["choices"][0]["message"]["content"]
            score, reasoning = self._parse_response(content)
            
            return {
                "score": score,
                "reasoning": reasoning,
                "full_response": content,
            }
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "score": None, "reasoning": None}
    
    def _parse_response(self, content: str) -> tuple:
        """Parse model response to extract score and reasoning"""
        parsing_config = self.config.get_parsing_config()
        score_pattern = parsing_config.get("score_pattern", r"Score:\s*(\d+)")
        reasoning_pattern = parsing_config.get("reasoning_pattern", r"Reasoning:?\s*(.+)")
        score_min = parsing_config.get("score_min", 0)
        score_max = parsing_config.get("score_max", 100)
        
        score_match = re.search(score_pattern, content, re.IGNORECASE)
        score = None
        if score_match:
            try:
                score = max(score_min, min(score_max, int(score_match.group(1))))
            except ValueError:
                pass
        
        reasoning_match = re.search(reasoning_pattern, content, re.IGNORECASE | re.DOTALL)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()
        elif score_match:
            reasoning = content[score_match.end():].strip()
        else:
            reasoning = content.strip()
        
        return score, reasoning
