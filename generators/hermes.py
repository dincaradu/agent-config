"""
Hermes Generator — Generates AGENTS.md, memory.json, .hermes/rules.md for Hermes agent.
"""

from __future__ import annotations

from generators.base import Generator, ValidationResult, register_generator
from spec.models import AgentRole, ProjectSpec, TargetAgent


@register_generator
class HermesGenerator(Generator):
    """Generates Hermes agent configuration files."""

    @property
    def target_agents(self) -> list[TargetAgent]:
        return [TargetAgent.HERMES]

    @property
    def output_files(self) -> list[str]:
        return ["AGENTS.md", "memory.json", ".hermes/rules.md"]

    def generate(self, spec: ProjectSpec) -> dict[str, str]:
        """Generate Hermes config files from spec."""
        files = {}

        # AGENTS.md - Agent team definition
        files["AGENTS.md"] = self._generate_agents_md(spec)

        # memory.json - mem0 configuration
        files["memory.json"] = self._generate_memory_json(spec)

        # .hermes/rules.md - Project rules and conventions
        files[".hermes/rules.md"] = self._generate_rules_md(spec)

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
        if tech_stack.language != "none":
            parts.append(f"Language: {tech_stack.language.value}")
        if tech_stack.frontend != "none":
            parts.append(f"Frontend: {tech_stack.frontend.value}")
        if tech_stack.backend != "none":
            parts.append(f"Backend: {tech_stack.backend.value}")
        if tech_stack.database != "none":
            parts.append(f"Database: {tech_stack.database.value}")
        if tech_stack.orm != "none":
            parts.append(f"ORM: {tech_stack.orm.value}")
        return ", ".join(parts) if parts else "Not specified"

    def _generate_memory_json(self, spec: ProjectSpec) -> str:
        """Generate memory.json for mem0-local."""
        import json

        mem_config = {
            "version": "1.0",
            "project": spec.project_name,
            "provider": spec.memory.provider.value,
            "mem0_local": {
                "ollama_base_url": spec.memory.mem0_local.ollama_base_url,
                "embedder": {
                    "model": spec.memory.mem0_local.embedder_model,
                    "dimensions": spec.memory.mem0_local.embedder_dim,
                },
                "llm": {
                    "model": spec.memory.mem0_local.llm_model,
                },
                "vector_store": {
                    "provider": spec.memory.mem0_local.vector_store.value,
                    "url": spec.memory.mem0_local.qdrant_url,
                    "collection": spec.memory.mem0_local.collection_name,
                },
            },
            "retention": {
                "max_memories": 10000,
                "ttl_days": 365,
            },
        }

        return json.dumps(mem_config, indent=2)

    def _generate_rules_md(self, spec: ProjectSpec) -> str:
        """Generate .hermes/rules.md with project conventions."""
        lines = [
            f"# Project Rules for {spec.project_name}",
            "",
            "These rules define the coding standards and conventions for this project.",
            "All agents working on this project must follow them.",
            "",
            "---",
            "",
            "## Code Style",
            "",
            f"- **Language:** {spec.tech_stack.language.value}",
            f"- **Line Length:** {spec.conventions.line_length} characters",
            f"- **Type Hints:** {'Required' if spec.conventions.type_hints else 'Optional'}",
            f"- **Docstrings:** {spec.conventions.docstrings.title()} style",
            "- **Imports:** Organized (stdlib, third-party, local)",
            "",
            "## Error Handling",
            "",
            f"- **Strategy:** {spec.conventions.error_handling}",
            f"- **Logging:** {spec.conventions.logging_library} at {spec.conventions.log_level}",
            "- **Never:** Silent failures, bare except, print() in production",
            "",
            "## Configuration",
            "",
            f"- **Library:** {spec.conventions.config_library}",
            "- **Environment:** .env files (never committed)",
            "- **Validation:** Pydantic models for all config",
            "",
            "## Testing",
            "",
            f"- **Framework:** {spec.tech_stack.testing.value}",
            f"- **Style:** {spec.conventions.test_style}",
            f"- **Mocking:** {spec.conventions.mock_library}",
            "- **Coverage Target:** >80%",
            "- **Run:** `pytest` (or `make test`)",
            "",
            "## Git Workflow",
            "",
            f"- **Commits:** {'Conventional commits' if spec.conventions.conventional_commits else 'Descriptive messages'}",
            f"- **Branches:** {spec.conventions.branch_naming}",
            "- **PRs:** Required for all changes, must pass CI",
            "",
            "## Documentation",
            "",
            f"- **Tool:** {spec.conventions.doc_tool}",
            "- **API Docs:** Auto-generated from docstrings",
            "- **Architecture:** ADRs in docs/adr/",
            "",
            "## Agent-Specific Rules",
            "",
            "- **Context:** Always read AGENTS.md first",
            "- **Memory:** Use memory tools for cross-session context",
            "- **Tools:** Prefer built-in tools over shell commands",
            "- **Verification:** Run tests after changes",
            "",
        ]

        return "\n".join(lines)

    def validate_output(self, files: dict[str, str]) -> ValidationResult:
        """Validate generated Hermes configs."""
        errors = []

        # Check AGENTS.md has required sections
        agents_md = files.get("AGENTS.md", "")
        if "## Orchestrator Agent" not in agents_md:
            errors.append("AGENTS.md missing Orchestrator Agent section")

        # Check memory.json is valid JSON
        import json
        try:
            json.loads(files.get("memory.json", "{}"))
        except json.JSONDecodeError as e:
            errors.append(f"memory.json invalid JSON: {e}")

        return ValidationResult(valid=len(errors) == 0, errors=errors)
