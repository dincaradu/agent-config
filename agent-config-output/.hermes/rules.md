# Project Rules for test-project

These rules define the coding standards and conventions for this project.
All agents working on this project must follow them.

---

## Code Style

- **Language:** python
- **Line Length:** 100 characters
- **Type Hints:** Required
- **Docstrings:** Google style
- **Imports:** Organized (stdlib, third-party, local)

## Error Handling

- **Strategy:** exceptions
- **Logging:** structlog at INFO
- **Never:** Silent failures, bare except, print() in production

## Configuration

- **Library:** pydantic-settings
- **Environment:** .env files (never committed)
- **Validation:** Pydantic models for all config

## Testing

- **Framework:** pytest
- **Style:** pytest
- **Mocking:** pytest-mock
- **Coverage Target:** >80%
- **Run:** `pytest` (or `make test`)

## Git Workflow

- **Commits:** Conventional commits
- **Branches:** type/scope-description
- **PRs:** Required for all changes, must pass CI

## Documentation

- **Tool:** mkdocs
- **API Docs:** Auto-generated from docstrings
- **Architecture:** ADRs in docs/adr/

## Agent-Specific Rules

- **Context:** Always read AGENTS.md first
- **Memory:** Use memory tools for cross-session context
- **Tools:** Prefer built-in tools over shell commands
- **Verification:** Run tests after changes
