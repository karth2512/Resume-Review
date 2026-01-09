#!/usr/bin/env python3
"""
Parse TXT resume files into markdown format.
Adds basic markdown formatting to plain text resumes.
"""

import sys
import os
import re
from pathlib import Path


def parse_txt_to_markdown(txt_path: str, output_path: str) -> bool:
    """
    Parse a TXT resume file and convert it to markdown.

    Args:
        txt_path: Path to the input TXT file
        output_path: Path where the markdown file should be saved

    Returns:
        True if successful, False otherwise
    """
    try:
        # Read text file
        with open(txt_path, 'r', encoding='utf-8') as txt_file:
            content = txt_file.read()

        lines = content.split('\n')
        markdown_lines = []

        for line in lines:
            stripped = line.strip()

            if not stripped:
                markdown_lines.append('')
                continue

            # Detect potential section headers
            # All caps lines or lines followed by underlines/equals
            if stripped.isupper() and len(stripped) < 50:
                markdown_lines.append(f"## {stripped}")
            # Detect lines that look like headers (title case, short, no punctuation at end)
            elif (len(stripped) < 50 and
                  stripped[0].isupper() and
                  not stripped.endswith(('.', ',', ';')) and
                  sum(1 for c in stripped if c.isupper()) > len(stripped) * 0.3):
                markdown_lines.append(f"## {stripped}")
            # Detect bullet points
            elif re.match(r'^[\-\*\•\◦]\s+', stripped):
                markdown_lines.append(stripped)
            # Detect numbered lists
            elif re.match(r'^\d+[\.\)]\s+', stripped):
                markdown_lines.append(stripped)
            # Detect email addresses (potential contact info)
            elif re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', stripped):
                markdown_lines.append(stripped)
            # Detect phone numbers (potential contact info)
            elif re.search(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', stripped):
                markdown_lines.append(stripped)
            # Detect URLs
            elif re.search(r'https?://[^\s]+', stripped):
                markdown_lines.append(stripped)
            else:
                markdown_lines.append(line.rstrip())

        markdown_content = '\n'.join(markdown_lines)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)

        # Write markdown file
        with open(output_path, 'w', encoding='utf-8') as md_file:
            md_file.write(markdown_content)

        print(f"Successfully parsed TXT to: {output_path}")
        return True

    except FileNotFoundError:
        print(f"Error: TXT file not found: {txt_path}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error parsing TXT: {str(e)}", file=sys.stderr)
        return False


def main():
    if len(sys.argv) < 3:
        print("Usage: python parse_txt.py <input_txt_path> <output_md_path>")
        sys.exit(1)

    txt_path = sys.argv[1]
    output_path = sys.argv[2]

    success = parse_txt_to_markdown(txt_path, output_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
