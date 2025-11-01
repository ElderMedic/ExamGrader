#!/usr/bin/env python3
"""Main entry point for ExamGrader"""

import argparse
import json
from exam_grader import ExamGrader, ScreenshotCapture


def main():
    parser = argparse.ArgumentParser(
        description="Automated exam paper grading with Vision LLM"
    )
    
    parser.add_argument(
        "--api-base",
        type=str,
        default="http://localhost:8000/v1",
        help="vLLM API base URL (default: http://localhost:8000/v1)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="deepseek-ocr",
        help="Model name (default: deepseek-ocr)"
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["single", "periodic"],
        default="single",
        help="Grading mode: single capture or periodic (default: single)"
    )
    
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Interval between captures in seconds (for periodic mode, default: 5.0)"
    )
    
    parser.add_argument(
        "--duration",
        type=float,
        default=30.0,
        help="Total duration in seconds (for periodic mode, default: 30.0)"
    )
    
    parser.add_argument(
        "--region",
        type=str,
        help="Screenshot region as 'left,top,width,height' (e.g., '100,100,800,600')"
    )
    
    parser.add_argument(
        "--reference-answer",
        type=str,
        help="Path to reference answer markdown file"
    )
    
    parser.add_argument(
        "--question-context",
        type=str,
        help="Question context or instructions"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path for results (JSON format)"
    )
    
    parser.add_argument(
        "--save-screenshots",
        action="store_true",
        help="Save captured screenshots to disk"
    )
    
    parser.add_argument(
        "--screenshot-dir",
        type=str,
        default="./screenshots",
        help="Directory to save screenshots (default: ./screenshots)"
    )
    
    args = parser.parse_args()
    
    # Parse region if provided
    region = None
    if args.region:
        try:
            parts = [int(x.strip()) for x in args.region.split(',')]
            if len(parts) == 4:
                region = {
                    "left": parts[0],
                    "top": parts[1],
                    "width": parts[2],
                    "height": parts[3]
                }
            else:
                print("Warning: Invalid region format. Using full screen.")
        except ValueError:
            print("Warning: Invalid region format. Using full screen.")
    
    # Load reference answer if provided
    reference_answer = None
    if args.reference_answer:
        try:
            grader = ExamGrader(args.api_base, args.model)
            reference_answer = grader.load_reference_answer(args.reference_answer)
            print(f"Loaded reference answer from {args.reference_answer}")
        except Exception as e:
            print(f"Warning: Failed to load reference answer: {e}")
    
    # Initialize grader
    grader = ExamGrader(args.api_base, args.model)
    
    # Execute grading
    if args.mode == "single":
        print("Capturing screenshot and grading...")
        result = grader.capture_and_grade(
            region=region,
            reference_answer=reference_answer,
            question_context=args.question_context
        )
        
        print("\n=== Grading Result ===")
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Score: {result.get('score', 'N/A')}")
            print(f"Reasoning: {result.get('reasoning', 'N/A')}")
        
        results = [result]
        
    else:  # periodic mode
        print(f"Starting periodic grading: interval={args.interval}s, duration={args.duration}s")
        results = grader.periodic_grading(
            interval=args.interval,
            duration=args.duration,
            region=region,
            reference_answer=reference_answer,
            question_context=args.question_context,
            save_screenshots=args.save_screenshots,
            output_dir=args.screenshot_dir
        )
        
        print(f"\n=== Completed {len(results)} gradings ===")
        for i, result in enumerate(results, 1):
            if "error" not in result:
                print(f"Capture #{i}: Score={result.get('score', 'N/A')}")
    
    # Save results if output file specified
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
