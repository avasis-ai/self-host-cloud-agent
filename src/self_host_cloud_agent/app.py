"""Core application logic for self-host-cloud-agent."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from docker.models.containers import Container
from docker.models.networks import Network

from self_host_cloud_agent.docker_manager import DockerManager
from self_host_cloud_agent.reverse_proxy import ReverseProxyManager
from self_host_cloud_agent.ssl_manager import SSLManager


logger = logging.getLogger(__name__)


@dataclass
class DeploymentResult:
    """Result of a deployment operation."""

    service_name: str
    success: bool
    container_id: str | None
    status: str
    message: str
    network_name: str | None = None


class ServerManager:
    """Main server management class for homelab deployments."""

    def __init__(self, base_path: Path | None = None):
        """Initialize the server manager.

        Args:
            base_path: Base path for deployments (default: /var/lib/self-host-cloud-agent)
        """
        self.base_path = Path(base_path or "/var/lib/self-host-cloud-agent")
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.docker = DockerManager()
        self.reverse_proxy = ReverseProxyManager()
        self.ssl_manager = SSLManager()

    def deploy_service(
        self,
        service_name: str,
        image: str,
        ports: dict[str, int] | None = None,
        volumes: dict[str, dict[str, str]] | None = None,
        environment: dict[str, str] | None = None,
        reverse_proxy_host: str | None = None,
        ssl_enabled: bool = True
    ) -> DeploymentResult:
        """Deploy a Docker service.

        Args:
            service_name: Name of the service
            image: Docker image to deploy
            ports: Port mappings {container_port: host_port}
            volumes: Volume mappings {volume_name: {"bind": container_path, "mode": "rw"}}
            environment: Environment variables
            reverse_proxy_host: Hostname for reverse proxy routing
            ssl_enabled: Whether to enable SSL for this service

        Returns:
            DeploymentResult with deployment status
        """
        try:
            logger.info(f"Deploying service: {service_name}")

            # Create network if needed
            network_name = f"{service_name}_network"
            self._ensure_network(network_name)

            # Configure deployment parameters
            deploy_config = self._build_deployment_config(
                image, ports, volumes, environment
            )

            # Create container
            container = self.docker.create_container(
                network_name=network_name,
                **deploy_config
            )
            container.start()

            logger.info(f"Container {container.id} started for {service_name}")

            # Configure reverse proxy if specified
            if reverse_proxy_host:
                port_to_use = list(ports.values())[0] if ports else 80
                self.reverse_proxy.configure_upstream(
                    service_name=service_name,
                    host=reverse_proxy_host,
                    container_port=port_to_use
                )

                # Provision SSL if enabled
                if ssl_enabled:
                    cert_path = self.ssl_manager.provision_certificate(
                        domain=reverse_proxy_host
                    )
                    logger.info(f"SSL certificate provisioned for {reverse_proxy_host}")

            return DeploymentResult(
                service_name=service_name,
                success=True,
                container_id=container.id,
                status=container.status,
                message="Service deployed successfully",
                network_name=network_name
            )

        except Exception as e:
            logger.error(f"Deployment failed for {service_name}: {e}")
            return DeploymentResult(
                service_name=service_name,
                success=False,
                container_id=None,
                status="failed",
                message=str(e)
            )

    def _ensure_network(self, network_name: str) -> Network:
        """Ensure a network exists for the service.

        Args:
            network_name: Name of the network

        Returns:
            Network object
        """
        existing_network = self.docker.get_network(network_name)

        if existing_network:
            return existing_network

        return self.docker.create_network(network_name)

    def _build_deployment_config(
        self,
        image: str,
        ports: dict[str, int] | None,
        volumes: dict[str, dict[str, str]] | None,
        environment: dict[str, str] | None
    ) -> dict[str, Any]:
        """Build deployment configuration.

        Args:
            image: Docker image
            ports: Port mappings
            volumes: Volume mappings
            environment: Environment variables

        Returns:
            Deployment configuration dictionary
        """
        config = {
            "image": image,
            "network": None  # Will be set by create_container
        }

        if ports:
            config["ports"] = ports

        if volumes:
            config["volumes"] = volumes

        if environment:
            config["environment"] = environment

        return config

    def stop_service(self, service_name: str) -> DeploymentResult:
        """Stop a deployed service.

        Args:
            service_name: Name of the service to stop

        Returns:
            DeploymentResult with stop status
        """
        try:
            logger.info(f"Stopping service: {service_name}")

            containers = self.docker.list_containers(filters={"label": f"service={service_name}"})

            for container in containers:
                container.stop()
                logger.info(f"Stopped container {container.id}")

            return DeploymentResult(
                service_name=service_name,
                success=True,
                container_id=None,
                status="stopped",
                message="Service stopped successfully"
            )

        except Exception as e:
            logger.error(f"Failed to stop {service_name}: {e}")
            return DeploymentResult(
                service_name=service_name,
                success=False,
                container_id=None,
                status="failed",
                message=str(e)
            )

    def remove_service(self, service_name: str) -> DeploymentResult:
        """Remove a deployed service.

        Args:
            service_name: Name of the service to remove

        Returns:
            DeploymentResult with removal status
        """
        try:
            logger.info(f"Removing service: {service_name}")

            containers = self.docker.list_containers(filters={"label": f"service={service_name}"})

            for container in containers:
                container.remove(v=True)
                logger.info(f"Removed container {container.id}")

            # Remove network
            self.docker.remove_network(f"{service_name}_network")

            return DeploymentResult(
                service_name=service_name,
                success=True,
                container_id=None,
                status="removed",
                message="Service removed successfully"
            )

        except Exception as e:
            logger.error(f"Failed to remove {service_name}: {e}")
            return DeploymentResult(
                service_name=service_name,
                success=False,
                container_id=None,
                status="failed",
                message=str(e)
            )

    def list_services(self) -> list[dict[str, Any]]:
        """List all deployed services.

        Returns:
            List of service information dictionaries
        """
        services = []
        containers = self.docker.list_containers(filters={"label": "service="})

        for container in containers:
            service_name = container.labels.get("service", "unknown")
            services.append({
                "name": service_name,
                "container_id": container.id,
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else "unknown",
                "ports": container.ports,
                "created": container.attrs["Created"]
            })

        return services
