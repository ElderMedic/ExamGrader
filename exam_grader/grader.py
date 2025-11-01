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
        """Initialize ExamGrader
        
        Args:
            vllm_api_base: Base URL for vLLM API
            model_name: Name of the vision model to use
        """
        self.screenshot_capture = ScreenshotCapture()
        self.vllm_client = VLLMClient(vllm_api_base, model_name)
    
    def grade_single_answer(self, image: Image.Image,
                           reference_answer: Optional[str] = None,
                           question_context: Optional[str] = None) -> Dict[str, Any]:
        """Grade a single answer image
        
        Args:
            image: PIL Image of student's answer
            reference_answer: Optional reference answer in markdown
            question_context: Optional question context
            
        Returns:
            Dict with grading results
        """
        result = self.vllm_client.grade_answer(
            image=image,
            reference_answer=reference_answer,
            question_context=question_context
        )
        return result
    
    def capture_and_grade(self, region: Optional[dict] = None,
                         reference_answer: Optional[str] = None,
                         question_context: Optional[str] = None) -> Dict[str, Any]:
        """Capture screenshot and grade immediately
        
        Args:
            region: Optional screenshot region dict
            reference_answer: Optional reference answer
            question_context: Optional question context
            
        Returns:
            Dict with grading results
        """
        if region:
            image = self.screenshot_capture.capture_region(
                region["left"], region["top"],
                region["width"], region["height"]
            )
        else:
            image = self.screenshot_capture.capture_full_screen()
        
        return self.grade_single_answer(image, reference_answer, question_context)
    
    def periodic_grading(self, interval: float, duration: float,
                        region: Optional[dict] = None,
                        reference_answer: Optional[str] = None,
                        question_context: Optional[str] = None,
                        save_screenshots: bool = False,
                        output_dir: str = "./screenshots") -> List[Dict[str, Any]]:
        """Periodically capture and grade screenshots
        
        Args:
            interval: Time interval between captures in seconds
            duration: Total duration to capture in seconds
            region: Optional screenshot region
            reference_answer: Optional reference answer
            question_context: Optional question context
            save_screenshots: Whether to save captured screenshots
            output_dir: Directory to save screenshots
            
        Returns:
            List of grading result dicts
        """
        if save_screenshots:
            os.makedirs(output_dir, exist_ok=True)
        
        results = []
        
        def grading_callback(img: Image.Image, index: int):
            """Callback for each capture"""
            print(f"\n[Capture #{index}] Grading...")
            result = self.grade_single_answer(
                img, reference_answer, question_context
            )
            
            if save_screenshots:
                screenshot_path = os.path.join(output_dir, f"capture_{index:04d}.png")
                self.screenshot_capture.save_image(img, screenshot_path)
                result["screenshot_path"] = screenshot_path
            
            result["capture_index"] = index
            results.append(result)
            
            # Print results
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"Score: {result.get('score', 'N/A')}")
                print(f"Reasoning: {result.get('reasoning', 'N/A')[:100]}...")
        
        self.screenshot_capture.capture_periodically(
            interval=interval,
            duration=duration,
            region=region,
            callback=grading_callback
        )
        
        return results
    
    def load_reference_answer(self, filepath: str) -> str:
        """Load reference answer from markdown file
        
        Args:
            filepath: Path to markdown file
            
        Returns:
            Content of the file as string
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
