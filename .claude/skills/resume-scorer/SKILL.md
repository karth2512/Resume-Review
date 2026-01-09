---
name: resume-scorer
description: Analyze and score multiple resumes against job descriptions to identify the best candidates. Use when the user needs to evaluate, compare, rank, or score candidates from resume files (.md format) against job requirements. Provides skills matching analysis, experience evaluation, detailed scoring (overall, skills, experience), ranked candidate lists, and comprehensive reports in both markdown and CSV/Excel formats.
---

# Resume Scorer

Systematically analyze and rank resume candidates against job requirements using LLM-powered evaluation with structured outputs and detailed reasoning.

## What This Skill Does

- **Intelligently extracts** evaluation criteria from job descriptions using Claude
- **Systematically evaluates** each resume against specific criteria with binary scoring and reasoning
- **Generates comprehensive reports** with rankings, detailed analysis, and exportable Excel data
- **Provides citation-backed scoring** where every evaluation includes specific evidence from the resume
- **Creates filterable Excel sheets** for easy candidate comparison and decision-making

## Key Features

1. **LLM-Powered Criteria Extraction**: Claude analyzes the job description and structures all evaluation criteria into categories (Required Skills, Experience, Education, etc.)
2. **Binary Scoring with Reasoning**: Each criterion gets a 0 or 1 score with 1-2 sentence justification citing resume content
3. **Weighted Scoring**: Criteria are weighted (Critical/High/Medium/Low) to calculate meaningful overall scores
4. **Multi-Sheet Excel Reports**: Comprehensive workbooks with rankings, category scores, criteria matrix, detailed evaluations, and criteria reference
5. **Markdown Reports**: Human-readable detailed analysis with strengths, gaps, and complete candidate profiles

## Prerequisites

### Installation

Install required Python packages:

```bash
pip install anthropic pandas openpyxl
```

Or use the requirements file:

```bash
pip install -r requirements.txt
```

### API Key Setup

This skill requires an Anthropic API key. Set it up using one of these methods:

**Method 1: .env File (Recommended)**

Create a `.env` file in your project root directory:

```bash
# .env file
ANTHROPIC_API_KEY=your-api-key-here
```

The scripts will automatically load the API key from the `.env` file using `python-dotenv`.

**Method 2: Environment Variable**
```bash
# Linux/Mac
export ANTHROPIC_API_KEY='your-api-key-here'

# Windows PowerShell
$env:ANTHROPIC_API_KEY='your-api-key-here'

# Windows CMD
set ANTHROPIC_API_KEY=your-api-key-here
```

**Method 3: Pass as Argument**
```bash
python scripts/analyze_resumes.py --api-key your-api-key-here ...
```

## Quick Start

**Basic usage:**
```bash
python scripts/analyze_resumes.py \
  --resumes-dir /path/to/parsed_resumes \
  --job-desc /path/to/job_description.txt
```

**With custom output directory:**
```bash
python scripts/analyze_resumes.py \
  --resumes-dir ./parsed_resumes \
  --job-desc ./senior_dev_job.txt \
  --output-dir ./hiring_round_1
```

## Complete Workflow

### Step 1: Prepare Inputs

**Locate Resume Files**
- Resumes must be in markdown (.md) format
- Common locations: `./parsed_resumes/`, user-specified directory
- Use the `resume-parser` skill if resumes are in PDF/DOCX format

**Obtain Job Description**
- Job description should be in a text or markdown file
- If user provides text directly, create a temporary file:
  ```bash
  # Create temp file from user input
  echo "User's job description text..." > /tmp/job_description.txt
  ```

**Verify inputs exist:**
```bash
ls /path/to/resumes/*.md
cat /path/to/job_description.txt
```

### Step 2: Run Complete Analysis

Execute the main orchestration script:

```bash
python scripts/analyze_resumes.py \
  --resumes-dir ./parsed_resumes \
  --job-desc ./job_description.txt \
  --output-dir ./resume_analysis_output
```

**What happens internally:**

1. **Criteria Extraction** (`extract_criteria.py`)
   - Claude analyzes the job description
   - Extracts and categorizes all evaluation criteria
   - Assigns weights (Critical/High/Medium/Low)
   - Generates evaluation guides for each criterion
   - Saves as JSON and markdown in `./output/criteria/`

