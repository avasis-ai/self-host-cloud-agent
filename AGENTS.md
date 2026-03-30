# AGENTS.md - Agent Configuration

## Self-Host Cloud Agent

This is **Agent #99** - the autonomous server management agent.

### Configuration

- **Name**: self-host-cloud-agent
- **Purpose**: Complete personal server management
- **Domain**: Docker container orchestration, reverse proxy configuration, SSL certificate provisioning

### Capabilities

- Docker container lifecycle management
- Port mapping and network configuration
- Volume management for persistent data
- Reverse proxy integration (Traefik)
- SSL certificate provisioning (Certbot)
- Service deployment automation

### Usage

This agent should be used for:

- Homelab deployments
- Personal media servers
- Local cloud services
- Home automation infrastructure

### Constraints

- Requires Docker socket access
- SSL provisioning requires Certbot
- Reverse proxy configuration assumes Traefik
- Always test in non-production first

### Volume Mapping

Standard volume naming convention:
- `{service_name}_data` - Service data and configuration
- `{service_name}_db` - Database storage
- `{service_name}_config` - Configuration files

---

For more information, see [README.md](README.md).
