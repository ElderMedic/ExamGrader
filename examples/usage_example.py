#!/usr/bin/env python3
"""Simple usage example for ExamGrader"""

from exam_grader import ExamGrader, ScreenshotCapture
from PIL import Image

def example_single_capture():
    """Example: Single capture and grade"""
    print("=== Example: Single Capture and Grade ===\n")
    
    # Initialize grader
    grader = ExamGrader(
        vllm_api_base="http://localhost:8000/v1",
        model_name="deepseek-ocr"
    )
    
    # Capture full screen
    print("1. Capturing screenshot...")
    result = grader.capture_and_grade()
    
    # Display results
    print("\n2. Grading Results:")
    if "error" in result:
        print(f"   Error: {result['error']}")
    else:
        print(f"   Score: {result.get('score', 'N/A')}")
        print(f"   Reasoning: {result.get('reasoning', 'N/A')}")


def example_with_reference():
    """Example: Grade with reference answer"""
    print("\n=== Example: Grade with Reference Answer ===\n")
    
    grader = ExamGrader()
    
    # Load reference answer
    reference_answer = """# Reference Answer

The correct answer should include:
1. Key concept explanation
2. Application examples
3. Conclusion"""
    
    # Capture region (example: 100,100,800,600)
    print("1. Capturing specific region...")
    result = grader.capture_and_grade(
        region={"left": 100, "top": 100, "width": 800, "height": 600},
        reference_answer=reference_answer,
        question_context="Question 1: Explain the main concept"
    )
    
    print("\n2. Grading Results:")
    if "error" not in result:
        print(f"   Score: {result.get('score', 'N/A')}")
        print(f"   Reasoning: {result.get('reasoning', 'N/A')[:200]}...")


def example_periodic_capture():
    """Example: Periodic capture and grading"""
    print("\n=== Example: Periodic Capture ===\n")
    
    grader = ExamGrader()
    
    print("Starting periodic capture (5s interval, 20s duration)...")
    print("Make sure vLLM server is running!\n")
    
    results = grader.periodic_grading(
        interval=5.0,
        duration=20.0,
        save_screenshots=True,
        output_dir="./screenshots"
    )
    
    print(f"\nCompleted {len(results)} gradings:")
    for i, result in enumerate(results, 1):
        if "error" not in result:
            print(f"  Capture #{i}: Score = {result.get('score', 'N/A')}")


def example_manual_image():
    """Example: Grade a manually loaded image"""
    print("\n=== Example: Grade Manual Image ===\n")
    
    # Create a test image (in real usage, load from file)
    test_image = Image.new('RGB', (800, 600), color='white')
    
    grader = ExamGrader()
    result = grader.grade_single_answer(
        image=test_image,
        reference_answer="Reference answer here",
        question_context="Question context"
    )
    
    print("Grading Results:")
    if "error" not in result:
        print(f"  Score: {result.get('score', 'N/A')}")
        print(f"  Reasoning: {result.get('reasoning', 'N/A')}")


if __name__ == "__main__":
    import sys
    
    print("ExamGrader Usage Examples\n")
    print("Note: These examples require vLLM server to be running.")
    print("Start server with: python -m vllm.entrypoints.openai.api_server --model deepseek-ocr\n")
    
    if len(sys.argv) > 1:
        example_name = sys.argv[1]
        if example_name == "single":
            example_single_capture()
        elif example_name == "reference":
            example_with_reference()
        elif example_name == "periodic":
            example_periodic_capture()
        elif example_name == "manual":
            example_manual_image()
        else:
            print(f"Unknown example: {example_name}")
            print("Available: single, reference, periodic, manual")
    else:
        print("Run examples with:")
        print("  python examples/usage_example.py single")
        print("  python examples/usage_example.py reference")
        print("  python examples/usage_example.py periodic")
        print("  python examples/usage_example.py manual")
