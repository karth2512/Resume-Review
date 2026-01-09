---
name: resume-parser
description: Parse resume files in multiple formats (PDF, DOCX, TXT) into markdown format. Use when the user requests to parse resumes, convert resumes to markdown, extract resume content, or mentions commands like 'parse resume', 'convert resume to markdown', or similar resume parsing tasks. The skill preserves original formatting and saves output to a user-specified folder.
---

# Resume Parser

Parse resume files from various formats (PDF, DOCX, TXT) into clean markdown format while preserving the original structure and formatting.

## Quick Start

When a user requests resume parsing, follow this workflow:

1. Identify the resume file(s) to parse
2. Ask the user for the output folder path if not specified
3. Determine the file format (PDF, DOCX, or TXT)
4. Run the appropriate parsing script
5. Confirm successful parsing

## Parsing Scripts

Three specialized scripts handle different resume formats:

### PDF Resumes

Use `scripts/parse_pdf.py` for PDF files:

```bash
python scripts/parse_pdf.py <input_pdf_path> <output_md_path>
```

**Requirements**: pdfplumber (`pip install pdfplumber`)

**Features**:
- **Two-column layout detection**: Automatically detects and handles two-column resume formats
- **Column-aware parsing**: Extracts left column first, then right column, stacking content properly
- Extracts text from all pages with layout preservation
- Advanced header detection using multiple heuristics
- Recognizes common resume section headers
- Detects headers by capitalization, title case, and contextual clues
- Maintains bullet points with extended character support
- Combines multi-page content
- Cleaner output with whitespace normalization

### DOCX Resumes

Use `scripts/parse_docx.py` for Word documents:

```bash
python scripts/parse_docx.py <input_docx_path> <output_md_path>
```

**Requirements**: python-docx (`pip install python-docx`)

**Features**:
- Preserves heading styles
- Maintains bold and italic formatting
- Detects and converts list items
- Handles inline formatting (bold, italic)
- Respects document structure

### TXT Resumes

Use `scripts/parse_txt.py` for plain text files:

```bash
python scripts/parse_txt.py <input_txt_path> <output_md_path>
```

**Requirements**: None (standard library only)

**Features**:
- Detects section headers (all caps, title case)
- Preserves bullet points and numbered lists
- Identifies contact information (email, phone)
- Maintains URL formatting
- Adds markdown structure to plain text

## Workflow Example

User: "Parse this resume and save it to the parsed_resumes folder"

1. Identify the resume file path
2. Check if output folder exists, create if needed
3. Determine file extension (.pdf, .docx, or .txt)
4. Generate output filename: `{original_name}.md`
5. Run appropriate script:
   - PDF: `python scripts/parse_pdf.py resume.pdf parsed_resumes/resume.md`
   - DOCX: `python scripts/parse_docx.py resume.docx parsed_resumes/resume.md`
   - TXT: `python scripts/parse_txt.py resume.txt parsed_resumes/resume.md`
6. Confirm: "Successfully parsed resume.pdf to parsed_resumes/resume.md"

## Batch Processing

For multiple resume files:

1. Ask user for the source folder containing resumes
2. Ask user for the output folder
3. Use Glob to find all resume files (*.pdf, *.docx, *.txt)
4. Process each file with the appropriate script
5. Report summary of parsed files

Example:

```bash
# Find all resumes
find resumes/ -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.txt" \)

# Parse each one with appropriate script
for file in *.pdf; do
    python scripts/parse_pdf.py "$file" "output/${file%.pdf}.md"
done
```

## Error Handling

If a script fails:

1. Check that required dependencies are installed
2. Verify the input file exists and is readable
3. Ensure output directory exists or can be created
4. Check file permissions
5. Report specific error to user with suggested fix

Common errors:

- **Missing dependency**: Prompt user to install (e.g., `pip install pdfplumber`)
- **File not found**: Verify file path and ask user to correct
- **Permission error**: Check file permissions or output folder access
- **Encoding issues**: Scripts use UTF-8; for other encodings, may need adjustment

## Output Format

All parsed resumes are saved as markdown (.md) files with:

- Preserved section headers (##)
- Maintained bullet points and lists
- Inline formatting (bold, italic) where detected
- Contact information preserved
- Clean, readable structure

The output preserves the original resume's visual hierarchy and organization while converting to markdown format for easy reading and further processing.
