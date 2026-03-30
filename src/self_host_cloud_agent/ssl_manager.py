"""SSL certificate manager for self-host-cloud-agent."""

import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SSLManager:
    """Manage SSL/TLS certificates using Certbot."""

    CERTBOT_PATH = "/usr/bin/certbot"
    CERT_PATH = "/etc/letsencrypt/live"

    def __init__(self, certbot_path: str | None = None):
        """Initialize SSL manager.

        Args:
            certbot_path: Path to Certbot binary
        """
        self.certbot_path = Path(certbot_path or self.CERTBOT_PATH)

    def provision_certificate(self, domain: str) -> str:
        """Provision an SSL certificate for a domain.

        Args:
            domain: Domain name to provision certificate for

        Returns:
            Path to certificate files
        """
        cert_name = domain.split(".")[0]  # Use first part as certificate name
        cert_path = Path(self.CERT_PATH) / domain

        # Check if certificate already exists
        if cert_path.exists():
            logger.info(f"Certificate already exists for {domain}")
            return str(cert_path)

        try:
            # Run Certbot in webroot mode
            result = subprocess.run(
                [
                    str(self.certbot_path),
                    "certonly",
                    "--standalone",
                    "-d", domain,
                    "--non-interactive",
                    "--agree-tos",
                    "-m", "admin@example.com"
                ],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                logger.error(f"Certbot failed for {domain}: {result.stderr}")
                raise RuntimeError(f"Certbot failed: {result.stderr}")

            logger.info(f"Certificate provisioned for {domain}")
            return str(cert_path)

        except subprocess.TimeoutExpired:
            logger.error(f"Certificate provisioning timed out for {domain}")
            raise
        except FileNotFoundError:
            logger.error(f"Certbot not found at {self.certbot_path}")
            raise

    def renew_certificates(self) -> dict[str, Any]:
        """Renew all certificates.

        Returns:
            Dictionary with renewal results
        """
        try:
            result = subprocess.run(
                [
                    str(self.certbot_path),
                    "renew",
                    "--force-renewal"
                ],
                capture_output=True,
                text=True,
                timeout=300
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "errors": "Certificate renewal timed out"
            }

    def get_certificate_info(self, domain: str) -> dict[str, Any]:
        """Get information about a certificate.

        Args:
            domain: Domain to check

        Returns:
            Dictionary with certificate information
        """
        cert_path = Path(self.CERT_PATH) / domain / "fullchain.pem"

        if not cert_path.exists():
            return {
                "exists": False,
                "domain": domain
            }

        # Get certificate expiry date
        try:
            result = subprocess.run(
                ["openssl", "x509", "-in", str(cert_path), "-noout", "-enddate"],
                capture_output=True,
                text=True,
                timeout=30
            )

            expiry_date = result.stdout.strip().replace("notAfter=", "")

            return {
                "exists": True,
                "domain": domain,
                "expiry_date": expiry_date,
                "path": str(cert_path)
            }

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {
                "exists": True,
                "domain": domain,
                "expiry_date": "unknown",
                "path": str(cert_path)
            }
