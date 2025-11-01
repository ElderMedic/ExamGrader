#!/usr/bin/env python3
"""Main entry point for ExamGrader"""

import argparse
import json
from exam_grader import ExamGrader, Config


def main():
    parser = argparse.ArgumentParser(
        description="Automated exam paper grading with Vision LLM"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (default: config.yaml)"
    )
    
    parser.add_argument(
        "--api-base",
        type=str,
        help="vLLM API base URL (overrides config)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        help="Model name (overrides config)"
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
        help="Interval between captures in seconds (overrides config)"
    )
    
    parser.add_argument(
        "--duration",
        type=float,
        help="Total duration in seconds (overrides config)"
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
        help="Directory to save screenshots (overrides config)"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = Config(args.config)
    
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
    
    # Initialize grader with config
    grader = ExamGrader(
        vllm_api_base=args.api_base,
        model_name=args.model,
        config=config
    )
    
    # Load reference answer if provided
    reference_answer = None
    if args.reference_answer:
        try:
            reference_answer = grader.load_reference_answer(args.reference_answer)
            print(f"Loaded reference answer from {args.reference_answer}")
        except Exception as e:
            print(f"Warning: Failed to load reference answer: {e}")
    
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
        print(f"Starting periodic grading: interval={args.interval or config.get('screenshot.default_interval', 5.0)}s, duration={args.duration or config.get('screenshot.default_duration', 30.0)}s")
        results = grader.periodic_grading(
            interval=args.interval,
            duration=args.duration,
            region=region,
            reference_answer=reference_answer,
            question_context=args.question_context,
            save_screenshots=args.save_screenshots if args.save_screenshots else None,
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
