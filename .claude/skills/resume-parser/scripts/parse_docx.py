#!/usr/bin/env python3
"""
Parse DOCX resume files into markdown format.
Uses python-docx to extract text and formatting from Word documents.
"""

import sys
import os
from pathlib import Path

try:
    from docx import Document
except ImportError:
    print("Error: python-docx not installed. Install with: pip install python-docx", file=sys.stderr)
    sys.exit(1)


def parse_docx_to_markdown(docx_path: str, output_path: str) -> bool:
    """
    Parse a DOCX resume file and convert it to markdown.

    Args:
        docx_path: Path to the input DOCX file
        output_path: Path where the markdown file should be saved

    Returns:
        True if successful, False otherwise
    """
    try:
        # Load the document
        doc = Document(docx_path)

        markdown_lines = []

        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if not text:
                markdown_lines.append('')
                continue

            # Check for heading styles
            if paragraph.style.name.startswith('Heading'):
                level = paragraph.style.name.replace('Heading ', '')
                if level.isdigit():
                    markdown_lines.append(f"{'#' * int(level)} {text}")
                else:
                    markdown_lines.append(f"## {text}")
            # Check for bold text (potential headers)
            elif paragraph.runs and all(run.bold for run in paragraph.runs if run.text.strip()):
                markdown_lines.append(f"## {text}")
            # Check for bullet points/list items
            elif paragraph.style.name.startswith('List'):
                markdown_lines.append(f"- {text}")
            else:
                # Process inline formatting (bold, italic)
                formatted_text = ""
                for run in paragraph.runs:
                    run_text = run.text
                    if run.bold and run.italic:
                        formatted_text += f"***{run_text}***"
                    elif run.bold:
                        formatted_text += f"**{run_text}**"
                    elif run.italic:
                        formatted_text += f"*{run_text}*"
                    else:
                        formatted_text += run_text

                if formatted_text.strip():
                    markdown_lines.append(formatted_text)

        markdown_content = '\n'.join(markdown_lines)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)

        # Write markdown file
        with open(output_path, 'w', encoding='utf-8') as md_file:
            md_file.write(markdown_content)

        print(f"Successfully parsed DOCX to: {output_path}")
        return True

    except FileNotFoundError:
        print(f"Error: DOCX file not found: {docx_path}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error parsing DOCX: {str(e)}", file=sys.stderr)
        return False


def main():
    if len(sys.argv) < 3:
        print("Usage: python parse_docx.py <input_docx_path> <output_md_path>")
        sys.exit(1)

    docx_path = sys.argv[1]
    output_path = sys.argv[2]

    success = parse_docx_to_markdown(docx_path, output_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