2. **Resume Evaluation** (`evaluate_resumes.py`)
   - For each resume, Claude evaluates against all criteria
   - Returns binary scores (0 or 1) with reasoning
   - Calculates weighted overall scores
   - Generates comprehensive Excel and markdown reports

### Step 3: Review Results

The analysis generates multiple output files:

**Criteria Files** (`output_dir/criteria/`)
- `evaluation_criteria.json` - Structured criteria data
- `evaluation_criteria.md` - Human-readable criteria reference

**Analysis Reports** (`output_dir/`)
- `resume_evaluation_TIMESTAMP.xlsx` - Multi-sheet Excel workbook
- `resume_evaluation_TIMESTAMP.md` - Detailed markdown report
- `resume_evaluation_TIMESTAMP.json` - Raw evaluation data

### Step 4: Present to User

Provide a clear summary:

```
Analysis complete! Evaluated 15 candidates against 32 criteria.

Top 3 Candidates:
1. Jane Smith - 87.5/100 (28/32 criteria met)
2. John Doe - 82.3/100 (26/32 criteria met)
3. Alice Johnson - 78.9/100 (25/32 criteria met)

Reports saved to: ./resume_analysis_output/

Main Excel Report: resume_evaluation_20240115_143022.xlsx
- Sheet 1: Rankings (sortable summary)
- Sheet 2: Category Scores (skills, experience, education breakdown)
- Sheet 3: Criteria Matrix (binary grid for filtering)
- Sheet 4: Detailed Evaluations (full reasoning for every criterion)
- Sheet 5: Criteria Reference (evaluation guide)

Markdown Report: resume_evaluation_20240115_143022.md
```

Link to the Excel file for easy access: `[Open Excel Report](./resume_analysis_output/resume_evaluation_20240115_143022.xlsx)`

## Excel Report Structure

### Sheet 1: Rankings
Sortable summary table with:
- Rank, Candidate Name, Overall Score
- Criteria Met (e.g., "28/32")
- Match Percentage
- Executive Summary

**Use for:** Quick identification of top candidates

### Sheet 2: Category Scores
Breakdown by evaluation categories:
- Candidate name
- Score and met/total for each category (Required Skills, Experience, Education, etc.)

**Use for:** Understanding strength areas by category

### Sheet 3: Criteria Matrix
Binary matrix (candidates × criteria):
- Rows: Candidates
- Columns: Each specific criterion
- Values: 1 (met) or 0 (not met)

**Use for:** Filtering candidates by specific requirements (e.g., "Show me all candidates with Python AND AWS experience")

### Sheet 4: Detailed Evaluations
Complete evaluation dataset:
- Candidate, Category, Criterion, Weight, Score, Reasoning

**Use for:** Understanding why each score was given, with resume citations

### Sheet 5: Criteria Reference
Original evaluation criteria:
- Category, Criterion, Weight, Evaluation Guide

**Use for:** Understanding how each criterion should be assessed

## Advanced Usage

### Individual Script Usage

**Run criteria extraction only:**
```bash
python scripts/extract_criteria.py \
  --job-desc ./job_description.txt \
  --output-dir ./criteria_only
```

**Run evaluation with pre-extracted criteria:**
```bash
python scripts/evaluate_resumes.py \
  --resumes-dir ./parsed_resumes \
  --criteria-json ./criteria/evaluation_criteria.json \
  --output-dir ./evaluation_results
```

### Iterative Refinement

Users can refine job descriptions and re-run analysis:

```bash
# Initial analysis
python scripts/analyze_resumes.py --resumes-dir ./resumes --job-desc ./jd_v1.txt

# Review criteria, update job description, re-analyze
python scripts/analyze_resumes.py --resumes-dir ./resumes --job-desc ./jd_v2_refined.txt
```

### Comparing Different Job Descriptions

Evaluate the same resumes against multiple positions:

```bash
python scripts/analyze_resumes.py \
  --resumes-dir ./resumes \
  --job-desc ./senior_backend_engineer.txt \
  --output-dir ./analysis_senior_backend

python scripts/analyze_resumes.py \
  --resumes-dir ./resumes \
  --job-desc ./frontend_lead.txt \
  --output-dir ./analysis_frontend_lead
```

