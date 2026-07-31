# AgentConfig Usage Guide

Complete usage instructions for AgentConfig v0.1.

---

## Quick Start

### Prerequisites

- **Python 3.12+**
- **Docker & Docker Compose** (for running generated configs)
- **Ollama** (for conversational spec gathering via `agent-config init`)

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required models
ollama pull llama3.2:latest
ollama pull gemma4:latest
ollama pull nomic-embed-text
```

### Configuration

All infrastructure URLs are configurable in the spec file:

```json
{
  "infra": {
    "ollama": {
      "enabled": true,
      "base_url": "http://your-ollama-server:11434",
      "models": ["llama3.2:latest", "gemma4:latest"],
      "default_model": "llama3.2:latest",
      "default_embed_model": "nomic-embed-text"
    },
    "qdrant": {
      "enabled": true,
      "base_url": "http://your-qdrant-server:6333",
      "host": "qdrant",
      "port": 6333
    },
    "mem0": {
      "enabled": true,
      "base_url": "http://your-mem0-server:8000",
      "provider": "mem0-local"
    },
    "postgres": {
      "enabled": true,
      "base_url": "postgresql://user:pass@your-postgres-server:5432/db",
      "host": "postgres",
      "port": 5432
    },
    "redis": {
      "enabled": false,
      "base_url": "redis://your-redis-server:6379",
      "host": "redis",
      "port": 6379
    }
  }
}
```

> **Note for Docker deployments:** When running with `docker compose up -d`, internal service communication uses Docker service names (e.g., `http://ollama:11434`, `http://qdrant:6333`). The `base_url` in the spec is used for external access and by the CLI conversation engine.

### Installation

```bash
# From source (recommended for development)
git clone https://github.com/your-org/agent-config.git
cd agent-config
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Or install from PyPI (when published)
pipx install agent-config
```

---

## Core Commands

### 1. `agent-config init` — Conversational Spec Gathering

Start a new project with guided conversation.

```bash
# New project in current directory
agent-config init

# New project in specific directory
agent-config init /path/to/my-project

# Resume previous conversation
agent-config init --resume

# Load from existing spec file
agent-config init --spec-file agent-config-spec.json

# Skip conversation, use defaults (--yes mode)
agent-config init --yes

# Use specific Ollama model
agent-config init --model llama3.2:latest
```

**What happens:**
1. Initializes git repo (if not already)
2. Starts 3-phase conversation:
   - **Elicitation**: Free-form project description
   - **Refinement**: Targeted Q&A to fill gaps
   - **Confirmation**: Review final spec → save
3. Writes `agent-config-spec.json` + `README.md`
4. Commits each refinement to git

---

### 2. `agent-config build` — Generate Configs

Generate agent configurations from spec.

```bash
# Build from spec in current directory
agent-config build

# Build from specific spec file
agent-config build --spec-file /path/to/agent-config-spec.json

# Force overwrite existing generated configs
agent-config build --force

# Build in specific project directory
agent-config build /path/to/project
```

**Output** (in `agent-config-output/`):
```
agent-config-output/
├── AGENTS.md              # Hermes/Opencode agent team
├── memory.json            # mem0-local config
├── .hermes/rules.md       # Hermes conventions
├── .cursorrules           # Cursor rules
├── .cursor/mcp.json       # Cursor MCP servers
├── .opencode/config.json  # Opencode config
├── docker-compose.yml     # Ollama, Qdrant, mem0, Postgres
├── eval.yaml              # Pytest benchmarks per role
├── eval/                  # pytest harness
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_feature_agent.py
│   └── test_review_agent.py
└── README.md              # Verified run commands
```

---

### 3. `agent-config validate` — Validate Generated Configs

```bash
# Validate configs in default output directory
agent-config validate

# Validate specific output directory
agent-config validate --output-dir ./agent-config-output
```

---

### 4. `agent-config doctor` — Environment Check

```bash
agent-config doctor
```

Checks:
- Python version
- Ollama availability
- Docker availability

---

## Conversation Flow (agent-config init)

### Phase 1: Elicitation
```
$ agent-config init

🚀 Initializing
Project: my-project
Directory: /path/to/my-project

Let's talk about your project.
Describe it like you're explaining to a senior engineer who'll architect it with you.
Take your time — this isn't a race.

What are you building?
> I want a tool that syncs Notion databases to Postgres for analytics...
```

### Phase 2: Refinement
```
Here's what I understand so far:
  Project: my-project
  Type: cli
  Description: I want a tool that syncs Notion databases...
  Target agents: hermes, cursor, opencode
  Local-first: True
  Language: python
  Backend: fastapi
  Database: postgresql

I have some questions to clarify...

What does 'done' look like for this project? How will you verify quality?
> Row counts match, data fidelity > 99%, latency < 5s per sync
```

### Phase 3: Confirmation
```
Final specification:
  Project: my-project
  Type: cli
  Target agents: hermes, cursor, opencode
  Language: python
  Backend: fastapi
  Database: postgresql
  Local-first: True

Ready to generate configs? (yes/no) [yes]:
> yes

✓ Spec saved to agent-config-spec.json
Next step: Run agent-config build to generate configs
```

