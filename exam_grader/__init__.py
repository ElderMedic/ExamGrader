"""ExamGrader - Automated exam paper grading with Vision LLM"""

__version__ = "0.1.0"

from .screenshot import ScreenshotCapture
from .vllm_client import VLLMClient
from .grader import ExamGrader

__all__ = ["ScreenshotCapture", "VLLMClient", "ExamGrader"]
