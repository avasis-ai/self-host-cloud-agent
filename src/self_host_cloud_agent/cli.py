"""CLI entry point for self-host-cloud-agent."""

import click
from pathlib import Path

from self_host_cloud_agent.app import DeploymentResult, ServerManager


@click.group()
@click.version_option(version="0.1.0", prog_name="self-host-cloud-agent")
def cli():
    """Self-Host Cloud Agent - Manage your personal server.

    Autonomously deploy Docker containers, configure reverse proxies,
    and provision SSL certificates for homelab deployments.
    """
    pass


@cli.command()
@click.argument("service_name")
@click.argument("image")
@click.option("--ports", "-p", multiple=True, help="Port mappings (host:container)")
@click.option("--volumes", "-v", multiple=True, help="Volume mappings (volume:container_path)")
@click.option("--env", "-e", multiple=True, help="Environment variables (KEY=VALUE)")
@click.option("--proxy", help="Reverse proxy hostname")
@click.option("--no-ssl", is_flag=True, help="Disable SSL for this service")
def deploy(service_name: str, image: str, ports: tuple, volumes: tuple, env: tuple, proxy: str, no_ssl: bool) -> None:
    """Deploy a Docker service.

    Example:
        self-host-cloud-agent deploy jellyfin jellyfin/lamp \
            --ports 80:8080 -p 443:443 \
            --volumes data:/config \
            --env TZ=America/New_York \
            --proxy jellyfin.example.com
    """
    manager = ServerManager()

    # Parse ports
    port_map = {}
    for port_spec in ports:
        host_port, container_port = port_spec.split(":")
        port_map[container_port] = int(host_port)

    # Parse volumes
    volume_map = {}
    for volume_spec in volumes:
        volume_name, container_path = volume_spec.split(":")
        volume_map[volume_name] = {"bind": container_path, "mode": "rw"}

    # Parse environment
    env_map = {}
    for env_spec in env:
        key, value = env_spec.split("=", 1)
        env_map[key] = value

    result = manager.deploy_service(
        service_name=service_name,
        image=image,
        ports=port_map if port_map else None,
        volumes=volume_map if volume_map else None,
        environment=env_map if env_map else None,
        reverse_proxy_host=proxy,
        ssl_enabled=not no_ssl
    )

    _print_deployment_result(result)


@cli.command()
@click.argument("service_name")
def stop(service_name: str) -> None:
    """Stop a deployed service."""
    manager = ServerManager()
    result = manager.stop_service(service_name)
    _print_deployment_result(result)


@cli.command()
@click.argument("service_name")
def remove(service_name: str) -> None:
    """Remove a deployed service and all its resources."""
    manager = ServerManager()
    result = manager.remove_service(service_name)
    _print_deployment_result(result)


@cli.command()
def list_services() -> None:
    """List all deployed services."""
    manager = ServerManager()
    services = manager.list_services()

    if not services:
        click.echo("No services deployed yet.")
        return

    click.echo(f"{'Name':<20} {'Status':<12} {'Image':<30}")
    click.echo("-" * 65)

    for service in services:
        click.echo(
            f"{service['name']:<20} "
            f"{service['status']:<12} "
            f"{service['image']:<30}"
        )


def _print_deployment_result(result: DeploymentResult) -> None:
    """Print deployment result to CLI.

    Args:
        result: Deployment result object
    """
    status_icon = "✓" if result.success else "✗"
    click.echo(f"\n{status_icon} {result.service_name}: {result.message}")

    if result.container_id:
        click.echo(f"  Container ID: {result.container_id}")

    if result.status:
        click.echo(f"  Status: {result.status}")

    if not result.success and result.message:
        click.echo(f"  Error: {result.message}")


if __name__ == "__main__":
    cli()
