import os
import pdfplumber

def extract_pdf_text(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as page_err:
                    # Skip pages that fail to extract (corrupt, image-only, etc.)
                    print(f"Warning: Failed to extract text from a page: {page_err}")
                    continue
    except Exception as e:
        raise ValueError(f"Failed to open or parse PDF: {str(e)}")

    if not text.strip():
        raise ValueError("No text could be extracted from the PDF. The file may be image-based/scanned.")

    return text
