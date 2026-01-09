#!/usr/bin/env python3
"""
Evaluate resumes against extracted criteria using LLM with structured outputs.
"""

import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from anthropic import Anthropic
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


EVALUATION_PROMPT = """You are an expert recruiter evaluating a candidate's resume against specific job criteria.

For each criterion provided, you must:
1. Assign a binary score (0 or 1):
   - 1: Criterion is clearly met or demonstrated in the resume
   - 0: Criterion is not met or not evident in the resume

2. Provide a brief citation or reasoning (1-2 sentences) explaining your score, with specific references to resume content if applicable.

Be objective and evidence-based. Only give a score of 1 if there is clear evidence in the resume.

Here is the candidate's resume:

<resume>
{resume_content}
</resume>

Here are the criteria to evaluate:

<criteria>
{criteria_json}
</criteria>

Return your evaluation as a JSON object with this structure:
{{
  "candidate_name": "extracted from resume",
  "evaluations": [
    {{
      "category": "category name",
      "criterion": "criterion description",
      "weight": "Critical/High/Medium/Low",
      "score": 0 or 1,
      "reasoning": "Brief explanation with resume citations"
    }}
  ],
  "overall_summary": "2-3 sentence summary of candidate's fit"
}}

Evaluate all criteria thoroughly and return the complete JSON."""


def evaluate_resume_with_llm(resume_content: str, criteria: dict, api_key: str = None) -> dict:
    """Use Claude to evaluate a resume against criteria."""

    client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    # Format criteria for the prompt
    criteria_json = json.dumps(criteria, indent=2)

    prompt = EVALUATION_PROMPT.format(
        resume_content=resume_content,
        criteria_json=criteria_json
    )

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # Extract JSON from response
    response_text = message.content[0].text

    try:
        # Look for JSON block
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        elif "{" in response_text:
            # Find the JSON object
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_text = response_text[json_start:json_end]
        else:
            json_text = response_text

        evaluation = json.loads(json_text)
        return evaluation
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from LLM response: {e}")
        print(f"Response text: {response_text[:500]}")
        raise


def calculate_weighted_score(evaluations: List[Dict]) -> Dict[str, float]:
    """Calculate weighted scores based on criterion weights."""

    weight_values = {
        'Critical': 4.0,
        'High': 3.0,
        'Medium': 2.0,
        'Low': 1.0
    }

    total_weighted_score = 0
    total_weight = 0
    category_scores = {}

    for eval_item in evaluations:
        weight = weight_values.get(eval_item.get('weight', 'Medium'), 2.0)
        score = eval_item.get('score', 0)
        category = eval_item.get('category', 'Other')

        total_weighted_score += score * weight
        total_weight += weight

        if category not in category_scores:
            category_scores[category] = {'score': 0, 'weight': 0, 'count': 0}

        category_scores[category]['score'] += score * weight
        category_scores[category]['weight'] += weight
        category_scores[category]['count'] += 1

    # Calculate normalized scores (0-100)
    overall_score = (total_weighted_score / total_weight * 100) if total_weight > 0 else 0

    # Calculate category scores
    for category in category_scores:
        cat_data = category_scores[category]
        cat_data['normalized_score'] = (cat_data['score'] / cat_data['weight'] * 100) if cat_data['weight'] > 0 else 0

    return {
        'overall_score': round(overall_score, 2),
        'category_scores': category_scores,
        'total_criteria': len(evaluations),
        'criteria_met': sum(1 for e in evaluations if e.get('score') == 1)
    }


