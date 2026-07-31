"""
Opencode Generator — Generates AGENTS.md and .opencode/config.json for Opencode agent.
"""

from __future__ import annotations

import json

from generators.base import Generator, ValidationResult, register_generator
from spec.models import AgentRole, ProjectSpec, TargetAgent


@register_generator
class OpencodeGenerator(Generator):
    """Generates Opencode agent configuration files."""

    @property
    def target_agents(self) -> list[TargetAgent]:
        return [TargetAgent.OPENCODE]

    @property
    def output_files(self) -> list[str]:
        return ["AGENTS.md", ".opencode/config.json"]

    def generate(self, spec: ProjectSpec) -> dict[str, str]:
        """Generate Opencode config files from spec."""
        files = {}

        # AGENTS.md (same format as Hermes)
        files["AGENTS.md"] = self._generate_agents_md(spec)

        # .opencode/config.json
        files[".opencode/config.json"] = self._generate_opencode_config(spec)

        return files

    def _generate_agents_md(self, spec: ProjectSpec) -> str:
        """Generate AGENTS.md with orchestrator and worker agents."""
        lines = [
            f"# Agent Team Configuration for {spec.project_name}",
            "",
            f"**Product:** {spec.product_description}",
            f"**Type:** {spec.product_type.value}",
            f"**Team Size:** {spec.team_size}",
            f"**Generated:** {spec.updated_at.isoformat()}",
            "",
            "---",
            "",
        ]

        # Orchestrator
        if spec.agent_team.orchestrator:
            lines.extend([
                "## Orchestrator Agent",
                "",
                "**Role:** Central coordinator that decomposes tasks and delegates to workers",
                f"**Model:** {spec.infra.ollama.default_model}",
                "**Tools:** All available tools",
                "**Prompt:**",
                "```",
                f"You are the orchestrator for {spec.project_name}.",
                "",
                f"Product: {spec.product_description}",
                f"Tech Stack: {self._format_tech_stack(spec.tech_stack)}",
                "",
                "Your job:",
                "1. Understand the user's request",
                "2. Break it down into subtasks",
                "3. Delegate to appropriate worker agents",
                "4. Coordinate and integrate results",
                "5. Report back to user",
                "",
                f"Available workers: {', '.join(r.value for r in spec.agent_team.workers.keys())}",
                "```",
                "",
            ])

        # Worker agents
        for role, count in spec.agent_team.workers.items():
            for i in range(count):
                agent_name = f"{role.value}-{i+1}" if count > 1 else role.value
                lines.extend(self._generate_worker_agent(spec, role, agent_name))

        return "\n".join(lines)

    def _generate_worker_agent(self, spec: ProjectSpec, role: AgentRole, name: str) -> list[str]:
        """Generate a worker agent definition."""
        role_prompts = {
            AgentRole.FEATURE: (
                f"You are a feature development agent for {spec.project_name}.\n"
                f"Write clean, tested, production-ready code.\n"
                f"Follow project conventions: {spec.conventions.docstrings} docstrings, "
                f"{spec.conventions.line_length} char lines, {spec.conventions.error_handling} for errors.\n"
                f"Tech stack: {self._format_tech_stack(spec.tech_stack)}"
            ),
            AgentRole.REVIEW: (
                f"You are a code review agent for {spec.project_name}.\n"
                f"Focus on: security, correctness, maintainability, performance.\n"
                f"Check for: SQL injection, XSS, race conditions, memory leaks, "
                f"proper error handling, test coverage.\n"
                f"Tech stack: {self._format_tech_stack(spec.tech_stack)}"
            ),
            AgentRole.TEST: (
                f"You are a test generation agent for {spec.project_name}.\n"
                f"Generate comprehensive tests: unit, integration, contract.\n"
                f"Framework: {spec.tech_stack.testing.value}\n"
                f"Target: >80% coverage, edge cases, error paths.\n"
                f"Tech stack: {self._format_tech_stack(spec.tech_stack)}"
            ),
            AgentRole.RESEARCH: (
                f"You are a research agent for {spec.project_name}.\n"
                f"Investigate: API changes, library updates, best practices, alternatives.\n"
                f"Provide: summaries, recommendations, code examples.\n"
                f"Tech stack: {self._format_tech_stack(spec.tech_stack)}"
            ),
            AgentRole.DOCS: (
                f"You are a documentation agent for {spec.project_name}.\n"
                f"Maintain: README, API docs, architecture decisions, runbooks.\n"
                f"Style: {spec.conventions.doc_tool}, {spec.conventions.docstrings} docstrings.\n"
                f"Tech stack: {self._format_tech_stack(spec.tech_stack)}"
            ),
            AgentRole.DEPS: (
                f"You are a dependency management agent for {spec.project_name}.\n"
                f"Monitor: security advisories, version updates, breaking changes.\n"
                f"Generate: PRs with updates, migration notes, test results.\n"
                f"Package manager: {spec.tech_stack.package_manager.value}"
            ),
        }

        return [
            f"## {name.title()} Agent ({role.value})",
            "",
            f"**Role:** {role.value.title()} development",
            f"**Model:** {spec.infra.ollama.default_model}",
            "**Tools:** Code tools, file system, git, terminal",
            "**Prompt:**",
            "```",
            role_prompts.get(role, f"You are a {role.value} agent for {spec.project_name}."),
            "```",
            "",
        ]

    def _format_tech_stack(self, tech_stack) -> str:
        """Format tech stack for prompts."""
        parts = []
        if tech_stack.language.value != "none":
            parts.append(f"Language: {tech_stack.language.value}")
        if tech_stack.frontend.value != "none":
            parts.append(f"Frontend: {tech_stack.frontend.value}")
        if tech_stack.backend.value != "none":
            parts.append(f"Backend: {tech_stack.backend.value}")
        if tech_stack.database.value != "none":
            parts.append(f"Database: {tech_stack.database.value}")
        if tech_stack.orm.value != "none":
            parts.append(f"ORM: {tech_stack.orm.value}")
        return ", ".join(parts) if parts else "Not specified"

    def _generate_opencode_config(self, spec: ProjectSpec) -> str:
        """Generate .opencode/config.json."""
        config = {
            "version": "1.0",
            "project": spec.project_name,
            "model": spec.infra.ollama.default_model,
            "provider": "ollama",
            "ollama": {
                "base_url": spec.infra.ollama.base_url,
                "model": spec.infra.ollama.default_model,
            },
            "agents": {
                "orchestrator": {
                    "enabled": spec.agent_team.orchestrator,
                    "model": spec.infra.ollama.default_model,
                }
            },
            "tools": {
                "read": True,
                "write": True,
                "edit": True,
                "bash": True,
                "grep": True,
                "glob": True,
                "task": True,
                "webfetch": True,
            },
            "permissions": {
                "read": ["**/*"],
                "write": ["**/*"],
                "bash": ["*"],
            },
            "memory": {
                "enabled": spec.memory.provider != "none",
                "provider": spec.memory.provider.value,
                "mem0": {
                    "url": spec.memory.mem0_local.qdrant_url,
                    "collection": spec.memory.mem0_local.collection_name,
                } if spec.memory.provider == "mem0-local" else None,
            },
        }

        # Add worker agents
        for role, count in spec.agent_team.workers.items():
            for i in range(count):
                agent_name = f"{role.value}-{i+1}" if count > 1 else role.value
                config["agents"][agent_name] = {
                    "enabled": True,
                    "model": spec.infra.ollama.default_model,
                    "role": role.value,
                }

        # Remove None values
        config = self._remove_none(config)

        return json.dumps(config, indent=2)

    def _remove_none(self, obj):
        """Recursively remove None values from dict."""
        if isinstance(obj, dict):
            return {k: self._remove_none(v) for k, v in obj.items() if v is not None}
        elif isinstance(obj, list):
            return [self._remove_none(v) for v in obj if v is not None]
        return obj

    def validate_output(self, files: dict[str, str]) -> ValidationResult:
        """Validate generated Opencode configs."""
        errors = []

        # Check AGENTS.md has required sections
        agents_md = files.get("AGENTS.md", "")
        if "## Orchestrator Agent" not in agents_md:
            errors.append("AGENTS.md missing Orchestrator Agent section")

        # Check .opencode/config.json is valid JSON
        try:
            json.loads(files.get(".opencode/config.json", "{}"))
        except json.JSONDecodeError as e:
            errors.append(f".opencode/config.json invalid JSON: {e}")

        return ValidationResult(valid=len(errors) == 0, errors=errors)
