"""
AgentConfig — ProjectSpec Models

Single source of truth for agent configuration generation.
Everything flows from ProjectSpec.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

# ──────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────

class TargetAgent(str, Enum):
    """AI agents that can consume generated configurations."""
    HERMES = "hermes"
    CURSOR = "cursor"
    OPENCODE = "opencode"
    CLAUDE_CODE = "claude-code"
    AIDER = "aider"
    CODEX = "codex"
    WINDSURF = "windsurf"
    ZED = "zed"


class AgentRole(str, Enum):
    """Roles in the agent team topology."""
    ORCHESTRATOR = "orchestrator"
    FEATURE = "feature"
    REVIEW = "review"
    TEST = "test"
    RESEARCH = "research"
    DOCS = "docs"
    DEPS = "deps"


class ProductType(str, Enum):
    """High-level project type."""
    SAAS = "saas"
    CLI = "cli"
    API = "api"
    INTERNAL_TOOL = "internal-tool"
    MOBILE = "mobile"
    LIBRARY = "library"
    DATA_PIPELINE = "data-pipeline"


class HostingTarget(str, Enum):
    """Deployment target."""
    VERCEL = "vercel"
    RAILWAY = "railway"
    FLY = "fly"
    SELF_HOSTED = "self-hosted"
    K8S = "k8s"
    NONE = "none"


class Language(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    GO = "go"
    RUST = "rust"


class FrontendFramework(str, Enum):
    NEXTJS = "nextjs"
    REACT = "react"
    VUE = "vue"
    SVELTE = "svelte"
    HTMX = "htmx"
    NONE = "none"


class BackendFramework(str, Enum):
    FASTAPI = "fastapi"
    DJANGO = "django"
    FLASK = "flask"
    EXPRESS = "express"
    HONO = "hono"
    GO_CHI = "go-chi"
    AXUM = "axum"
    NONE = "none"


class Database(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"
    REDIS = "redis"
    NONE = "none"


class ORM(str, Enum):
    SQLALCHEMY = "sqlalchemy"
    PRISMA = "prisma"
    DRIZZLE = "drizzle"
    GORM = "gorm"
    SQLX = "sqlx"
    NONE = "none"


class AuthProvider(str, Enum):
    JWT = "jwt"
    CLERK = "clerk"
    AUTH0 = "auth0"
    SUPABASE = "supabase"
    NEXTAUTH = "nextauth"
    NONE = "none"


class TestingFramework(str, Enum):
    PYTEST = "pytest"
    VITEST = "vitest"
    JEST = "jest"
    PLAYWRIGHT = "playwright"
    NONE = "none"


class CIProvider(str, Enum):
    GITHUB_ACTIONS = "github-actions"
    GITLAB_CI = "gitlab-ci"
    CIRCLECI = "circleci"
    NONE = "none"


class Containerization(str, Enum):
    DOCKER = "docker"
    PODMAN = "podman"
    NONE = "none"


class PackageManager(str, Enum):
    UV = "uv"
    PIP = "pip"
    POETRY = "poetry"
    PNPM = "pnpm"
    NPM = "npm"
    BUN = "bun"
    CARGO = "cargo"
    GO_MOD = "go-mod"


class MemoryProvider(str, Enum):
    MEM0 = "mem0"
    MEM0_LOCAL = "mem0-local"
    NONE = "none"


class VectorStore(str, Enum):
    QDRANT = "qdrant"
    CHROMA = "chroma"
    WEAVIATE = "weaviate"
    NONE = "none"


class EvalFramework(str, Enum):
    PYTEST = "pytest"
    VITEST = "vitest"
    CUSTOM = "custom"


# ──────────────────────────────────────────────────────────────
# Nested Configuration Models
# ──────────────────────────────────────────────────────────────

class TechStack(BaseModel):
    """Technology stack configuration."""
    language: Language = Language.PYTHON
    frontend: FrontendFramework = FrontendFramework.NONE
    backend: BackendFramework = BackendFramework.NONE
    database: Database = Database.NONE
    orm: ORM = ORM.NONE
    auth: AuthProvider = AuthProvider.NONE
    testing: TestingFramework = TestingFramework.NONE
    ci: CIProvider = CIProvider.NONE
    containerization: Containerization = Containerization.DOCKER
    package_manager: PackageManager = PackageManager.UV


class AgentTeam(BaseModel):
    """Agent team topology — which roles and how many."""
    orchestrator: bool = True
    workers: dict[AgentRole, int] = Field(
        default_factory=lambda: {
            AgentRole.FEATURE: 1,
            AgentRole.REVIEW: 1,
        }
    )


class OllamaConfig(BaseModel):
    """Ollama local LLM configuration."""
    enabled: bool = True
    host: str = "ollama"
    port: int = 11434
    models: list[str] = Field(default_factory=lambda: ["llama3.2:latest", "gemma4:latest"])
    default_model: str = "llama3.2:latest"
    default_embed_model: str = "nomic-embed-text"


class QdrantConfig(BaseModel):
    """Qdrant vector database configuration."""
    enabled: bool = True
    host: str = "qdrant"
    port: int = 6333
    grpc_port: int = 6334
    collection_prefix: str = "agent-config"


class Mem0Config(BaseModel):
    """mem0 memory layer configuration."""
    enabled: bool = True
    provider: MemoryProvider = MemoryProvider.MEM0_LOCAL
    host: str = "mem0"
    port: int = 8000
    # mem0-local specific
    ollama_embed_model: str = "nomic-embed-text"
    ollama_llm_model: str = "llama3.2:latest"
    qdrant_collection: str = "memories"


class PostgresConfig(BaseModel):
    """PostgreSQL configuration."""
    enabled: bool = True
    host: str = "postgres"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    database: str = "agent_config"


class RedisConfig(BaseModel):
    """Redis configuration."""
    enabled: bool = False
    host: str = "redis"
    port: int = 6379


class MonitoringConfig(BaseModel):
    """Observability / monitoring configuration."""
    enabled: bool = False
    langfuse: bool = False
    langsmith: bool = False
    sentry: bool = False


class Infrastructure(BaseModel):
    """Complete infrastructure configuration."""
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    qdrant: QdrantConfig = Field(default_factory=QdrantConfig)
    mem0: Mem0Config = Field(default_factory=Mem0Config)
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)


class Mem0LocalConfig(BaseModel):
    """mem0-local specific configuration."""
    ollama_base_url: str = "http://ollama:11434"
    embedder_model: str = "nomic-embed-text"
    embedder_dim: int = 768
    llm_model: str = "llama3.2:latest"
    vector_store: VectorStore = VectorStore.QDRANT
    qdrant_url: str = "http://qdrant:6333"
    collection_name: str = "memories"


class Mem0CloudConfig(BaseModel):
    """mem0 cloud configuration."""
    api_key: str = ""
    org_id: str = ""
    project_id: str = ""


class MemoryConfig(BaseModel):
    """Memory layer configuration."""
    provider: MemoryProvider = MemoryProvider.MEM0_LOCAL
    mem0_local: Mem0LocalConfig = Field(default_factory=Mem0LocalConfig)
    mem0_cloud: Mem0CloudConfig | None = None


class VectorStoreConfig(BaseModel):
    """Vector store configuration."""
    provider: VectorStore = VectorStore.QDRANT
    qdrant_url: str = "http://qdrant:6333"
    chroma_url: str = "http://chroma:8000"
    weaviate_url: str = "http://weaviate:8080"
    collection_prefix: str = "agent-config"


class RAGSource(BaseModel):
    """RAG document source configuration."""
    name: str
    type: Literal["local", "github", "s3", "gdrive", "notion", "confluence", "web"]
    path: str | None = None
    url: str | None = None
    recursive: bool = True
    include_patterns: list[str] = Field(default_factory=lambda: ["**/*.md", "**/*.py", "**/*.txt"])
    exclude_patterns: list[str] = Field(default_factory=list)


class Benchmark(BaseModel):
    """Evaluation benchmark definition."""
    name: str
    agent_role: AgentRole
    test_file: str
    threshold: float = 0.8
    description: str = ""


class EvalConfig(BaseModel):
    """Evaluation harness configuration."""
    enabled: bool = True
    framework: EvalFramework = EvalFramework.PYTEST
    benchmarks: list[Benchmark] = Field(default_factory=list)
    thresholds: dict[str, float] = Field(default_factory=dict)


class DetectedStack(BaseModel):
    """Auto-detected stack from existing repository."""
    language: Language | None = None
    frontend: FrontendFramework | None = None
    backend: BackendFramework | None = None
    database: Database | None = None
    orm: ORM | None = None
    testing: TestingFramework | None = None
    ci: CIProvider | None = None
    package_manager: PackageManager | None = None
    config_files: list[str] = Field(default_factory=list)


class Conventions(BaseModel):
    """Project coding conventions and standards."""
    # Code style
    line_length: int = 100
    type_hints: bool = True
    docstrings: Literal["google", "numpy", "sphinx", "none"] = "google"
    # Error handling
    error_handling: Literal["exceptions", "result-type", "both"] = "exceptions"
    # Logging
    logging_library: Literal["structlog", "logging", "loguru"] = "structlog"
    log_level: str = "INFO"
    # Config management
    config_library: Literal["pydantic-settings", "dynaconf", "environs", "none"] = "pydantic-settings"
    # Testing
    test_style: Literal["pytest", "unittest"] = "pytest"
    mock_library: Literal["pytest-mock", "unittest.mock", "responses"] = "pytest-mock"
    # Git
    conventional_commits: bool = True
    branch_naming: str = "type/scope-description"
    # Documentation
    doc_tool: Literal["mkdocs", "sphinx", "none"] = "mkdocs"


# ──────────────────────────────────────────────────────────────
# Main Specification
# ──────────────────────────────────────────────────────────────

class ProjectSpec(BaseModel):
    """
    Complete project specification — single source of truth.
    
    Generated through conversational elicitation, refined iteratively,
    committed to git, and used to generate all agent configurations.
    """
    # ── Identity ──────────────────────────────────────────────
    project_name: str = Field(
        ...,
        description="kebab-case, used for dirs, containers, networks",
        pattern=r"^[a-z0-9-]+$"
    )
    product_description: str = Field(
        default="",
        min_length=0,
        max_length=5000,
        description="Free-form description of what you're building"
    )
    product_type: ProductType = ProductType.CLI

    # ── Tech Stack ────────────────────────────────────────────
    tech_stack: TechStack = Field(default_factory=TechStack)

    # ── Team & Agent Topology ────────────────────────────────
    team_size: int = Field(default=1, ge=1, le=50)
    target_agents: list[TargetAgent] = Field(
        default_factory=lambda: [TargetAgent.HERMES, TargetAgent.CURSOR, TargetAgent.OPENCODE]
    )
    agent_team: AgentTeam = Field(default_factory=AgentTeam)

    # ── Infrastructure Philosophy ────────────────────────────
    local_first: bool = True
    hosting: HostingTarget = HostingTarget.SELF_HOSTED
    infra: Infrastructure = Field(default_factory=Infrastructure)

    # ── Memory & Knowledge ───────────────────────────────────
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    rag_sources: list[RAGSource] = Field(default_factory=list)

    # ── Evaluation & Quality ─────────────────────────────────
    eval_config: EvalConfig = Field(default_factory=EvalConfig)

    # ── Existing Context (optional) ──────────────────────────
    existing_repo_url: str | None = None
    existing_stack_detected: DetectedStack | None = None
    conventions: Conventions = Field(default_factory=Conventions)

    # ── Metadata ─────────────────────────────────────────────
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = "0.1"
    spec_version: str = "0.1"

    # ── Private / Runtime (not persisted) ──────────────────
    _confidence: dict[str, float] = {}
    _phase: Literal["elicitation", "refinement", "confirmation"] = "elicitation"

    def model_post_init(self, __context: Any) -> None:
        """Update timestamp on any change."""
        self.updated_at = datetime.utcnow()

    def update_confidence(self, field: str, confidence: float) -> None:
        """Track extraction confidence per field."""
        self._confidence[field] = max(0.0, min(1.0, confidence))

    def get_confidence(self, field: str) -> float:
        """Get confidence for a field."""
        return self._confidence.get(field, 0.0)

    def all_confident(self, threshold: float = 0.8) -> bool:
        """Check if all required fields meet confidence threshold."""
        required_fields = [
            "project_name", "product_description", "product_type",
            "tech_stack", "target_agents", "local_first"
        ]
        return all(self.get_confidence(f) >= threshold for f in required_fields)

    def to_json_file(self, path: str) -> None:
        """Write spec to JSON file."""
        import json
        data = self.model_dump(mode="json", exclude={"_confidence", "_phase"})
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    @classmethod
    def from_json_file(cls, path: str) -> ProjectSpec:
        """Load spec from JSON file."""
        import json
        with open(path) as f:
            data = json.load(f)
        return cls.model_validate(data)
