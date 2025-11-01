"""VLLM client for calling vision language models"""

import base64
import io
import re
from typing import Optional, Dict, Any
from PIL import Image
import requests


class VLLMClient:
    """Client for calling Vision Language Models via vLLM API"""
    
    def __init__(self, api_base: str = "http://localhost:8000/v1", 
                 model_name: str = "deepseek-ocr"):
        self.api_base = api_base.rstrip('/')
        self.model_name = model_name
        
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
        
        system_message = """You are an exam paper grading assistant. Your task is to:
1. Analyze the student's answer image
2. Compare it with the reference answer (if provided)
3. Provide a score (0-100)
4. Explain your grading rationale briefly

Format your response as:
Score: [0-100]
Reasoning: [brief explanation]"""
        
        if question_context:
            system_message += f"\n\nQuestion Context: {question_context}"
        
        text_content = "Please grade this student's answer."
        if reference_answer:
            text_content += f"\n\nReference Answer:\n```markdown\n{reference_answer}\n```"
        text_content += "\n\nPlease provide: 1) Score (0-100), 2) Brief reasoning for your scoring."
        
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
            "max_tokens": kwargs.get("max_tokens", 500),
            "temperature": kwargs.get("temperature", 0.3),
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                json=payload,
                timeout=kwargs.get("timeout", 60)
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
        score_match = re.search(r'Score:\s*(\d+)', content, re.IGNORECASE)
        score = None
        if score_match:
            try:
                score = max(0, min(100, int(score_match.group(1))))
            except ValueError:
                pass
        
        reasoning_match = re.search(r'Reasoning:?\s*(.+)', content, re.IGNORECASE | re.DOTALL)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()
        elif score_match:
            reasoning = content[score_match.end():].strip()
        else:
            reasoning = content.strip()
        
        return score, reasoning
