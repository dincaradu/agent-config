"""
Cursor Generator — Generates .cursorrules and .cursor/mcp.json for Cursor IDE.
"""

from __future__ import annotations

import json

from generators.base import Generator, ValidationResult, register_generator
from spec.models import ProjectSpec, TargetAgent


@register_generator
class CursorGenerator(Generator):
    """Generates Cursor IDE configuration files."""

    @property
    def target_agents(self) -> list[TargetAgent]:
        return [TargetAgent.CURSOR]

    @property
    def output_files(self) -> list[str]:
        return [".cursorrules", ".cursor/mcp.json"]

    def generate(self, spec: ProjectSpec) -> dict[str, str]:
        """Generate Cursor config files from spec."""
        files = {}

        # .cursorrules
        files[".cursorrules"] = self._generate_cursorrules(spec)

        # .cursor/mcp.json
        files[".cursor/mcp.json"] = self._generate_mcp_json(spec)

        return files

    def _generate_cursorrules(self, spec: ProjectSpec) -> str:
        """Generate .cursorrules with project conventions."""
        lines = [
            f"# Cursor Rules for {spec.project_name}",
            "",
            "## Project Overview",
            f"- **Product:** {spec.product_description}",
            f"- **Type:** {spec.product_type.value}",
            f"- **Team Size:** {spec.team_size}",
            "",
            "## Tech Stack",
            f"- **Language:** {spec.tech_stack.language.value}",
        ]

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
            "## Coding Standards",
            f"- Line length: {spec.conventions.line_length} characters",
            f"- Type hints: {'Required' if spec.conventions.type_hints else 'Optional'}",
            f"- Docstrings: {spec.conventions.docstrings.title()} style",
            f"- Error handling: {spec.conventions.error_handling}",
            f"- Logging: {spec.conventions.logging_library} at {spec.conventions.log_level}",
            "",
            "## Agent Instructions",
            "",
            "### When writing code:",
            "1. Follow the tech stack and conventions above",
            "2. Use existing patterns in the codebase",
            "3. Write tests for new functionality",
            "4. Handle errors explicitly - no bare except",
            "5. Add type hints to all function signatures",
            f"6. Include {spec.conventions.docstrings} docstrings for public APIs",
            "",
            "### When reviewing code:",
            "1. Check for security issues (SQL injection, XSS, path traversal)",
            "2. Verify error handling is complete",
            "3. Ensure tests cover happy path + edge cases",
            "4. Confirm conventions are followed",
            "5. Look for performance issues (N+1 queries, memory leaks)",
            "",
            "### When generating tests:",
            "1. Target >80% coverage",
            "2. Test happy path, error paths, edge cases",
            f"3. Use {spec.tech_stack.testing.value} conventions",
            "4. Mock external dependencies",
            "",
            "## Project-Specific Context",
            "",
        ])

        # Add RAG sources context
        if spec.rag_sources:
            lines.append("### Knowledge Sources")
            for source in spec.rag_sources:
                lines.append(f"- {source.name} ({source.type}): {source.path or source.url}")
            lines.append("")

        lines.extend([
            "## Commands",
            "- **Run tests:** `pytest`",
            "- **Lint:** `ruff check .`",
            "- **Format:** `ruff format .`",
            "- **Type check:** `mypy .`",
            "- **Start dev:** `docker compose up -d`",
            "",
        ])

        return "\n".join(lines)

    def _generate_mcp_json(self, spec: ProjectSpec) -> str:
        """Generate .cursor/mcp.json with MCP server definitions."""
        mcp_config = {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
                    "env": {}
                },
                "git": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-git"],
                    "env": {}
                },
                "github": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {
                        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
                    }
                },
            }
        }

        # Add database MCP if postgres enabled
        if spec.infra.postgres.enabled:
            mcp_config["mcpServers"]["postgres"] = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-postgres"],
                "env": {
                    "POSTGRES_CONNECTION_STRING": f"postgresql://{spec.infra.postgres.user}:{spec.infra.postgres.password}@localhost:{spec.infra.postgres.port}/{spec.infra.postgres.database}"
                }
            }

        # Add memory MCP
        mcp_config["mcpServers"]["memory"] = {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-memory"],
            "env": {}
        }

        return json.dumps(mcp_config, indent=2)

    def validate_output(self, files: dict[str, str]) -> ValidationResult:
        """Validate generated Cursor configs."""
        errors = []

        # Check .cursorrules has required sections
        cursorrules = files.get(".cursorrules", "")
        required_sections = ["## Project Overview", "## Tech Stack", "## Coding Standards", "## Agent Instructions"]
        for section in required_sections:
            if section not in cursorrules:
                errors.append(f".cursorrules missing section: {section}")

        # Check .cursor/mcp.json is valid JSON
        try:
            json.loads(files.get(".cursor/mcp.json", "{}"))
        except json.JSONDecodeError as e:
            errors.append(f".cursor/mcp.json invalid JSON: {e}")

        return ValidationResult(valid=len(errors) == 0, errors=errors)
