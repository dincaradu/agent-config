"""
Docker Compose Generator — Shared infrastructure for all projects.
Generates docker-compose.yml with Ollama, Qdrant, mem0, Postgres, Redis.
"""

from __future__ import annotations

from generators.base import Generator, ValidationResult, register_generator
from spec.models import ProjectSpec, TargetAgent


@register_generator
class DockerComposeGenerator(Generator):
    """Generates docker-compose.yml for local-first infrastructure."""

    @property
    def target_agents(self) -> list[TargetAgent]:
        return []  # Shared - runs for all projects

    @property
    def output_files(self) -> list[str]:
        return ["docker-compose.yml"]

    def generate(self, spec: ProjectSpec) -> dict[str, str]:
        """Generate docker-compose.yml from spec."""
        infra = spec.infra
        project_name = spec.project_name

        services = {}
        volumes = {}

        # Ollama
        if infra.ollama.enabled:
            # Inside Docker, use service name; externally use base_url
            internal_ollama_url = "http://ollama:11434"
            services["ollama"] = {
                "image": "ollama/ollama:latest",
                "container_name": f"{project_name}_ollama",
                "ports": ["11434:11434"],
                "volumes": ["ollama_data:/root/.ollama"],
                "networks": ["agent-config-network"],
                "restart": "unless-stopped",
                "healthcheck": {
                    "test": ["CMD", "curl", "-f", f"{internal_ollama_url}/api/tags"],
                    "interval": "10s",
                    "timeout": "5s",
                    "retries": 5,
                },
            }
            volumes["ollama_data"] = {}

        # Qdrant
        if infra.qdrant.enabled:
            services["qdrant"] = {
                "image": "qdrant/qdrant:v1.18.1",
                "container_name": f"{project_name}_qdrant",
                "ports": ["6333:6333", "6334:6334"],
                "volumes": ["qdrant_data:/qdrant/storage"],
                "networks": ["agent-config-network"],
                "restart": "unless-stopped",
                "healthcheck": {
                    "test": ["CMD", "curl", "-f", "http://qdrant:6333/healthz"],
                    "interval": "10s",
                    "timeout": "5s",
                    "retries": 5,
                },
            }
            volumes["qdrant_data"] = {}

        # mem0
        if infra.mem0.enabled:
            if infra.mem0.provider.value == "mem0-local":
                services["mem0"] = {
                    "image": "mem0ai/mem0:latest",
                    "container_name": f"{project_name}_mem0",
                    "ports": ["8000:8000"],
                    "environment": {
                        "OLLAMA_BASE_URL": "http://ollama:11434",
                        "EMBEDDER_MODEL": infra.mem0.ollama_embed_model,
                        "LLM_MODEL": infra.mem0.ollama_llm_model,
                        "VECTOR_STORE": "qdrant",
                        "QDRANT_URL": "http://qdrant:6333",
                        "COLLECTION_NAME": infra.mem0.qdrant_collection,
                    },
                    "depends_on": {
                        "ollama": {"condition": "service_healthy"},
                        "qdrant": {"condition": "service_healthy"},
                    },
                    "networks": ["agent-config-network"],
                    "restart": "unless-stopped",
                }

        # Postgres
        if infra.postgres.enabled:
            services["postgres"] = {
                "image": "postgres:16-alpine",
                "container_name": f"{project_name}_postgres",
                "environment": {
                    "POSTGRES_USER": infra.postgres.user,
                    "POSTGRES_PASSWORD": infra.postgres.password,
                    "POSTGRES_DB": infra.postgres.database,
                },
                "volumes": ["postgres_data:/var/lib/postgresql/data"],
                "ports": ["5432:5432"],
                "networks": ["agent-config-network"],
                "restart": "unless-stopped",
                "healthcheck": {
                    "test": ["CMD-SHELL", "pg_isready -U postgres"],
                    "interval": "10s",
                    "timeout": "5s",
                    "retries": 5,
                },
            }
            volumes["postgres_data"] = {}

        # Redis
        if infra.redis.enabled:
            services["redis"] = {
                "image": "redis:7-alpine",
                "container_name": f"{project_name}_redis",
                "ports": ["6379:6379"],
                "volumes": ["redis_data:/data"],
                "networks": ["agent-config-network"],
                "restart": "unless-stopped",
                "healthcheck": {
                    "test": ["CMD", "redis-cli", "ping"],
                    "interval": "10s",
                    "timeout": "5s",
                    "retries": 5,
                },
            }
            volumes["redis_data"] = {}

        # Build compose dict
        compose = {
            "version": "3.8",
            "services": services,
            "networks": {
                "agent-config-network": {
                    "driver": "bridge",
                }
            },
            "volumes": volumes,
        }

        # Convert to YAML
        import yaml
        yaml_content = yaml.dump(compose, sort_keys=False, default_flow_style=False)

        # Add header comment
        header = f"""# AgentConfig Generated Docker Compose
# Project: {spec.project_name}
# Generated: {spec.updated_at.isoformat()}
# 
# Run: docker compose up -d
# 
# Services:
"""
        for svc_name in services:
            header += f"#   - {svc_name}\n"

        return {"docker-compose.yml": header + "\n" + yaml_content}

    def validate_output(self, files: dict[str, str]) -> ValidationResult:
        """Validate docker-compose.yml syntax."""
        try:
            import yaml
            yaml.safe_load(files.get("docker-compose.yml", ""))
            return ValidationResult(valid=True)
        except Exception as e:
            return ValidationResult(valid=False, errors=[f"Invalid YAML: {e}"])
