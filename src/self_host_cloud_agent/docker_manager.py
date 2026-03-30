"""Docker manager for self-host-cloud-agent."""

import logging
from pathlib import Path
from typing import Any

import docker
from docker.models.containers import Container
from docker.models.images import Image
from docker.models.networks import Network

logger = logging.getLogger(__name__)


class DockerManager:
    """Manage Docker operations for service deployments."""

    def __init__(self, socket_path: str | None = None):
        """Initialize Docker manager.

        Args:
            socket_path: Path to Docker socket (default: /var/run/docker.sock)
        """
        self.client = docker.DockerClient(
            base_url=f"unix://{socket_path or '/var/run/docker.sock'}"
        )

    def create_container(
        self,
        image: str,
        network_name: str,
        ports: dict[str, int] | None = None,
        volumes: dict[str, dict[str, str]] | None = None,
        environment: dict[str, str] | None = None,
        labels: dict[str, str] | None = None,
        name: str | None = None
    ) -> Container:
        """Create and start a Docker container.

        Args:
            image: Docker image to use
            network_name: Network name to connect to
            ports: Port mappings {container_port: host_port}
            volumes: Volume mappings {volume_name: {"bind": path, "mode": "rw"}}
            environment: Environment variables
            labels: Container labels
            name: Container name

        Returns:
            Container object
        """
        # Get or create network
        network = self.get_network(network_name) or self.create_network(network_name)

        # Build container configuration
        container_config = {
            "image": image,
            "network": network,
            "remove": False
        }

        if ports:
            container_config["ports"] = ports

        if volumes:
            host_volumes = {}
            for volume_name, config in volumes.items():
                # Create named volumes if they don't exist
                self._ensure_volume(volume_name)
                host_volumes[volume_name] = config

            container_config["volumes"] = host_volumes

        if environment:
            container_config["environment"] = environment

        if labels:
            container_config["labels"] = labels

        if name:
            container_config["name"] = name

        # Create and return container
        container = self.client.containers.run(**container_config)
        return container

    def list_containers(self, filters: dict[str, Any] | None = None) -> list[Container]:
        """List all containers with optional filters.

        Args:
            filters: Docker filter criteria

        Returns:
            List of Container objects
        """
        return self.client.containers.list(filters=filters or {})

    def get_container(self, container_id: str) -> Container | None:
        """Get a specific container by ID or name.

        Args:
            container_id: Container ID or name

        Returns:
            Container object or None if not found
        """
        try:
            return self.client.containers.get(container_id)
        except docker.errors.NotFound:
            return None

    def get_network(self, network_name: str) -> Network | None:
        """Get a network by name.

        Args:
            network_name: Network name

        Returns:
            Network object or None if not found
        """
        try:
            return self.client.networks.get(network_name)
        except docker.errors.NotFound:
            return None

    def create_network(self, network_name: str) -> Network:
        """Create a new Docker network.

        Args:
            network_name: Name for the new network

        Returns:
            Network object
        """
        network = self.client.networks.create(
            name=network_name,
            driver="bridge"
        )
        return network

    def remove_network(self, network_name: str) -> None:
        """Remove a Docker network.

        Args:
            network_name: Network name to remove
        """
        network = self.get_network(network_name)
        if network:
            network.remove()

    def _ensure_volume(self, volume_name: str) -> None:
        """Ensure a named volume exists.

        Args:
            volume_name: Volume name
        """
        try:
            self.client.volumes.get(volume_name)
        except docker.errors.NotFound:
            logger.info(f"Creating volume: {volume_name}")
            self.client.volumes.create(name=volume_name)

    def pull_image(self, image_name: str) -> Image:
        """Pull a Docker image.

        Args:
            image_name: Image name

        Returns:
            Image object
        """
        logger.info(f"Pulling image: {image_name}")
        return self.client.images.pull(image_name)
