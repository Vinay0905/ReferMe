import pytest
from pathlib import Path
from app.config import get_settings
from app.core.security import (
    is_ip_private_or_loopback,
    sanitize_url_for_logging,
    validate_safe_url,
)
from app.processing.extractor import PDFTextExtractor
from app.storage.local import LocalArtifactStorage


def test_cors_config_no_wildcard():
    settings = get_settings()
    assert "*" not in settings.CORS_ORIGINS
    assert "http://localhost:3000" in settings.CORS_ORIGINS


def test_is_ip_private_or_loopback():
    assert is_ip_private_or_loopback("127.0.0.1") is True
    assert is_ip_private_or_loopback("10.0.0.5") is True
    assert is_ip_private_or_loopback("192.168.1.100") is True
    assert is_ip_private_or_loopback("169.254.169.254") is True
    assert is_ip_private_or_loopback("::1") is True
    assert is_ip_private_or_loopback("8.8.8.8") is False


def test_validate_safe_url():
    # Valid domains with live DNS resolution
    assert validate_safe_url("https://s3.ap-south-1.amazonaws.com/allen-tests/test.pdf") is True
    assert validate_safe_url("https://api.allen-live.in/files/doc.pdf") is True

    # Valid domain pattern check (offline / without DNS dependency)
    assert validate_safe_url("https://d1234.cloudfront.net/paper.pdf", check_dns=False) is True

    # Scheme restrictions (must be https)
    assert validate_safe_url("http://s3.amazonaws.com/test.pdf") is False
    assert validate_safe_url("file:///etc/passwd") is False
    assert validate_safe_url("ftp://s3.amazonaws.com/test.pdf") is False

    # Untrusted external domains
    assert validate_safe_url("https://evil-site.com/payload.pdf") is False
    assert validate_safe_url("https://google.com/test.pdf") is False

    # Direct IP addresses (SSRF targets)
    assert validate_safe_url("https://169.254.169.254/latest/meta-data") is False
    assert validate_safe_url("https://127.0.0.1/admin") is False
    assert validate_safe_url("https://10.0.0.1/secret") is False

    # Empty / malformed
    assert validate_safe_url("") is False
    assert validate_safe_url("not-a-url") is False


def test_sanitize_url_for_logging():
    raw_url = "https://s3.amazonaws.com/bucket/test.pdf?AWSAccessKeyId=AKIAIOSFODNN7EXAMPLE&Signature=SECRET123"
    sanitized = sanitize_url_for_logging(raw_url)
    assert "SECRET123" not in sanitized
    assert "AWSAccessKeyId" not in sanitized
    assert sanitized == "https://s3.amazonaws.com/bucket/test.pdf"


def test_pdf_size_and_content_validation():
    # Below minimum
    assert PDFTextExtractor.validate_pdf_bytes(b"short") is False

    # Valid dummy PDF
    valid_pdf = b"%PDF-1.4 " + b"x" * 200 + b"%%EOF"
    assert PDFTextExtractor.validate_pdf_bytes(valid_pdf) is True

    # HTML error page
    html_page = b"<!DOCTYPE html><html><body>Error 404</body></html>" + b" " * 100
    assert PDFTextExtractor.validate_pdf_bytes(html_page) is False

    # Exceeding MAX_PDF_BYTES
    huge_pdf = b"%PDF-1.4 " + b"x" * (PDFTextExtractor.MAX_PDF_BYTES + 10)
    assert PDFTextExtractor.validate_pdf_bytes(huge_pdf) is False


@pytest.mark.asyncio
async def test_local_storage_path_traversal_protection(tmp_path: Path):
    storage = LocalArtifactStorage(base_dir=tmp_path)

    # Valid save and get
    saved_path = await storage.save("tests/test1.pdf", b"test pdf content")
    assert await storage.exists(saved_path) is True
    content = await storage.get(saved_path)
    assert content == b"test pdf content"

    # Directory traversal in save
    with pytest.raises(ValueError, match="Path traversal detected"):
        await storage.save("../../etc/evil.pdf", b"evil")

    # Directory traversal in get / exists
    assert await storage.get("/etc/passwd") is None
    assert await storage.exists("/etc/passwd") is False
    assert await storage.get("../../etc/passwd") is None
