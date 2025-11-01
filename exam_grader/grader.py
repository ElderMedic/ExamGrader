"""Main grading logic"""

import os
from typing import Optional, List, Dict, Any
from PIL import Image
from .screenshot import ScreenshotCapture
from .vllm_client import VLLMClient


class ExamGrader:
    """Main exam grading class"""
    
    def __init__(self, vllm_api_base: str = "http://localhost:8000/v1",
                 model_name: str = "deepseek-ocr"):
        self.screenshot_capture = ScreenshotCapture()
        self.vllm_client = VLLMClient(vllm_api_base, model_name)
    
    def grade_single_answer(self, image: Image.Image,
                           reference_answer: Optional[str] = None,
                           question_context: Optional[str] = None) -> Dict[str, Any]:
        """Grade a single answer image"""
        return self.vllm_client.grade_answer(image, reference_answer, question_context)
    
    def capture_and_grade(self, region: Optional[dict] = None,
                         reference_answer: Optional[str] = None,
                         question_context: Optional[str] = None) -> Dict[str, Any]:
        """Capture screenshot and grade immediately"""
        if region:
            image = self.screenshot_capture.capture_region(**region)
        else:
            image = self.screenshot_capture.capture_full_screen()
        return self.grade_single_answer(image, reference_answer, question_context)
    
    def periodic_grading(self, interval: float, duration: float,
                        region: Optional[dict] = None,
                        reference_answer: Optional[str] = None,
                        question_context: Optional[str] = None,
                        save_screenshots: bool = False,
                        output_dir: str = "./screenshots") -> List[Dict[str, Any]]:
        """Periodically capture and grade screenshots"""
        if save_screenshots:
            os.makedirs(output_dir, exist_ok=True)
        
        results = []
        
        def grading_callback(img: Image.Image, index: int):
            result = self.grade_single_answer(img, reference_answer, question_context)
            
            if save_screenshots:
                screenshot_path = os.path.join(output_dir, f"capture_{index:04d}.png")
                self.screenshot_capture.save_image(img, screenshot_path)
                result["screenshot_path"] = screenshot_path
            
            result["capture_index"] = index
            results.append(result)
            
            if "error" in result:
                print(f"[Capture #{index}] Error: {result['error']}")
            else:
                print(f"[Capture #{index}] Score: {result.get('score', 'N/A')}")
        
        self.screenshot_capture.capture_periodically(
            interval=interval,
            duration=duration,
            region=region,
            callback=grading_callback
        )
        
        return results
    
    def load_reference_answer(self, filepath: str) -> str:
        """Load reference answer from markdown file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
