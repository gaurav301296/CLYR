import pytest
from app.utils.parser import extract_pdf_text

def test_extract_pdf_text_invalid_path():
    with pytest.raises(FileNotFoundError):
        extract_pdf_text("nonexistent_file.pdf")
