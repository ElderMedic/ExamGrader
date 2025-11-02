"""OpenAI compatible client for calling vision language models"""

import os
import base64
import io
import re
from typing import Optional, Dict, Any
from PIL import Image
from openai import OpenAI
from .config import Config


class VLLMClient:
    """Client for calling Vision Language Models via OpenAI compatible API"""
    
    def __init__(self, api_base: Optional[str] = None, 
                 model_name: Optional[str] = None,
                 api_key: Optional[str] = None,
                 config: Optional[Config] = None):
        """Initialize VLLM client
        
        Args:
            api_base: Base URL for OpenAI compatible API (overrides config if provided)
            model_name: Model name (overrides config if provided)
            api_key: API key (overrides config and env if provided)
            config: Config instance (creates default if None)
        """
        self.config = config or Config()
        api_config = self.config.get_api_config()
        
        # Get API key from parameter, config, or environment variable
        self.api_key = api_key or api_config.get("api_key") or os.getenv("DASHSCOPE_API_KEY")
        
        # Get base URL and model name
        self.api_base = (api_base or api_config.get("base_url", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")).rstrip('/')
        self.model_name = model_name or api_config.get("model_name", "qwen3-vl-flash")
        self.timeout = api_config.get("timeout", 60)
        self.max_tokens = api_config.get("max_tokens", 2000)
        self.temperature = api_config.get("temperature", 0.0)
        self.top_p = api_config.get("top_p", 1.0)
        self.seed = api_config.get("seed", None)
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base,
            timeout=self.timeout,
        )
        
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
        else:
            # If no reference answer but template expects it, provide a warning in the section
            reference_answer_section = "\n\n⚠️ 警告：未提供参考答案。请根据一般评分标准进行评分。"
        
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
        messages = self._build_messages(image, reference_answer, question_context)
        
        try:
            # Build parameters dict
            completion_params = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
            }
            
            # Add top_p if specified (OpenAI compatible API)
            top_p = kwargs.get("top_p", self.top_p)
            if top_p is not None:
                completion_params["top_p"] = top_p
            
            # Add seed if specified (for reproducibility)
            seed = kwargs.get("seed", self.seed)
            if seed is not None:
                completion_params["seed"] = seed
            
            completion = self.client.chat.completions.create(**completion_params)
            
            content = completion.choices[0].message.content
            student_answer, score, reasoning = self._parse_response(content)
            
            return {
                "student_answer": student_answer,
                "score": score,
                "reasoning": reasoning,
                "full_response": content,
            }
        except Exception as e:
            return {"error": str(e), "student_answer": None, "score": None, "reasoning": None}
    
    def _parse_response(self, content: str) -> tuple:
        """Parse model response to extract student answer, score and reasoning"""
        parsing_config = self.config.get_parsing_config()
        student_answer_pattern = parsing_config.get("student_answer_pattern", r"(?:识别的学生答案|Recognized Student Answer|学生答案)[：:]\s*(.+?)(?=\n\s*(?:分数|Score)|\n\s*(?:评分理由|Reasoning)|$)")
        score_pattern = parsing_config.get("score_pattern", r"(?:分数|Score):\s*(\d+(?:\.\d+)?)")
        reasoning_pattern = parsing_config.get("reasoning_pattern", r"(?:评分理由|Reasoning):?\s*(.+)")
        score_min = parsing_config.get("score_min", 0)
        score_max = parsing_config.get("score_max", None)  # None means no upper limit
        
        # Extract student answer
        student_answer = None
        student_answer_match = re.search(student_answer_pattern, content, re.IGNORECASE | re.DOTALL)
        if student_answer_match:
            student_answer = student_answer_match.group(1).strip()
        
        # Extract score
        score_match = re.search(score_pattern, content, re.IGNORECASE)
        score = None
        if score_match:
            try:
                score_value = float(score_match.group(1))
                # Apply min constraint
                score = max(score_min, score_value)
                # Apply max constraint only if score_max is specified
                if score_max is not None:
                    score = min(score_max, score)
            except ValueError:
                pass
        
        # Extract reasoning
        reasoning_match = re.search(reasoning_pattern, content, re.IGNORECASE | re.DOTALL)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()
        elif score_match:
            reasoning = content[score_match.end():].strip()
        else:
            reasoning = content.strip()
        
        return student_answer, score, reasoning