def generate_excel_report(all_evaluations: List[Dict], criteria: dict, output_path: str):
    """Generate comprehensive Excel report with multiple sheets."""

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Sheet 1: Summary Rankings
        summary_data = []
        for eval_result in all_evaluations:
            summary_data.append({
                'Rank': 0,  # Will be filled after sorting
                'Candidate Name': eval_result['candidate_name'],
                'Overall Score': eval_result['scores']['overall_score'],
                'Criteria Met': f"{eval_result['scores']['criteria_met']}/{eval_result['scores']['total_criteria']}",
                'Match %': round(eval_result['scores']['criteria_met'] / eval_result['scores']['total_criteria'] * 100, 1) if eval_result['scores']['total_criteria'] > 0 else 0,
                'Summary': eval_result['overall_summary']
            })

        # Sort by overall score
        summary_data.sort(key=lambda x: x['Overall Score'], reverse=True)
        for i, row in enumerate(summary_data, 1):
            row['Rank'] = i

        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Rankings', index=False)

        # Sheet 2: Category Scores
        category_data = []
        for eval_result in all_evaluations:
            row = {'Candidate': eval_result['candidate_name']}
            for category, scores in eval_result['scores']['category_scores'].items():
                row[f"{category} (Score)"] = round(scores['normalized_score'], 1)
                row[f"{category} (Met/Total)"] = f"{int(scores['score'] / max(1, scores['weight']) * scores['count'])}/{scores['count']}"

            category_data.append(row)

        category_df = pd.DataFrame(category_data)
        category_df.to_excel(writer, sheet_name='Category Scores', index=False)

        # Sheet 3: Detailed Criteria Matrix
        # Create a matrix with candidates as rows and criteria as columns
        detailed_data = []

        for eval_result in all_evaluations:
            row = {
                'Candidate': eval_result['candidate_name'],
                'Overall Score': eval_result['scores']['overall_score']
            }

            for eval_item in eval_result['evaluations']:
                criterion_key = f"{eval_item['category']}: {eval_item['criterion']}"
                row[criterion_key] = eval_item['score']

            detailed_data.append(row)

        detailed_df = pd.DataFrame(detailed_data)
        detailed_df.to_excel(writer, sheet_name='Criteria Matrix', index=False)

        # Sheet 4: Detailed Evaluations with Reasoning
        reasoning_data = []
        for eval_result in all_evaluations:
            for eval_item in eval_result['evaluations']:
                reasoning_data.append({
                    'Candidate': eval_result['candidate_name'],
                    'Category': eval_item['category'],
                    'Criterion': eval_item['criterion'],
                    'Weight': eval_item['weight'],
                    'Score': eval_item['score'],
                    'Met': '✓' if eval_item['score'] == 1 else '✗',
                    'Reasoning': eval_item['reasoning']
                })

        reasoning_df = pd.DataFrame(reasoning_data)
        reasoning_df.to_excel(writer, sheet_name='Detailed Evaluations', index=False)

        # Sheet 5: Criteria Reference
        criteria_ref = []
        for category in criteria.get('categories', []):
            for criterion in category.get('criteria', []):
                criteria_ref.append({
                    'Category': category['name'],
                    'Criterion': criterion['criterion'],
                    'Weight': criterion['weight'],
                    'Evaluation Guide': criterion['evaluation_guide']
                })

        criteria_df = pd.DataFrame(criteria_ref)
        criteria_df.to_excel(writer, sheet_name='Criteria Reference', index=False)

    print(f"Excel report generated: {output_path}")


