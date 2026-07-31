"""
README Generator — Generates README.md with verified run commands.
"""

from __future__ import annotations

from generators.base import Generator, ValidationResult, register_generator
from spec.models import ProjectSpec, TargetAgent


@register_generator
class ReadmeGenerator(Generator):
    """Generates README.md with verified run commands and agent-specific quickstarts."""

    @property
    def target_agents(self) -> list[TargetAgent]:
        return []  # Shared - runs for all projects

    @property
    def output_files(self) -> list[str]:
        return ["README.md"]

    def generate(self, spec: ProjectSpec) -> dict[str, str]:
        """Generate README.md from spec."""
        files = {}
        files["README.md"] = self._generate_readme(spec)
        return files

    def _generate_readme(self, spec: ProjectSpec) -> str:
        lines = [
            f"# {spec.project_name}",
            "",
            f"**{spec.product_description}**",
            "",
            "---",
            "",
            "## Quick Start",
            "",
            "### Prerequisites",
            "- Docker & Docker Compose",
            "- Python 3.12+ (for local development)",
            "",
            "### Start Development Environment",
            "```bash",
            "docker compose up -d",
            "```",
            "",
            "This starts:",
        ]

        if spec.infra.ollama.enabled:
            lines.append("- Ollama (LLM) at http://localhost:11434")
        if spec.infra.qdrant.enabled:
            lines.append("- Qdrant (Vector DB) at http://localhost:6333")
        if spec.infra.mem0.enabled:
            lines.append("- mem0 (Memory) at http://localhost:8000")
        if spec.infra.postgres.enabled:
            lines.append("- PostgreSQL at localhost:5432")
        if spec.infra.redis.enabled:
            lines.append("- Redis at localhost:6379")

        lines.extend([
            "",
            "### Verify Services",
            "```bash",
            "docker compose ps",
            "```",
            "",
            "All services should show `healthy` or `running`.",
            "",
            "---",
            "",
        ])

        # Agent-specific sections
        if TargetAgent.HERMES in spec.target_agents:
            lines.extend(self._hermes_section(spec))

        if TargetAgent.CURSOR in spec.target_agents:
            lines.extend(self._cursor_section(spec))

        if TargetAgent.OPENCODE in spec.target_agents:
            lines.extend(self._opencode_section(spec))

        # Common sections
        lines.extend([
            "---",
            "",
            "## Project Structure",
            "",
            "```",
            f"{spec.project_name}/",
            "├── AGENTS.md              # Agent team configuration (Hermes, Opencode)",
            "├── memory.json          # mem0 configuration",
            "├── .hermes/rules.md     # Hermes-specific rules",
            "├── .cursorrules         # Cursor rules",
            "├── .cursor/mcp.json     # Cursor MCP servers",
            "├── .opencode/config.json # Opencode configuration",
            "├── docker-compose.yml   # Infrastructure",
            "├── eval.yaml            # Evaluation harness config",
            "├── eval/                # Pytest benchmarks",
            "├── agent-config-spec.json # Source specification",
            "└── README.md            # This file",
            "```",
            "",
            "---",
            "",
            "## Evaluation",
            "",
            "Run the evaluation harness to verify agent quality:",
            "",
            "```bash",
            "cd eval && pytest -v",
            "```",
            "",
            "Benchmarks defined in `eval.yaml` with thresholds per agent role.",
            "",
            "---",
            "",
            "## Configuration",
            "",
            "This project was configured with [AgentConfig](https://github.com/your-org/agent-config).",
            "",
            "Source spec: `agent-config-spec.json`",
            "",
            "To regenerate configs after changes:",
            "",
            "```bash",
            "agent-config build --spec-file agent-config-spec.json --force",
            "```",
            "",
            "---",
            "",
            "## Tech Stack",
            "",
            f"- **Language:** {spec.tech_stack.language.value}",
        ])

        if spec.tech_stack.frontend.value != "none":
            lines.append(f"- **Frontend:** {spec.tech_stack.frontend.value}")
        if spec.tech_stack.backend.value != "none":
            lines.append(f"- **Backend:** {spec.tech_stack.backend.value}")
        if spec.tech_stack.database.value != "none":
            lines.append(f"- **Database:** {spec.tech_stack.database.value}")
        if spec.tech_stack.orm.value != "none":
            lines.append(f"- **ORM:** {spec.tech_stack.orm.value}")
        if spec.tech_stack.auth.value != "none":
            lines.append(f"- **Auth:** {spec.tech_stack.auth.value}")
        if spec.tech_stack.testing.value != "none":
            lines.append(f"- **Testing:** {spec.tech_stack.testing.value}")
        if spec.tech_stack.ci.value != "none":
            lines.append(f"- **CI:** {spec.tech_stack.ci.value}")

        lines.extend([
            "",
            "---",
            "",
            "*Generated with AgentConfig v0.1*",
        ])

        return "\n".join(lines)

    def _hermes_section(self, spec: ProjectSpec) -> list[str]:
        return [
            "## Hermes",
            "",
            "### Config Files",
            "- `AGENTS.md` — Agent team (orchestrator + workers)",
            "- `memory.json` — mem0-local configuration",
            "- `.hermes/rules.md` — Project rules & conventions",
            "",
            "### Usage",
            "```bash",
            "# In Hermes, the agents are auto-loaded from AGENTS.md",
            "# Just start a conversation and they'll use the configuration",
            "```",
            "",
        ]

    def _cursor_section(self, spec: ProjectSpec) -> list[str]:
        return [
            "## Cursor",
            "",
            "### Config Files",
            "- `.cursorrules` — Project rules for Cursor's AI",
            "- `.cursor/mcp.json` — MCP server definitions",
            "",
            "### Usage",
            "```bash",
            "# Open in Cursor: cursor .",
            "# The rules are auto-applied to Cursor's agent mode",
            "# MCP servers available via Ctrl+Shift+P > MCP",
            "```",
            "",
        ]

    def _opencode_section(self, spec: ProjectSpec) -> list[str]:
        return [
            "## Opencode",
            "",
            "### Config Files",
            "- `AGENTS.md` — Agent team (same format as Hermes)",
            "- `.opencode/config.json` — Opencode settings",
            "",
            "### Usage",
            "```bash",
            "# Run: opencode",
            "# Agents from AGENTS.md are auto-loaded",
            "```",
            "",
        ]

    def validate_output(self, files: dict[str, str]) -> ValidationResult:
        """Validate generated README."""
        errors = []
        readme = files.get("README.md", "")

        required = ["Quick Start", "docker compose up", "Tech Stack"]
        for req in required:
            if req not in readme:
                errors.append(f"README missing required section: {req}")

        return ValidationResult(valid=len(errors) == 0, errors=errors)
