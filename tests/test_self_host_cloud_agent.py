"""Tests for self-host-cloud-agent."""

from pathlib import Path

import pytest

from self_host_cloud_agent.app import DeploymentResult, ServerManager
from self_host_cloud_agent.docker_manager import DockerManager
from self_host_cloud_agent.reverse_proxy import ReverseProxyManager
from self_host_cloud_agent.ssl_manager import SSLManager


class TestDeploymentResult:
    """Tests for DeploymentResult dataclass."""

    def test_success_result(self) -> None:
        """Test successful deployment result."""
        result = DeploymentResult(
            service_name="test_service",
            success=True,
            container_id="abc123",
            status="running",
            message="Success"
        )

        assert result.success is True
        assert result.container_id == "abc123"
        assert result.status == "running"

    def test_failure_result(self) -> None:
        """Test failed deployment result."""
        result = DeploymentResult(
            service_name="test_service",
            success=False,
            container_id=None,
            status="failed",
            message="Error occurred"
        )

        assert result.success is False
        assert result.container_id is None
        assert result.status == "failed"

    def test_default_fields(self) -> None:
        """Test default network_name field."""
        result = DeploymentResult(
            service_name="test",
            success=True,
            container_id="test123",
            status="running",
            message="Success"
        )

        assert result.network_name is None


class TestDockerManager:
    """Tests for DockerManager class."""

    def test_create_client(self) -> None:
        """Test Docker client creation."""
        manager = DockerManager()
        assert manager.client is not None

    def test_list_containers_empty(self) -> None:
        """Test listing containers when empty."""
        manager = DockerManager()
        containers = manager.list_containers()

        assert isinstance(containers, list)

    def test_get_nonexistent_network(self) -> None:
        """Test getting a network that doesn't exist."""
        manager = DockerManager()
        network = manager.get_network("nonexistent_network_xyz")

        assert network is None


class TestReverseProxyManager:
    """Tests for ReverseProxyManager class."""

    def test_create_config(self, tmp_path: Path) -> None:
        """Test creating Traefik configuration."""
        config_path = tmp_path / "traefik.yml"
        manager = ReverseProxyManager(config_path=str(config_path))

        status = manager.get_proxy_status()
        assert status["config_exists"] is True

    def test_configure_upstream(self, tmp_path: Path) -> None:
        """Test configuring an upstream service."""
        config_path = tmp_path / "traefik.yml"
        manager = ReverseProxyManager(config_path=str(config_path))

        manager.configure_upstream(
            service_name="test_service",
            host="test.example.com",
            container_port=8080
        )

        status = manager.get_proxy_status()
        assert status["config_exists"] is True


class TestSSLManager:
    """Tests for SSLManager class."""

    def test_certificate_not_found(self, tmp_path: Path) -> None:
        """Test checking certificate that doesn't exist."""
        manager = SSLManager()
        info = manager.get_certificate_info("nonexistent.example.com")

        assert info["exists"] is False

    def test_renewal_returns_structure(self) -> None:
        """Test renewal returns proper structure."""
        manager = SSLManager()
        result = manager.renew_certificates()

        assert "success" in result
        assert "output" in result
        assert "errors" in result


class TestServerManager:
    """Tests for ServerManager class."""

    def test_init_creates_base_path(self, tmp_path: Path) -> None:
        """Test that base path is created on init."""
        manager = ServerManager(base_path=tmp_path / "test_base")
        assert (tmp_path / "test_base").exists()

    def test_list_services_empty(self) -> None:
        """Test listing services when no services exist."""
        manager = ServerManager()
        services = manager.list_services()

        assert isinstance(services, list)


class TestCLICommands:
    """Tests for CLI commands."""

    def test_deploy_help(self) -> None:
        """Test deploy command help."""
        from click.testing import CliRunner
        from self_host_cloud_agent.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["deploy", "--help"])

        assert result.exit_code == 0
        assert "Deploy a Docker service" in result.output

    def test_stop_help(self) -> None:
        """Test stop command help."""
        from click.testing import CliRunner
        from self_host_cloud_agent.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["stop", "--help"])

        assert result.exit_code == 0
        assert "Stop a deployed service" in result.output

    def test_list_help(self) -> None:
        """Test list command help."""
        from click.testing import CliRunner
        from self_host_cloud_agent.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["list", "--help"])

        assert result.exit_code == 0
        assert "List all deployed services" in result.output