def generate_markdown_report(all_evaluations: List[Dict], criteria: dict, output_path: str):
    """Generate detailed markdown report."""

    # Sort by overall score
    sorted_evals = sorted(all_evaluations, key=lambda x: x['scores']['overall_score'], reverse=True)

    report = f"""# Resume Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Job Title:** {criteria.get('job_title', 'N/A')}
**Total Candidates Analyzed:** {len(all_evaluations)}
**Total Evaluation Criteria:** {sorted_evals[0]['scores']['total_criteria'] if sorted_evals else 0}

---

## Executive Summary

### Top 3 Candidates

"""

    for i, eval_result in enumerate(sorted_evals[:3], 1):
        report += f"{i}. **{eval_result['candidate_name']}** - Score: {eval_result['scores']['overall_score']}/100\n"
        report += f"   - Criteria Met: {eval_result['scores']['criteria_met']}/{eval_result['scores']['total_criteria']}\n"
        report += f"   - {eval_result['overall_summary']}\n\n"

    report += "\n---\n\n## Complete Rankings\n\n"
    report += "| Rank | Candidate | Overall Score | Criteria Met | Match % |\n"
    report += "|------|-----------|---------------|--------------|----------|\n"

    for i, eval_result in enumerate(sorted_evals, 1):
        match_pct = round(eval_result['scores']['criteria_met'] / eval_result['scores']['total_criteria'] * 100, 1)
        report += f"| {i} | {eval_result['candidate_name']} | {eval_result['scores']['overall_score']} | {eval_result['scores']['criteria_met']}/{eval_result['scores']['total_criteria']} | {match_pct}% |\n"

    report += "\n---\n\n## Detailed Candidate Analysis\n\n"

    for eval_result in sorted_evals:
        report += f"### {eval_result['candidate_name']}\n\n"
        report += f"**Overall Score:** {eval_result['scores']['overall_score']}/100  \n"
        report += f"**Criteria Met:** {eval_result['scores']['criteria_met']}/{eval_result['scores']['total_criteria']}  \n"
        report += f"**Summary:** {eval_result['overall_summary']}\n\n"

        report += "#### Category Breakdown\n\n"
        for category, scores in eval_result['scores']['category_scores'].items():
            criteria_met = int(scores['score'] / max(1, scores['weight']) * scores['count'])
            report += f"- **{category}:** {round(scores['normalized_score'], 1)}/100 ({criteria_met}/{scores['count']} criteria met)\n"

        report += "\n#### Strengths\n\n"
        strengths = [e for e in eval_result['evaluations'] if e['score'] == 1 and e['weight'] in ['Critical', 'High']]
        if strengths:
            for strength in strengths[:5]:
                report += f"- ✓ **{strength['criterion']}** ({strength['category']})\n"
                report += f"  - {strength['reasoning']}\n"
        else:
            report += "- No high-priority criteria met\n"

        report += "\n#### Gaps\n\n"
        gaps = [e for e in eval_result['evaluations'] if e['score'] == 0 and e['weight'] in ['Critical', 'High']]
        if gaps:
            for gap in gaps[:5]:
                report += f"- ✗ **{gap['criterion']}** ({gap['category']})\n"
                report += f"  - {gap['reasoning']}\n"
        else:
            report += "- No significant gaps identified\n"

        report += "\n---\n\n"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"Markdown report generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Evaluate resumes against criteria using LLM')
    parser.add_argument('--resumes-dir', required=True, help='Directory containing resume markdown files')
    parser.add_argument('--criteria-json', required=True, help='Path to criteria JSON file from extract_criteria.py')
    parser.add_argument('--output-dir', default='./evaluation_output', help='Output directory for reports')
    parser.add_argument('--api-key', help='Anthropic API key (or set ANTHROPIC_API_KEY env var)')

    args = parser.parse_args()

    # Load criteria
    with open(args.criteria_json, 'r', encoding='utf-8') as f:
        criteria = json.load(f)

    print(f"Loaded criteria with {len(criteria.get('categories', []))} categories")

    # Find all resume files
    resumes_dir = Path(args.resumes_dir)
    resume_files = list(resumes_dir.glob('*.md'))

    if not resume_files:
        print(f"No markdown files found in {args.resumes_dir}")
        return

    print(f"\nFound {len(resume_files)} resume(s) to evaluate...")

    # Evaluate all resumes
    all_evaluations = []

    for i, resume_file in enumerate(resume_files, 1):
        print(f"\n[{i}/{len(resume_files)}] Evaluating: {resume_file.name}")

        with open(resume_file, 'r', encoding='utf-8') as f:
            resume_content = f.read()

        try:
            evaluation = evaluate_resume_with_llm(resume_content, criteria, args.api_key)

            # Calculate scores
            scores = calculate_weighted_score(evaluation['evaluations'])
            evaluation['scores'] = scores
            evaluation['file_path'] = str(resume_file)

            all_evaluations.append(evaluation)

            print(f"  Overall Score: {scores['overall_score']}/100")
            print(f"  Criteria Met: {scores['criteria_met']}/{scores['total_criteria']}")

        except Exception as e:
            print(f"  Error evaluating {resume_file.name}: {e}")
            continue

    if not all_evaluations:
        print("\nNo resumes were successfully evaluated.")
        return

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate reports
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_path = output_dir / f'resume_evaluation_{timestamp}.xlsx'
    markdown_path = output_dir / f'resume_evaluation_{timestamp}.md'
    json_path = output_dir / f'resume_evaluation_{timestamp}.json'

    print("\nGenerating reports...")

    generate_excel_report(all_evaluations, criteria, str(excel_path))
    generate_markdown_report(all_evaluations, criteria, str(markdown_path))

    # Save raw JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_evaluations, f, indent=2, ensure_ascii=False)

    print(f"\nEvaluation complete!")
    print(f"Reports saved to: {output_dir}")
    print(f"- Excel: {excel_path.name}")
    print(f"- Markdown: {markdown_path.name}")
    print(f"- JSON: {json_path.name}")


if __name__ == '__main__':
    main()
