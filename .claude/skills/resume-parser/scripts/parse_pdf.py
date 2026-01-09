#!/usr/bin/env python3
"""
Parse PDF resume files into markdown format.
Uses Anthropic's Claude model with vision capabilities to parse PDF pages as images.
"""

import sys
import os
import base64
from pathlib import Path
from io import BytesIO

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv not installed. Install with: pip install python-dotenv", file=sys.stderr)
    sys.exit(1)

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF not installed. Install with: pip install pymupdf", file=sys.stderr)
    sys.exit(1)

try:
    from anthropic import Anthropic
except ImportError:
    print("Error: anthropic not installed. Install with: pip install anthropic", file=sys.stderr)
    sys.exit(1)

# Load environment variables from .env file
# Look for .env in the project root (4 levels up from scripts folder: scripts -> resume-parser -> skills -> .claude -> root)
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)


def image_to_base64(image) -> str:
    """
    Convert a PIL Image to base64 string.

    Args:
        image: PIL Image object

    Returns:
        Base64 encoded string of the image
    """
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def parse_page_with_claude(client: Anthropic, image_base64: str, page_num: int, total_pages: int) -> str:
    """
    Use Claude's vision API to parse a resume page image into markdown.

    Args:
        client: Anthropic client instance
        image_base64: Base64 encoded image of the PDF page
        page_num: Current page number (1-indexed)
        total_pages: Total number of pages

    Returns:
        Markdown formatted text extracted from the page
    """
    page_context = f"page {page_num} of {total_pages}" if total_pages > 1 else "single page resume"

    prompt = f"""You are parsing a resume ({page_context}). Please extract all the text content from this resume page and convert it to clean, well-structured markdown format.

Instructions:
1. Preserve the exact text content - do not summarize or paraphrase
2. Identify section headers (like "Experience", "Education", "Skills", etc.) and format them as ## headers
3. Maintain bullet points using - for list items
4. Preserve all dates, job titles, company names, and details exactly as written
5. Handle multi-column layouts by reading left-to-right, top-to-bottom naturally
6. Keep contact information, links, and email addresses
7. Maintain the hierarchical structure (sections, subsections, bullet points)
8. Do not add any commentary, explanations, or content that isn't in the original resume
9. If there are tables, convert them to markdown table format
10. Remove any template artifacts, watermarks, or non-content elements

Output only the markdown formatted resume content, nothing else."""

    try:
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_base64,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }
            ],
        )

        return message.content[0].text

    except Exception as e:
        print(f"Error calling Claude API for page {page_num}: {str(e)}", file=sys.stderr)
        raise


def parse_pdf_to_markdown(pdf_path: str, output_path: str, api_key: str = None) -> bool:
    """
    Parse a PDF resume file and convert it to markdown using Claude's vision API.
    Converts each PDF page to an image and uses Claude to extract structured content.

    Args:
        pdf_path: Path to the input PDF file
        output_path: Path where the markdown file should be saved
        api_key: Anthropic API key (if not provided, uses ANTHROPIC_API_KEY env var)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize Anthropic client
        if not api_key:
            # Get API key from environment variable
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                print("Error: ANTHROPIC_API_KEY not found in environment or .env file", file=sys.stderr)
                return False

        client = Anthropic(api_key=api_key)

        print(f"Converting PDF to images: {pdf_path}")
        # Open PDF with PyMuPDF
        pdf_document = fitz.open(pdf_path)
        total_pages = len(pdf_document)

        print(f"Processing {total_pages} page(s) with Claude vision API...")

        # Process each page with Claude
        page_contents = []
        for page_num in range(total_pages):
            print(f"  Processing page {page_num + 1}/{total_pages}...")

            # Get the page
            page = pdf_document[page_num]

            # Render page to image (300 DPI for good quality)
            # The matrix scales the page - 300/72 = ~4.17x for 300 DPI
            mat = fitz.Matrix(300/72, 300/72)
            pix = page.get_pixmap(matrix=mat)

            # Convert pixmap to PIL Image
            img_data = pix.tobytes("png")
            image_base64 = base64.b64encode(img_data).decode('utf-8')

            # Parse with Claude
            markdown_content = parse_page_with_claude(client, image_base64, page_num + 1, total_pages)

            page_contents.append(markdown_content)

        # Close the PDF document
        pdf_document.close()

        # Combine all pages
        # Add page separators for multi-page resumes
        if total_pages > 1:
            full_markdown = '\n\n---\n\n'.join(page_contents)
        else:
            full_markdown = page_contents[0]

        # Clean up excessive whitespace
        full_markdown = full_markdown.strip()

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Write markdown file
        with open(output_path, 'w', encoding='utf-8') as md_file:
            md_file.write(full_markdown)

        print(f"Successfully parsed PDF to: {output_path}")
        return True

    except FileNotFoundError:
        print(f"Error: PDF file not found: {pdf_path}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error parsing PDF: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


def main():
    if len(sys.argv) < 3:
        print("Usage: python parse_pdf.py <input_pdf_path> <output_md_path> [api_key]")
        print("\nNote: If api_key is not provided, ANTHROPIC_API_KEY environment variable will be used")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_path = sys.argv[2]
    api_key = sys.argv[3] if len(sys.argv) > 3 else None

    success = parse_pdf_to_markdown(pdf_path, output_path, api_key)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
