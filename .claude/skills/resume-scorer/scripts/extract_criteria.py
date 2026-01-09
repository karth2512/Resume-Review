#!/usr/bin/env python3
"""
Extract and structure evaluation criteria from job descriptions using LLM.
"""

import os
import json
import argparse
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


CRITERIA_EXTRACTION_PROMPT = """You are an expert recruiter analyzing a job description. Extract and categorize all evaluation criteria that should be used to assess candidates.

Organize the criteria into these categories:
1. **Required Technical Skills** - Must-have technical competencies
2. **Preferred Technical Skills** - Nice-to-have technical competencies
3. **Experience Requirements** - Years of experience, specific roles, industry experience
4. **Education Requirements** - Degrees, certifications, training
5. **Soft Skills** - Communication, leadership, teamwork, etc.
6. **Domain Knowledge** - Industry-specific or business domain expertise
7. **Other Requirements** - Any other important criteria

For each criterion, provide:
- **Category**: Which category it belongs to
- **Criterion**: Clear, specific description
- **Weight**: Importance (Critical, High, Medium, Low)
- **Evaluation Guide**: How to assess this criterion from a resume

Return your analysis as a JSON object with this structure:
{{
  "job_title": "extracted job title",
  "categories": [
    {{
      "name": "Required Technical Skills",
      "criteria": [
        {{
          "criterion": "Python programming",
          "weight": "Critical",
          "evaluation_guide": "Look for Python mentioned in skills or project descriptions, code samples, or work experience using Python"
        }}
      ]
    }}
  ]
}}

Here is the job description:

<job_description>
{job_description}
</job_description>

Analyze this thoroughly and extract all relevant criteria."""


def extract_criteria_with_llm(job_description: str, api_key: str = None) -> dict:
    """Use Claude to extract structured criteria from job description."""

    client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    prompt = CRITERIA_EXTRACTION_PROMPT.format(job_description=job_description)

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # Extract JSON from response
    response_text = message.content[0].text

    # Try to parse JSON from the response
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

        criteria = json.loads(json_text)
        return criteria
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from LLM response: {e}")
        print(f"Response text: {response_text[:500]}")
        raise


def save_criteria_as_markdown(criteria: dict, output_path: str):
    """Save extracted criteria as a markdown file."""

    md_content = f"""# Evaluation Criteria: {criteria.get('job_title', 'Position')}

This document contains the structured evaluation criteria extracted from the job description.

"""

    for category in criteria.get('categories', []):
        md_content += f"## {category['name']}\n\n"

        for item in category.get('criteria', []):
            md_content += f"### {item['criterion']}\n\n"
            md_content += f"**Weight:** {item['weight']}  \n"
            md_content += f"**Evaluation Guide:** {item['evaluation_guide']}\n\n"
            md_content += "---\n\n"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"Criteria markdown saved to: {output_path}")


def save_criteria_as_json(criteria: dict, output_path: str):
    """Save extracted criteria as JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(criteria, f, indent=2, ensure_ascii=False)

    print(f"Criteria JSON saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Extract evaluation criteria from job description using LLM')
    parser.add_argument('--job-desc', required=True, help='Path to job description file')
    parser.add_argument('--output-dir', default='./criteria_output', help='Output directory for criteria files')
    parser.add_argument('--api-key', help='Anthropic API key (or set ANTHROPIC_API_KEY env var)')

    args = parser.parse_args()

    # Read job description
    with open(args.job_desc, 'r', encoding='utf-8') as f:
        job_description = f.read()

    print("Extracting criteria from job description using LLM...")

    # Extract criteria
    criteria = extract_criteria_with_llm(job_description, args.api_key)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save in both formats
    md_path = output_dir / 'evaluation_criteria.md'
    json_path = output_dir / 'evaluation_criteria.json'

    save_criteria_as_markdown(criteria, str(md_path))
    save_criteria_as_json(criteria, str(json_path))

    # Print summary
    print("\nCriteria Extraction Summary:")
    print(f"Job Title: {criteria.get('job_title', 'N/A')}")
    print(f"Total Categories: {len(criteria.get('categories', []))}")

    total_criteria = sum(len(cat.get('criteria', [])) for cat in criteria.get('categories', []))
    print(f"Total Criteria: {total_criteria}")

    print("\nCategories:")
    for cat in criteria.get('categories', []):
        print(f"  - {cat['name']}: {len(cat.get('criteria', []))} criteria")


if __name__ == '__main__':
    main()
