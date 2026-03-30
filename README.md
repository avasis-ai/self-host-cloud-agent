# Self-Host Cloud Agent

[![PyPI](https://img.shields.io/pypi/v/self-host-cloud-agent)](https://pypi.org/project/self-host-cloud-agent)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](https://www.apache.org/licenses/LICENSE-2.0)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)]()

## 🏠 Self-Host Cloud Agent

**The agent that completely manages your personal server.**

## What It Does

Designed for the homelab community, this agent autonomously:

1. **Finds** open-source repositories (e.g., Jellyfin for local Netflix)
2. **Writes** Docker Compose configurations
3. **Configures** reverse proxies
4. **Provisions** SSL certificates
5. **Launches** your services with zero configuration

## Installation

```bash
pip install self-host-cloud-agent
```

Or install from source:

```bash
pip install -e .
```

## Quick Start

### Deploy a Simple Service

```bash
# Deploy Jellyfin with reverse proxy and SSL
self-host-cloud-agent deploy jellyfin jellyfin/lamp \
    --ports 8080:8080 \
    --volumes data:/config \
    --env TZ=America/New_York \
    --proxy jellyfin.yourdomain.com
```

### Deploy Without SSL

```bash
# Deploy a service without SSL (for local testing)
self-host-cloud-agent deploy testapp testimage \
    --ports 80:80 \
    --no-ssl
```

### Stop a Service

```bash
self-host-cloud-agent stop jellyfin
```

### Remove a Service

```bash
self-host-cloud-agent remove jellyfin
```

### List All Services

```bash
self-host-cloud-agent list
```

## CLI Reference

```bash
self-host-cloud-agent --help

Commands:
  deploy    Deploy a Docker service
  stop      Stop a deployed service
  remove    Remove a deployed service and all its resources
  list      List all deployed services
```

### Deploy Command Options

```
--ports, -p        Port mappings (host:container)
--volumes, -v      Volume mappings (volume:container_path)
--env, -e          Environment variables (KEY=VALUE)
--proxy            Reverse proxy hostname
--no-ssl           Disable SSL for this service
```

### Examples

#### Deploy Nextcloud with SSL

```bash
self-host-cloud-agent deploy nextcloud nextcloud:latest \
    --ports 80:80 -p 443:443 \
    --volumes data:/var/www/html \
    --volumes db:/var/www/html/nextcloud/data \
    --env NEXTCLOUD_TRUSTED_DOMAINS=cloud.example.com \
    --proxy cloud.example.com
```

#### Deploy CasaOS

```bash
self-host-cloud-agent deploy casaos casaos/casaos \
    --ports 80:80 \
    --volumesCasaOS:/var/lib/casaos \
    --env TZ=America/New_York
```

## How It Works

### Architecture

```
┌─────────────────┐
│  CLI Interface  │
└────────┬────────┘
         │
         ▼
┌──────────────────┐
│  ServerManager   │
└───────┬──────────┘
        │
    ┌───┴───┐
    ▼       ▼
┌─────────┐ ┌────────────────┐
│ Docker  │ │ Reverse Proxy  │
│Manager  │ │ Manager        │
└────┬────┘ └────┬───────────┘
     │          │
     ▼          ▼
┌─────────────┐ ┌────────────────┐
│  Containers │ │ SSL Manager    │
│             │ │ (Certbot)      │
└─────────────┘ └────────────────┘
```

### Deployment Flow

1. **Parse input**: CLI arguments are parsed into deployment configuration
2. **Create network**: A dedicated Docker network is created for isolation
3. **Pull image**: The specified Docker image is pulled if not present
4. **Start container**: Container is started with configured ports, volumes, and environment
5. **Configure proxy**: If a proxy hostname is provided, Traefik is configured
6. **Provision SSL**: SSL certificate is automatically provisioned using Certbot

## Project Structure

```
self-host-cloud-agent/
├── pyproject.toml           # Project configuration
├── src/self_host_cloud_agent/
│   ├── __init__.py         # Package initialization
│   ├── app.py              # Core server manager logic
│   ├── cli.py              # CLI entry point with Click
│   ├── docker_manager.py   # Docker API wrapper
│   ├── reverse_proxy.py    # Traefik configuration
│   └── ssl_manager.py      # Certbot integration
├── tests/
│   └── test_self_host_cloud_agent.py
├── README.md               # This file
├── AGENTS.md               # Agent configuration
└── LICENSE                 # Apache 2.0 license
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=self_host_cloud_agent

# Quick test run
pytest tests/ -q
```

## Requirements

- Python 3.10+
- Docker Engine (latest)
- Docker socket access: `/var/run/docker.sock`
- Certbot (for SSL certificates)
- Traefik reverse proxy (recommended)

## Usage Notes

### Docker Socket

The agent requires access to the Docker socket. Ensure it's mounted:

```bash
docker run -v /var/run/docker.sock:/var/run/docker.sock self-host-cloud-agent
```

### Reverse Proxy

For production deployments, it's recommended to run a Traefik reverse proxy:

```bash
docker run -d \
    --name traefik \
    -p 80:80 \
    -p 443:443 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    traefik:latest
```

### Certbot

SSL certificates require Certbot to be installed:

```bash
# Ubuntu/Debian
apt install certbot

# CentOS/RHEL
dnf install certbot

# Or via pip
pip install certbot
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the **Apache 2.0 License** - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by **Coolify** for homelab deployment automation
- Built on top of the official **Docker SDK** and **Certbot**
- Inspired by the thriving **r/SelfHosted** community
- Reverse proxy integration with **Traefik**

## Version

Current version: **0.1.0**

---

**Agent #99** - Your personal server, completely managed.
