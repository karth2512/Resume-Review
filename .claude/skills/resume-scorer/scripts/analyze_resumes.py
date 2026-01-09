#!/usr/bin/env python3
"""
Resume Analysis Script - LLM-powered orchestration
Orchestrates the complete resume analysis workflow:
1. Extract criteria from job description using LLM
2. Evaluate each resume against criteria using LLM
3. Generate comprehensive reports
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)

    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False

    print(result.stdout)
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Analyze resumes against job description using LLM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python analyze_resumes.py --resumes-dir ./parsed_resumes --job-desc ./job.txt

  # With custom output directory
  python analyze_resumes.py --resumes-dir ./resumes --job-desc ./job.txt --output-dir ./results

  # With API key
  python analyze_resumes.py --resumes-dir ./resumes --job-desc ./job.txt --api-key YOUR_KEY
        """
    )

    parser.add_argument('--resumes-dir', required=True,
                       help='Directory containing resume markdown files')
    parser.add_argument('--job-desc', required=True,
                       help='Path to job description file')
    parser.add_argument('--output-dir', default='./resume_analysis_output',
                       help='Output directory for all results (default: ./resume_analysis_output)')
    parser.add_argument('--api-key',
                       help='Anthropic API key (or set ANTHROPIC_API_KEY env var)')

    args = parser.parse_args()

    # Validate inputs
    if not Path(args.resumes_dir).exists():
        print(f"Error: Resumes directory not found: {args.resumes_dir}")
        sys.exit(1)

    if not Path(args.job_desc).exists():
        print(f"Error: Job description file not found: {args.job_desc}")
        sys.exit(1)

    # Check for API key
    api_key = args.api_key or os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found.")
        print("Please set your API key using one of these methods:")
        print("  1. Create a .env file with: ANTHROPIC_API_KEY=your_key")
        print("  2. Set environment variable: export ANTHROPIC_API_KEY=your_key")
        print("  3. Pass via argument: --api-key your_key")
        sys.exit(1)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    criteria_dir = output_dir / 'criteria'
    criteria_dir.mkdir(exist_ok=True)

    print("\n" + "="*60)
    print("RESUME ANALYSIS WORKFLOW - LLM POWERED")
    print("="*60)
    print(f"Resumes Directory: {args.resumes_dir}")
    print(f"Job Description: {args.job_desc}")
    print(f"Output Directory: {args.output_dir}")

    # Get script directory
    script_dir = Path(__file__).parent

    # Step 1: Extract criteria from job description
    print("\n" + "="*60)
    print("STEP 1: Extracting Evaluation Criteria from Job Description")
    print("="*60)

    extract_cmd = [
        sys.executable,
        str(script_dir / 'extract_criteria.py'),
        '--job-desc', args.job_desc,
        '--output-dir', str(criteria_dir),
        '--api-key', api_key
    ]

    if not run_command(' '.join(f'"{c}"' if ' ' in str(c) else str(c) for c in extract_cmd),
                       "Extracting criteria using LLM..."):
        print("\nFailed to extract criteria. Exiting.")
        sys.exit(1)

    criteria_json = criteria_dir / 'evaluation_criteria.json'
    if not criteria_json.exists():
        print(f"\nError: Criteria file not generated: {criteria_json}")
        sys.exit(1)

    # Step 2: Evaluate resumes against criteria
    print("\n" + "="*60)
    print("STEP 2: Evaluating Resumes Against Criteria")
    print("="*60)

    evaluate_cmd = [
        sys.executable,
        str(script_dir / 'evaluate_resumes.py'),
        '--resumes-dir', args.resumes_dir,
        '--criteria-json', str(criteria_json),
        '--output-dir', str(output_dir),
        '--api-key', api_key
    ]

    if not run_command(' '.join(f'"{c}"' if ' ' in str(c) else str(c) for c in evaluate_cmd),
                       "Evaluating resumes using LLM..."):
        print("\nFailed to evaluate resumes. Exiting.")
        sys.exit(1)

    # Summary
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE!")
    print("="*60)
    print(f"\nAll results saved to: {output_dir}")
    print("\nGenerated files:")
    print(f"  - Evaluation criteria: {criteria_dir}/")
    print(f"    - evaluation_criteria.md (human-readable)")
    print(f"    - evaluation_criteria.json (structured data)")
    print(f"  - Analysis results: {output_dir}/")
    print(f"    - resume_evaluation_*.xlsx (Excel report)")
    print(f"    - resume_evaluation_*.md (markdown report)")
    print(f"    - resume_evaluation_*.json (raw data)")

    # Find and display the latest Excel file
    excel_files = list(output_dir.glob('resume_evaluation_*.xlsx'))
    if excel_files:
        latest_excel = max(excel_files, key=lambda p: p.stat().st_mtime)
        print(f"\nMain Excel Report: {latest_excel}")
        print("\nExcel Sheets:")
        print("  1. Rankings - Sorted candidate summary")
        print("  2. Category Scores - Scores by criteria category")
        print("  3. Criteria Matrix - Binary matrix of all criteria")
        print("  4. Detailed Evaluations - Full reasoning for each criterion")
        print("  5. Criteria Reference - Original evaluation criteria")

    print("\n" + "="*60)
    print("Next Steps:")
    print("  - Open the Excel file to review rankings and filter candidates")
    print("  - Read the markdown report for detailed analysis")
    print("  - Use the criteria matrix to compare specific skills across candidates")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
