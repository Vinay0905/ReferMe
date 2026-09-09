import ipaddress
import logging
import socket
from typing import Iterable, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Default domains trusted for downloading syllabus and question paper PDFs
TRUSTED_PDF_HOST_SUFFIXES = (
    "amazonaws.com",
    "allen-live.in",
    "allen.in",
    "cloudfront.net",
)


def is_ip_private_or_loopback(ip_str: str) -> bool:
    """Checks if an IP string is a private, loopback, link-local, or reserved address."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        )
    except ValueError:
        return True  # If not a parseable IP, fail safe


def validate_safe_url(
    url: str,
    allowed_suffixes: Iterable[str] = TRUSTED_PDF_HOST_SUFFIXES,
    require_https: bool = True,
    check_dns: bool = True,
) -> bool:
    """
    Validates a URL before fetching to defend against SSRF.
    Enforces:
    1. Scheme must be https (if require_https is True).
    2. Hostname must match one of the allowed host suffixes.
    3. Hostname must not resolve to any private, loopback, or link-local IP (e.g. AWS IMDS 169.254.169.254).
    """
    if not url or not isinstance(url, str):
        return False

    try:
        parsed = urlparse(url.strip())
    except Exception:
        return False

    if require_https and parsed.scheme.lower() != "https":
        logger.warning(f"Rejected unsafe URL scheme: {parsed.scheme}")
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    hostname_lower = hostname.lower()

    # Reject direct IP hostnames in URLs
    try:
        ipaddress.ip_address(hostname_lower)
        logger.warning(f"Rejected URL with direct IP address host: {hostname_lower}")
        return False
    except ValueError:
        pass

    # Check hostname matches allowed suffixes
    domain_match = any(
        hostname_lower == suffix or hostname_lower.endswith("." + suffix)
        for suffix in allowed_suffixes
    )
    if not domain_match:
        logger.warning(f"Rejected URL host not in trusted domains: {hostname_lower}")
        return False

    # Resolve DNS to check if it points to internal/private IPs (DNS rebinding / SSRF)
    if check_dns:
        try:
            resolved_ips = socket.getaddrinfo(hostname, None)
            for item in resolved_ips:
                ip_str = item[4][0]
                if is_ip_private_or_loopback(ip_str):
                    logger.warning(f"Rejected URL host {hostname} resolving to private IP {ip_str}")
                    return False
        except socket.gaierror as e:
            logger.warning(f"Failed to resolve DNS for host {hostname}: {e}")
            return False
        except Exception as e:
            logger.warning(f"Error validating host IP addresses: {e}")
            return False

    return True


def sanitize_url_for_logging(url: Optional[str]) -> str:
    """Strips query parameters and fragments from a URL to avoid leaking presigned tokens/credentials in logs."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    except Exception:
        return "<invalid_url>"
