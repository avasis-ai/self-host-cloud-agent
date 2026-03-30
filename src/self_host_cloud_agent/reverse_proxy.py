"""Reverse proxy manager for self-host-cloud-agent."""

import logging
from pathlib import Path
from typing import Any

import yaml


logger = logging.getLogger(__name__)


class ReverseProxyManager:
    """Manage Traefik reverse proxy configuration."""

    def __init__(self, config_path: Path | None = None):
        """Initialize reverse proxy manager.

        Args:
            config_path: Path to Traefik configuration file
        """
        self.config_path = Path(config_path or "/etc/traefik/traefik.yml")
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize Traefik configuration
        self._ensure_config()

    def _ensure_config(self) -> None:
        """Ensure Traefik configuration file exists."""
        if not self.config_path.exists():
            config = {
                "entryPoints": {
                    "web": {
                        "address": ":80"
                    },
                    "websecure": {
                        "address": ":443"
                    }
                },
                "providers": {
                    "docker": {
                        "endpoint": "unix:///var/run/docker.sock",
                        "exposedByDefault": False
                    }
                }
            }

            with self.config_path.open("w") as f:
                yaml.dump(config, f)

            logger.info(f"Created Traefik config: {self.config_path}")

    def configure_upstream(
        self,
        service_name: str,
        host: str,
        container_port: int
    ) -> None:
        """Configure Traefik to route traffic to a service.

        Args:
            service_name: Name of the Docker service
            host: Hostname to route to
            container_port: Port inside the container
        """
        try:
            with self.config_path.open("r") as f:
                config = yaml.safe_load(f)

            # Add service to providers.docker.services
            if "providers" not in config:
                config["providers"] = {}

            if "docker" not in config["providers"]:
                config["providers"]["docker"] = {}

            if "services" not in config["providers"]["docker"]:
                config["providers"]["docker"]["services"] = {}

            config["providers"]["docker"]["services"][service_name] = {
                "http": {
                    "servers": [
                        {
                            "url": f"http://localhost:{container_port}",
                            "weight": 100
                        }
                    ],
                    "loadBalancer": {
                        "servers": [
                            {
                                "url": f"http://{service_name}:{container_port}"
                            }
                        ]
                    }
                },
                "entryPoints": ["websecure"],
                " routers": {
                    f"{service_name}-router": {
                        "rule": f"Host(`{host}`)",
                        "service": service_name,
                        "entryPoints": ["websecure"]
                    }
                }
            }

            # Write updated configuration
            with self.config_path.open("w") as f:
                yaml.dump(config, f)

            logger.info(f"Configured reverse proxy for {service_name} -> {host}")

        except Exception as e:
            logger.error(f"Failed to configure reverse proxy: {e}")
            raise

    def get_proxy_status(self) -> dict[str, Any]:
        """Get current reverse proxy status.

        Returns:
            Dictionary with proxy configuration status
        """
        try:
            with self.config_path.open("r") as f:
                config = yaml.safe_load(f)

            return {
                "config_exists": True,
                "entrypoints": list(config.get("entryPoints", {}).keys()),
                "services": len(config.get("providers", {}).get("docker", {}).get("services", {}))
            }

        except FileNotFoundError:
            return {
                "config_exists": False,
                "entrypoints": [],
                "services": 0
            }