---

## Using Generated Configs

### With Hermes
```bash
cd agent-config-output
# Hermes auto-loads AGENTS.md and memory.json
hermes
# Agents (orchestrator, feature, review) are ready to use
```

### With Cursor
```bash
cd agent-config-output
cursor .
# .cursorrules auto-applied
# MCP servers: filesystem, git, github, postgres, memory
# Ctrl+Shift+P > MCP to manage servers
```

### With Opencode
```bash
cd agent-config-output
opencode
# AGENTS.md loaded automatically
# Config from .opencode/config.json
```

### Start Infrastructure
```bash
cd agent-config-output
docker compose up -d
# Services: ollama (11434), qdrant (6333), mem0 (8000), postgres (5432)

# Verify
docker compose ps
```

---

## Running Evaluations

```bash
cd agent-config-output/eval
pytest -v
# Runs benchmarks per agent role:
# - feature_code_correctness
# - feature_test_coverage
# - feature_conventions
# - review_security_detection
# - review_correctness
```

---

## Resuming Work

```bash
# Resume conversation
agent-config init --resume

# Regenerate after spec changes
agent-config build --force

# Modify spec manually, then rebuild
vim agent-config-spec.json
agent-config build --force
```

---

## Project Structure

```
my-project/
├── .git/
├── .agent-config-session.json    # Conversation state
├── agent-config-spec.json        # Source spec (commit this)
├── README.md                     # Generated docs
├── agent-config-output/          # Generated configs (rebuildable)
│   ├── AGENTS.md
│   ├── memory.json
│   ├── .hermes/rules.md
│   ├── .cursorrules
│   ├── .cursor/mcp.json
│   ├── .opencode/config.json
│   ├── docker-compose.yml
│   ├── eval.yaml
│   ├── eval/
│   └── README.md
└── (your source code here)
```

---

## Configuration Reference

### Spec File (`agent-config-spec.json`)

Key fields:
```json
{
  "project_name": "my-project",
  "product_description": "What you're building",
  "product_type": "saas|cli|api|internal-tool|mobile|library|data-pipeline",
  "tech_stack": {
    "language": "python",
    "frontend": "nextjs|react|vue|svelte|htmx|none",
    "backend": "fastapi|django|flask|express|hono|go-chi|axum|none",
    "database": "postgresql|mysql|sqlite|mongodb|redis|none",
    "orm": "sqlalchemy|prisma|drizzle|gorm|sqlx|none",
    "auth": "jwt|clerk|auth0|supabase|nextauth|none",
    "testing": "pytest|vitest|jest|playwright|none",
    "ci": "github-actions|gitlab-ci|circleci|none"
  },
  "target_agents": ["hermes", "cursor", "opencode"],
  "local_first": true,
  "hosting": "self-hosted|vercel|railway|fly|k8s",
  "agent_team": {
    "orchestrator": true,
    "workers": {"feature": 1, "review": 1, "test": 1, "research": 0, "docs": 0, "deps": 0}
  }
}
```

### CLI Options

| Command | Options |
|---------|---------|
| `init` | `--spec-file`, `--resume`, `--yes`, `--model` |
| `build` | `--spec-file`, `--force` |
| `validate` | `--output-dir` |
| `doctor` | (none) |

---

## Troubleshooting

### "Ollama not installed/running"
```bash
# Install
curl -fsSL https://ollama.ai/install.sh | sh

# Start service
ollama serve

# Pull models
ollama pull llama3.2:latest
ollama pull gemma4:latest
ollama pull nomic-embed-text
```

### "Docker not running"
```bash
# Start Docker Desktop or
sudo systemctl start docker
```

### "Spec file not found"
```bash
# Run init first
agent-config init

# Or provide spec file
agent-config build --spec-file /path/to/spec.json
```

### "Generated configs don't work"
```bash
# Force rebuild
agent-config build --force

# Check validation
agent-config validate
```

### "Git commit fails"
```bash
# Check git config
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

---

## File Locations

| File | Purpose |
|------|---------|
| `agent-config-spec.json` | Source spec (version control) |
| `.agent-config-session.json` | Conversation state (gitignored) |
| `agent-config-output/` | Generated configs (rebuildable) |
| `README.md` | Project docs with quickstarts |

---

## Examples

### Example 1: SaaS Project
```bash
mkdir my-saas && cd my-saas
agent-config init
# Describe: "Multi-tenant B2B SaaS with Next.js, Postgres, Stripe..."
# Select agents: hermes, cursor
# Build: agent-config build
docker compose up -d
```

### Example 2: CLI Tool
```bash
mkdir my-cli && cd my-cli
agent-config init --yes
# Quick minimal spec
agent-config build
```

### Example 3: Resume & Iterate
```bash
agent-config init --resume
# Continue conversation
agent-config build --force
```

---

## Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Docs**: This file + `agent-config --help`

---

*Generated with AgentConfig v0.1*