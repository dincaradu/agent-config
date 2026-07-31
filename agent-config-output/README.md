# test-project

**A test project for agent configuration generation with enough characters to pass validation**

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.12+ (for local development)

### Start Development Environment
```bash
docker compose up -d
```

This starts:
- Ollama (LLM) at http://ollama:11434
- Qdrant (Vector DB) at http://qdrant:6333
- mem0 (Memory) at http://mem0:8000
- PostgreSQL at postgresql://postgres:postgres@postgres:5432/agent_config

### Verify Services
```bash
docker compose ps
```

All services should show `healthy` or `running`.

---

## Hermes

### Config Files
- `AGENTS.md` — Agent team (orchestrator + workers)
- `memory.json` — mem0-local configuration
- `.hermes/rules.md` — Project rules & conventions

### Usage
```bash
# In Hermes, the agents are auto-loaded from AGENTS.md
# Just start a conversation and they'll use the configuration
```

## Cursor

### Config Files
- `.cursorrules` — Project rules for Cursor's AI
- `.cursor/mcp.json` — MCP server definitions

### Usage
```bash
# Open in Cursor: cursor .
# The rules are auto-applied to Cursor's agent mode
# MCP servers available via Ctrl+Shift+P > MCP
```

## Opencode

### Config Files
- `AGENTS.md` — Agent team (same format as Hermes)
- `.opencode/config.json` — Opencode settings

### Usage
```bash
# Run: opencode
# Agents from AGENTS.md are auto-loaded
```

---

## Project Structure

```
test-project/
├── AGENTS.md              # Agent team configuration (Hermes, Opencode)
├── memory.json          # mem0 configuration
├── .hermes/rules.md     # Hermes-specific rules
├── .cursorrules         # Cursor rules
├── .cursor/mcp.json     # Cursor MCP servers
├── .opencode/config.json # Opencode configuration
├── docker-compose.yml   # Infrastructure
├── eval.yaml            # Evaluation harness config
├── eval/                # Pytest benchmarks
├── agent-config-spec.json # Source specification
└── README.md            # This file
```

---

## Evaluation

Run the evaluation harness to verify agent quality:

```bash
cd eval && pytest -v
```

Benchmarks defined in `eval.yaml` with thresholds per agent role.

---

## Configuration

This project was configured with [AgentConfig](https://github.com/your-org/agent-config).

Source spec: `agent-config-spec.json`

To regenerate configs after changes:

```bash
agent-config build --spec-file agent-config-spec.json --force
```

---

## Tech Stack

- **Language:** python
- **Backend:** fastapi
- **Database:** postgresql
- **ORM:** sqlalchemy
- **Auth:** jwt
- **Testing:** pytest
- **CI:** github-actions

---

*Generated with AgentConfig v0.1*