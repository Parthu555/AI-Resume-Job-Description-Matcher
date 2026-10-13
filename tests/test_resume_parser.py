import io
import zipfile
import pytest
from pypdf import PdfWriter
from backend.services.resume_parser import ResumeParser, ResumeParsingError


def create_synthetic_pdf(text: str) -> bytes:
    """Creates in-memory synthetic PDF with extractable text."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    for line in text.split("\n"):
        c.drawString(50, y, line)
        y -= 20
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def create_blank_pdf() -> bytes:
    """Creates a PDF with blank pages (no extractable text)."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def create_synthetic_docx(paragraphs: list[str]) -> bytes:
    """Creates a valid in-memory DOCX file containing paragraphs."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        # Minimal [Content_Types].xml
        content_types = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
            '  <Default Extension="xml" ContentType="application/xml"/>\n'
            '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
            '  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>\n'
            '</Types>'
        )
        z.writestr("[Content_Types].xml", content_types)
        
        # Minimal document.xml
        p_xml = "".join([f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs])
        doc_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
            f"  <w:body>{p_xml}</w:body>\n"
            "</w:document>"
        )
        z.writestr("word/document.xml", doc_xml)
    buffer.seek(0)
    return buffer.getvalue()


class TestResumeParser:
    def setup_method(self):
        self.parser = ResumeParser(max_size_mb=5, min_chars=30)

    def test_valid_pdf_extraction(self):
        sample_text = (
            "Jane Doe\n"
            "Summary: Senior Software Engineer with 5 years experience in Python and FastAPI.\n"
            "Technical Skills: Python, Docker, PostgreSQL, PyTorch.\n"
            "Experience: Built cloud microservices and scalable APIs."
        )
        pdf_bytes = create_synthetic_pdf(sample_text)
        extracted, sections = self.parser.parse_file("resume.pdf", pdf_bytes)
        
        assert "Jane Doe" in extracted
        assert "FastAPI" in extracted
        assert "Skills" in sections
        assert "Experience" in sections

    def test_valid_docx_extraction(self):
        paragraphs = [
            "John Smith",
            "Professional Summary: Machine Learning Engineer specializing in NLP and LLMs.",
            "Education: Bachelor of Science in Computer Science.",
            "Skills: Python, Scikit-Learn, PyTorch, AWS, Git.",
            "Work Experience: Developed recommendation algorithms and data pipelines."
        ]
        docx_bytes = create_synthetic_docx(paragraphs)
        extracted, sections = self.parser.parse_file("resume.docx", docx_bytes)
        
        assert "John Smith" in extracted
        assert "NLP and LLMs" in extracted
        assert "Education" in sections
        assert "Skills" in sections

    def test_empty_file_rejected(self):
        with pytest.raises(ResumeParsingError) as exc_info:
            self.parser.parse_file("empty.pdf", b"")
        assert "empty" in str(exc_info.value).lower()

    def test_unsupported_file_extension(self):
        with pytest.raises(ResumeParsingError) as exc_info:
            self.parser.parse_file("resume.txt", b"Some random text")
        assert "unsupported" in str(exc_info.value).lower()

    def test_oversized_file_rejected(self):
        tiny_parser = ResumeParser(max_size_mb=1)  # 1 MB limit
        huge_bytes = b"0" * (2 * 1024 * 1024)  # 2 MB
        with pytest.raises(ResumeParsingError) as exc_info:
            tiny_parser.parse_file("large.pdf", huge_bytes)
        assert "exceeds" in str(exc_info.value).lower()

    def test_corrupt_docx_rejected(self):
        corrupt_bytes = b"Not a valid zip content for docx file"
        with pytest.raises(ResumeParsingError):
            self.parser.parse_file("corrupt.docx", corrupt_bytes)

    def test_blank_pdf_scanned_notice(self):
        blank_pdf = create_blank_pdf()
        with pytest.raises(ResumeParsingError) as exc_info:
            self.parser.parse_file("blank.pdf", blank_pdf)
        assert "ocr" in str(exc_info.value).lower()

    def test_whitespace_normalization(self):
        raw = "Line 1   with    spaces.\n\n\n\nLine 2 \u00a0with nonbreaking."
        cleaned = self.parser.normalize_text(raw)
        assert "    " not in cleaned
        assert "\u00a0" not in cleaned
        assert "\n\n\n" not in cleaned
