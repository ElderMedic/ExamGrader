#!/usr/bin/env python3
"""Main entry point for ExamGrader"""

import argparse
import json
import os
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
        help="OpenAI compatible API base URL (overrides config)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        help="Model name (overrides config)"
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        help="API key (overrides config and env)"
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
        "--monitor",
        type=int,
        help="Monitor index to capture (1 for first monitor, 2 for second, etc. Use --list-monitors to see available)"
    )
    
    parser.add_argument(
        "--list-monitors",
        action="store_true",
        help="List all available monitors and exit"
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
    
    parser.add_argument(
        "--save-records",
        action="store_true",
        help="Save grading records (default: enabled in periodic mode)"
    )
    
    parser.add_argument(
        "--no-save-records",
        action="store_true",
        help="Disable automatic saving of grading records"
    )
    
    parser.add_argument(
        "--records-dir",
        type=str,
        help="Directory to save grading records (overrides config)"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = Config(args.config)
    
    # List monitors if requested
    if args.list_monitors:
        from exam_grader import ScreenshotCapture
        capture = ScreenshotCapture()
        capture.print_monitors()
        return
    
    # Parse region if provided
    region = None
    if args.region:
        # Command line region takes precedence
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
    else:
        # Try to get default region from config
        screenshot_config = config.get_screenshot_config()
        default_region = screenshot_config.get("default_region")
        if default_region and isinstance(default_region, list) and len(default_region) == 4:
            region = {
                "left": default_region[0],
                "top": default_region[1],
                "width": default_region[2],
                "height": default_region[3]
            }
    
    # Get monitor index from config or args
    monitor_index = args.monitor
    if monitor_index is None:
        screenshot_config = config.get_screenshot_config()
        monitor_index = screenshot_config.get("default_monitor")
    
    # Initialize grader with config
    grader = ExamGrader(
        vllm_api_base=args.api_base,
        model_name=args.model,
        api_key=args.api_key,
        config=config
    )
    
    # Load reference answer if provided
    reference_answer = None
    reference_answer_path = None
    
    if args.reference_answer:
        # Use command line argument (highest priority)
        reference_answer_path = args.reference_answer
    else:
        # Try to load from config default
        ref_config = config.get("reference_answer", {})
        default_ref_file = ref_config.get("default_file")
        if default_ref_file:
            # Check if file exists (could be relative to project root)
            from pathlib import Path
            project_root = Path(__file__).parent
            default_ref_path = project_root / default_ref_file
            
            if default_ref_path.exists():
                reference_answer_path = str(default_ref_path)
                print(f"Using default reference answer from config: {default_ref_file}")
    
    if reference_answer_path:
        try:
            reference_answer = grader.load_reference_answer(reference_answer_path)
            print(f"Loaded reference answer from {reference_answer_path}")
        except Exception as e:
            print(f"Warning: Failed to load reference answer: {e}")
    
    # Execute grading
    if args.mode == "single":
        print("Capturing screenshot and grading...")
        if reference_answer:
            print(f"Using reference answer (length: {len(reference_answer)} chars)")
        else:
            print("⚠️  Warning: No reference answer provided!")
        result = grader.capture_and_grade(
            region=region,
            monitor_index=monitor_index,
            reference_answer=reference_answer,
            question_context=args.question_context,
            save_screenshot=args.save_screenshots,
            screenshot_path=os.path.join(args.screenshot_dir, "capture_single.png") if (args.save_screenshots and args.screenshot_dir) else None
        )
        
        print("\n=== Grading Result ===")
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            if result.get('student_answer'):
                print(f"Recognized Student Answer: {result.get('student_answer', 'N/A')}")
            print(f"Score: {result.get('score', 'N/A')}")
            print(f"Reasoning: {result.get('reasoning', 'N/A')}")
        
        results = [result]
        
    else:  # periodic mode
        print(f"Starting periodic grading: interval={args.interval or config.get('screenshot.default_interval', 5.0)}s, duration={args.duration or config.get('screenshot.default_duration', 30.0)}s")
        # Determine save_records setting
        save_records = None
        if args.save_records:
            save_records = True
        elif args.no_save_records:
            save_records = False
        
        # Store reference answer file path for records
        reference_answer_file_path = reference_answer_path
        
        results = grader.periodic_grading(
            interval=args.interval,
            duration=args.duration,
            region=region,
            monitor_index=monitor_index,
            reference_answer=reference_answer,
            question_context=args.question_context,
            save_screenshots=args.save_screenshots if args.save_screenshots else None,
            output_dir=args.screenshot_dir,
            save_records=save_records,
            records_dir=args.records_dir,
            reference_answer_file_path=reference_answer_file_path
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
