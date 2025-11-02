"""Test files for ExamGrader"""

import unittest
import time
from PIL import Image
import os
from exam_grader.screenshot import ScreenshotCapture
from exam_grader.vllm_client import VLLMClient
from exam_grader.grader import ExamGrader


class TestScreenshotCapture(unittest.TestCase):
    """Test screenshot capture functionality"""
    
    def setUp(self):
        self.capture = ScreenshotCapture()
    
    def test_capture_full_screen(self):
        """Test full screen capture"""
        img = self.capture.capture_full_screen()
        self.assertIsInstance(img, Image.Image)
        self.assertGreater(img.width, 0)
        self.assertGreater(img.height, 0)
        print(f"Captured full screen: {img.size}")
    
    def test_capture_region(self):
        """Test region capture"""
        # Capture a small region (100x100 pixels from top-left)
        img = self.capture.capture_region(0, 0, 100, 100)
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (100, 100))
        print(f"Captured region: {img.size}")
    
    def test_save_image(self):
        """Test saving image"""
        img = self.capture.capture_full_screen()
        test_path = "/tmp/test_screenshot.png"
        self.capture.save_image(img, test_path)
        self.assertTrue(os.path.exists(test_path))
        os.remove(test_path)
        print("Image save test passed")


class TestVLLMClient(unittest.TestCase):
    """Test VLLM client functionality"""
    
    def setUp(self):
        # Create a test image
        self.test_image = Image.new('RGB', (800, 600), color='white')
        self.client = VLLMClient()
    
    def test_encode_image(self):
        """Test image encoding"""
        encoded = self.client._encode_image(self.test_image)
        self.assertIsInstance(encoded, str)
        self.assertGreater(len(encoded), 0)
        print("Image encoding test passed")
    
    def test_build_messages(self):
        """Test message building"""
        messages = self.client._build_messages(
            self.test_image,
            reference_answer="Test answer",
            question_context="Test question"
        )
        self.assertIsInstance(messages, list)
        self.assertGreater(len(messages), 0)
        print(f"Built {len(messages)} messages")
    
    def test_parse_response(self):
        """Test response parsing"""
        test_response = "Score: 85\nReasoning: The answer is mostly correct but missing some details."
        score, reasoning = self.client._parse_response(test_response)
        self.assertEqual(score, 85)
        self.assertIn("mostly correct", reasoning.lower())
        print(f"Parsed score: {score}, reasoning: {reasoning[:50]}...")


class TestExamGrader(unittest.TestCase):
    """Test ExamGrader integration"""
    
    def setUp(self):
        self.grader = ExamGrader()
        # Create a test image
        self.test_image = Image.new('RGB', (800, 600), color='white')
    
    def test_grade_single_answer_no_reference(self):
        """Test grading without reference answer"""
        # Note: This will fail if vLLM server is not running
        # It's expected for testing without server
        result = self.grader.grade_single_answer(self.test_image)
        print(f"Grading result: {result}")
        # Check that result has expected structure
        self.assertIsInstance(result, dict)
    
    def test_load_reference_answer(self):
        """Test loading reference answer from file"""
        # Create a test markdown file
        test_file = "/tmp/test_reference.md"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("# Reference Answer\n\nThis is a test answer.")
        
        content = self.grader.load_reference_answer(test_file)
        self.assertIn("Reference Answer", content)
        os.remove(test_file)
        print("Reference answer loading test passed")


def run_basic_tests():
    """Run basic tests that don't require vLLM server"""
    print("=" * 60)
    print("Running Basic Tests")
    print("=" * 60)
    
    # Test screenshot capture
    print("\n1. Testing Screenshot Capture...")
    capture = ScreenshotCapture()
    
    # Full screen test
    print("   - Full screen capture...")
    img = capture.capture_full_screen()
    print(f"     ? Captured {img.size[0]}x{img.size[1]} image")
    
    # Region test
    print("   - Region capture...")
    img_region = capture.capture_region(0, 0, 200, 200)
    print(f"     ? Captured {img_region.size[0]}x{img_region.size[1]} region")
    
    # Save test
    print("   - Save image...")
    test_path = "/tmp/test_screenshot.png"
    capture.save_image(img_region, test_path)
    if os.path.exists(test_path):
        print(f"     ? Image saved to {test_path}")
        os.remove(test_path)
    
    # Test VLLM client (without actual API call)
    print("\n2. Testing VLLM Client...")
    client = VLLMClient()
    
    # Encoding test
    print("   - Image encoding...")
    encoded = client._encode_image(img)
    print(f"     ? Encoded image ({len(encoded)} chars)")
    
    # Message building test
    print("   - Message building...")
    messages = client._build_messages(
        img,
        reference_answer="Test reference answer",
        question_context="Test question"
    )
    print(f"     ? Built {len(messages)} messages")
    
    # Response parsing test
    print("   - Response parsing...")
    test_response = """Score: 92
Reasoning: The student's answer demonstrates good understanding of the concepts."""
    score, reasoning = client._parse_response(test_response)
    print(f"     ? Parsed score: {score}, reasoning length: {len(reasoning)}")
    
    print("\n" + "=" * 60)
    print("Basic Tests Completed!")
    print("=" * 60)
    print("\nNote: To test full grading functionality, ensure vLLM server is running.")
    print("Example: python main.py --mode single")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--basic":
        run_basic_tests()
    else:
        unittest.main()
