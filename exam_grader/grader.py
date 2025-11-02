"""Main grading logic"""

import os
import json
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from PIL import Image
from .screenshot import ScreenshotCapture
from .vllm_client import VLLMClient
from .config import Config


class ExamGrader:
    """Main exam grading class"""
    
    def __init__(self, vllm_api_base: Optional[str] = None,
                 model_name: Optional[str] = None,
                 api_key: Optional[str] = None,
                 config: Optional[Config] = None,
                 config_path: Optional[str] = None):
        """Initialize ExamGrader
        
        Args:
            vllm_api_base: Base URL for OpenAI compatible API (overrides config if provided)
            model_name: Model name (overrides config if provided)
            api_key: API key (overrides config and env if provided)
            config: Config instance (creates default if None)
            config_path: Path to config file (used if config is None)
        """
        self.config = config or Config(config_path)
        self.screenshot_capture = ScreenshotCapture()
        self.vllm_client = VLLMClient(vllm_api_base, model_name, api_key, self.config)
    
    def grade_single_answer(self, image: Image.Image,
                           reference_answer: Optional[str] = None,
                           question_context: Optional[str] = None) -> Dict[str, Any]:
        """Grade a single answer image"""
        return self.vllm_client.grade_answer(image, reference_answer, question_context)
    
    def capture_and_grade(self, region: Optional[dict] = None,
                         monitor_index: Optional[int] = None,
                         reference_answer: Optional[str] = None,
                         question_context: Optional[str] = None,
                         save_screenshot: Optional[bool] = False,
                         screenshot_path: Optional[str] = None) -> Dict[str, Any]:
        """Capture screenshot and grade immediately
        
        Args:
            region: Optional dict with left, top, width, height
            monitor_index: Optional monitor index (None uses default)
            reference_answer: Optional reference answer text
            question_context: Optional question context
            save_screenshot: Whether to save the screenshot
            screenshot_path: Path to save screenshot (auto-generated if None and save_screenshot=True)
        """
        if region:
            image = self.screenshot_capture.capture_region(**region)
        else:
            image = self.screenshot_capture.capture_full_screen(monitor_index)
        
        # Save screenshot if requested
        if save_screenshot:
            if screenshot_path is None:
                screenshot_config = self.config.get_screenshot_config()
                save_dir = screenshot_config.get("save_dir", "./screenshots")
                os.makedirs(save_dir, exist_ok=True)
                import time
                timestamp = int(time.time())
                screenshot_path = os.path.join(save_dir, f"capture_{timestamp}.png")
            self.screenshot_capture.save_image(image, screenshot_path)
            print(f"Screenshot saved to: {screenshot_path}")
        
        result = self.grade_single_answer(image, reference_answer, question_context)
        
        # Add screenshot path to result if saved
        if save_screenshot:
            result["screenshot_path"] = screenshot_path
        
        return result
    
    def periodic_grading(self, interval: Optional[float] = None,
                        duration: Optional[float] = None,
                        region: Optional[dict] = None,
                        monitor_index: Optional[int] = None,
                        reference_answer: Optional[str] = None,
                        question_context: Optional[str] = None,
                        save_screenshots: Optional[bool] = None,
                        output_dir: Optional[str] = None,
                        save_records: Optional[bool] = None,
                        records_dir: Optional[str] = None,
                        reference_answer_file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Periodically capture and grade screenshots"""
        screenshot_config = self.config.get_screenshot_config()
        output_config = self.config.get("output", {})
        
        interval = interval or screenshot_config.get("default_interval", 5.0)
        duration = duration or screenshot_config.get("default_duration", 30.0)
        save_screenshots = save_screenshots if save_screenshots is not None else output_config.get("save_screenshots", False)
        output_dir = output_dir or screenshot_config.get("save_dir", "./screenshots")
        
        # Records saving configuration
        save_records = save_records if save_records is not None else output_config.get("auto_save_records", True)
        records_dir = records_dir or output_config.get("records_dir", output_config.get("default_dir", "./results"))
        
        if save_screenshots:
            os.makedirs(output_dir, exist_ok=True)
        
        if save_records:
            os.makedirs(records_dir, exist_ok=True)
        
        results = []
        start_time = datetime.now()
        start_timestamp = time.time()
        
        def grading_callback(img: Image.Image, index: int):
            capture_time = datetime.now()
            timestamp = time.time()
            
            result = self.grade_single_answer(img, reference_answer, question_context)
            
            if save_screenshots:
                screenshot_path = os.path.join(output_dir, f"capture_{index:04d}.png")
                self.screenshot_capture.save_image(img, screenshot_path)
                result["screenshot_path"] = screenshot_path
            
            # Add metadata
            result["capture_index"] = index
            result["timestamp"] = timestamp
            result["datetime"] = capture_time.isoformat()
            result["relative_time"] = timestamp - start_timestamp  # Time since start in seconds
            
            results.append(result)
            
            if "error" in result:
                print(f"[Capture #{index}] Error: {result['error']}")
            else:
                if result.get('student_answer'):
                    print(f"[Capture #{index}] Student Answer: {result.get('student_answer', 'N/A')[:100]}...")  # Show first 100 chars
                print(f"[Capture #{index}] Score: {result.get('score', 'N/A')}")
        
        self.screenshot_capture.capture_periodically(
            interval=interval,
            duration=duration,
            region=region,
            monitor_index=monitor_index,
            callback=grading_callback
        )
        
        # Save records if requested
        if save_records and results:
            end_time = datetime.now()
            records_data = {
                "session_info": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_seconds": duration,
                    "interval_seconds": interval,
                    "total_captures": len(results),
                    "region": region,
                    "monitor_index": monitor_index,
                    "reference_answer_file": reference_answer_file_path,
                    "question_context": question_context,
                },
                "results": results
            }
            
            # Generate filename with timestamp
            timestamp_str = start_time.strftime("%Y%m%d_%H%M%S")
            records_filename = f"grading_records_{timestamp_str}.json"
            records_path = os.path.join(records_dir, records_filename)
            
            with open(records_path, 'w', encoding='utf-8') as f:
                json.dump(records_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n[Records] Grading records saved to: {records_path}")
        
        return results
    
    def load_reference_answer(self, filepath: str) -> str:
        """Load reference answer from markdown file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