## Scoring Methodology

### Overall Score Calculation

Overall Score = Weighted Average of All Criteria

Weight values:
- **Critical**: 4.0
- **High**: 3.0
- **Medium**: 2.0
- **Low**: 1.0

Formula:
```
Overall Score = (Σ(criterion_score × weight) / Σ(weight)) × 100
```

### Binary Scoring Rules

- **1 (Met)**: Clear evidence in resume that criterion is satisfied
- **0 (Not Met)**: No evidence or insufficient evidence in resume

Every score includes reasoning with specific citations from the resume.

### Category Scores

Calculated per category (e.g., Required Skills, Experience) using the same weighted approach within that category.

## Common Issues and Solutions

### Issue: "ANTHROPIC_API_KEY not found"
**Solution:** Set the API key as environment variable or pass via `--api-key` argument

### Issue: "No markdown files found in directory"
**Solution:**
- Verify resumes are in .md format
- Check directory path is correct
- If resumes are PDF/DOCX, use the `resume-parser` skill first

### Issue: Low scores across all candidates
**Possible causes:**
- Job description may be too specific or use different terminology
- Review the extracted criteria in `criteria/evaluation_criteria.md`
- Consider if candidates use different terms for same concepts (e.g., "JS" vs "JavaScript")
- Refine job description and re-run

### Issue: LLM evaluation seems inconsistent
**Solution:**
- Review reasoning in "Detailed Evaluations" sheet
- Check if resume formatting affects parsing
- Ensure resumes have clear structure with headers

### Issue: Script fails during evaluation
**Possible causes:**
- API rate limiting (wait and retry)
- Network connectivity issues
- Malformed resume markdown
- Check error messages in console output

## Tips for Best Results

1. **Clear Job Descriptions**: Provide comprehensive, well-structured job descriptions with explicit requirements
2. **Consistent Resume Format**: Ensure all resumes follow similar markdown structure with clear section headers
3. **Specific Criteria**: More specific criteria lead to more actionable evaluations
4. **Review Extracted Criteria**: After Step 1, review the criteria markdown file and adjust job description if needed
5. **Use Excel Filtering**: Leverage Excel's filter and sort features to explore different candidate perspectives
6. **Cross-Reference**: Use "Detailed Evaluations" sheet to validate scores against actual resume content

## Example Interaction Flow

**User:** "I have 20 resumes in parsed_resumes/. Score them against this Senior Python Developer job description."

**Claude:**
1. Verifies resumes directory exists and contains .md files
2. Asks for job description location or text
3. Checks for ANTHROPIC_API_KEY
4. Runs the complete analysis workflow
5. Presents top 3 candidates with scores
6. Provides links to Excel and markdown reports
7. Offers to dive deeper into specific candidates or explain scoring

**Follow-up User:** "Why did candidate A score higher than candidate B on experience?"

**Claude:**
1. Opens the Excel "Detailed Evaluations" sheet
2. Filters for experience-related criteria
3. Compares scores and reasoning for both candidates
4. Explains the specific differences with citations from their resumes

## Next Steps After Analysis

Suggest to users:
- **Review Top Candidates**: Open Excel report and review top 5-10 candidates
- **Filter by Must-Haves**: Use Criteria Matrix sheet to filter for critical requirements
- **Read Detailed Reasoning**: Review "Detailed Evaluations" for insight into scores
- **Schedule Interviews**: Use rankings to prioritize interview scheduling
- **Track Feedback**: Add columns to Excel for interview notes and final decisions
- **Compare Finalists**: Create shortlist and deep-dive into detailed evaluations

## Architecture Notes

This skill uses a two-phase LLM approach:

**Phase 1: Criteria Extraction**
- Single LLM call to analyze job description
- Structured output with categories, weights, and evaluation guides
- Saves criteria for reusability and transparency

**Phase 2: Resume Evaluation**
- One LLM call per resume (parallelizable)
- Structured output with binary scores and reasoning
- Citations tied to specific resume content

This architecture ensures:
- **Consistency**: Same criteria applied to all candidates
- **Transparency**: Every score has explicit reasoning
- **Efficiency**: Criteria extracted once, reused for all resumes
- **Auditability**: Complete evaluation trail in Excel
