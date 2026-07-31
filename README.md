# AgentConfig

> **Describe your project in natural language → Get a complete, validated, runnable agent configuration pack for your chosen agent(s) in seconds.**

AgentConfig is a **universal, agent-agnostic configuration generator** for AI coding agents. It gathers a `ProjectSpec` via conversational interview and generates all configuration files needed for any combination of target agents (Hermes, Cursor, Opencode, Claude Code, Aider, Codex, Windsurf, Zed) — including runnable infrastructure, evaluation harnesses, and memory/RAG setup.

---

## Problem

Developers using AI agents spend hours crafting configuration files for every new project:
- `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.aider.conf.yml`, `memory.json`
- `docker-compose.yml` (Ollama, Qdrant, mem0, Postgres, Redis)
- `eval.yaml` (pytest benchmarks per agent role)
- MCP configs, agent prompts, tool permissions

Existing tools (VStorm, create-ai-app, starters) generate **application scaffolds**, not **agent configurations**. They:
- Target only one agent (usually Claude Code)
- Use wizard/forms, not conversational spec gathering
- Produce output that often doesn't run (invalid YAML, missing lock files, hardcoded names)
- Don't model multi-agent teams (orchestrator + workers)
- Don't support local-first / self-hosted stacks

**Result:** Every developer hand-rolls configs, copies from gists, or gives up on agent tooling entirely.

---

## Vision

> **One conversation → Complete, validated, runnable agent config pack for any agent(s).**

---

## Target Users

| User | Pain Point | AgentConfig Value |
|------|------------|-------------------|
| Solo dev starting new project | "Which configs do I need? How do I wire Ollama + Qdrant + mem0?" | One command → complete config pack |
| Team lead onboarding agents | "Standardize agent config across 5 devs using Cursor + Hermes" | Shared `ProjectSpec` → consistent configs for all agents |
| AI Engineer evaluating agents | "I want to try Opencode but config is alien" | Select Opencode → get working config instantly |
| Consultant / agency | "New client, new stack, new agent setup every time" | Reusable `ProjectSpec` templates per client type |
| Open source maintainer | "Contributors use different agents" | Generate configs for all major agents in repo |

---

## Core Concept: The `ProjectSpec`

**Single source of truth.** Everything flows from this Pydantic model.

```python
class ProjectSpec(BaseModel):
    # ── Identity ──────────────────────────────────────────────
    project_name: str
    product_description: str
    product_type: Literal["saas", "cli", "api", "internal-tool", "mobile", "library", "data-pipeline"]
    
    # ── Tech Stack ────────────────────────────────────────────
    tech_stack: TechStack
    
    # ── Team & Agent Topology ────────────────────────────────
    team_size: int
    target_agents: list[TargetAgent]
    agent_team: AgentTeam
    
    # ── Infrastructure ────────────────────────────────────────
    local_first: bool
    hosting: HostingTarget
    infra: Infrastructure
    
    # ── Memory & Knowledge ───────────────────────────────────
    memory: MemoryConfig
    vector_store: VectorStoreConfig
    rag_sources: list[RAGSource]
    
    # ── Evaluation & Quality ─────────────────────────────────
    eval_config: EvalConfig
    
    # ── Existing Context ──────────────────────────────────────
    existing_repo_url: Optional[str]
    existing_stack_detected: Optional[DetectedStack]
    conventions: Conventions
```

See [`spec/models.py`](spec/models.py) for complete definitions.

---

## Conversational Spec Gathering (The UX Differentiator)

**Not a form. A real conversation with an AI architect.**

### The Flow (Realistic)

```
$ agent-config init

┌─────────────────────────────────────────────────────────────┐
│  "What are you building? Describe it like you're explaining  │
│   to a senior engineer who'll architect it with you.         │
│   Take your time — this isn't a race."                       │
└─────────────────────────────────────────────────────────────┘
> I want a tool that syncs Notion databases to Postgres for 
> analytics. The Notion side has messy schemas — different 
> workspaces, inconsistent property types, some databases are 
> actually views. Postgres side needs clean, typed tables 
> with proper indexes for analytical queries. It should run 
> incrementally on a schedule, handle schema drift, and give 
> me a dashboard to monitor sync health. Team of 2, we use 
> Cursor and Hermes. Prefer local-first with Ollama.

┌─────────────────────────────────────────────────────────────┐
│  "Got it. Let me dig into a few things..."                   │
│                                                              │
│  1. **Sync strategy** — Full refresh or incremental?         │
│     How do you detect changes in Notion (no webhooks)?       │
│                                                              │
│  2. **Schema mapping** — Do you want to define mappings      │
│     declaratively (YAML) or infer from Notion schema?        │
│                                                              │
│  3. **Agent workflows** — When you say "Cursor + Hermes",    │
│     what should each agent *actually do*?                    │
│     ▸ Feature agent: write sync logic, handle API quirks     │
│     ▸ Review agent: check for SQL injection, migration safety│
│     ▸ Test agent: generate contract tests for Notion API     │
│     ▸ Research agent: investigate Notion API changes         │
│     ▸ Docs agent: keep CLAUDE.md / AGENTS.md current         │
│                                                              │
│  4. **Conventions** — Any existing patterns in your team?    │
│     (error handling, logging, config management, testing)    │
│                                                              │
│  5. **Pain points to avoid** — What broke in past projects?  │
│     (rate limits, schema drift, silent failures, ...)        │
│                                                              │
│  6. **Memory needs** — Should agents remember:               │
│     ▸ Notion API quirks across sessions?                     │
│     ▸ Schema mapping decisions?                              │
│     ▸ Failed sync debug sessions?                            │
│                                                              │
│  7. **Eval criteria** — How do you know the sync works?      │
│     Row counts? Data fidelity? Latency? Cost per sync?       │
└─────────────────────────────────────────────────────────────┘
```

**This is a dialogue, not a questionnaire.** The agent:
- **Listens** to free-form description (as long as you need)
- **Identifies gaps** in the mental model
- **Asks targeted follow-ups** based on what was said
- **Proposes structure** ("Here's how I'd model the agent team...")
- **Confirms understanding** before generating
- **Writes the spec to disk** (`agent-config-spec.json` + `README.md`)
- **Initializes git** — every refinement is a commit
- **Only generates when you say "build it"**

### Three-Phase Architecture (No Time Limit)

| Phase | What Happens |
|-------|--------------|
| **1. Elicitation** | User speaks freely — as long as needed. LLM extracts entities, constraints, intent → builds `DraftSpec` with confidence scores. No rush. |
| **2. Refinement** | Iterative loops: Agent proposes structures, asks focused questions, user corrects/adds → `DraftSpec` updated → diff shown. Repeat until user says "that's it." |
| **3. Confirmation** | Final `ProjectSpec` rendered → user reviews → generates. |

**This mirrors our conversation:** hours of dialogue → written spec (README) → git repo → iterative refinement → build when ready.

### Implementation: LLM-Driven Conversation Engine

```python
# spec/conversation.py
class ConversationState(BaseModel):
    turns: list[ConversationTurn] = []
    draft_spec: Optional[ProjectSpec] = None
    confidence: dict[str, float] = Field(default_factory=dict)  # field → 0-1
    pending_questions: list[str] = []
    phase: Literal["elicitation", "refinement", "confirmation"] = "elicitation"

CONVERSATION_SYSTEM_PROMPT = """
You are a senior AI architect helping a developer specify an agent configuration.
Your goal: build a complete ProjectSpec through natural conversation.

PRINCIPLES:
- Start with open-ended listening. Let them describe the project fully.
- Extract: product, tech stack, team, agent roles, conventions, pain points, 
  infrastructure preferences, memory needs, eval criteria.
- Ask ONE focused question at a time. No questionnaires.
- Propose concrete structures: "Based on what you said, I see 3 agent roles..."
- Track confidence per field. When all > 0.8, offer to generate.
- Never assume. Clarify ambiguity: "When you say 'local-first', do you mean...?"
"""
```

```python
# spec/extractor.py
async def extract_spec_from_conversation(
    conversation: ConversationState
) -> tuple[ProjectSpec, dict[str, float]]:
    """Use LLM to extract structured spec from conversation history."""
    prompt = f"""
    Conversation history:
    {format_turns(conversation.turns)}
    
    Extract a complete ProjectSpec. Return JSON + confidence per field.
    """
    # Call LLM (Hermes/Ollama/local) → parse → validate with Pydantic
```

### CLI Modes

```bash
# Mode 1: Conversational (default) — full dialogue, writes spec, initializes git
agent-config init

# Mode 2: Spec file (CI/automation) — generate from existing spec
agent-config generate --spec-file agent-config-spec.json

# Mode 3: Hybrid — start from spec, then converse to refine
agent-config init --spec-file agent-config-spec.json

# Mode 4: Resume previous conversation in this directory
agent-config init --resume

# Mode 5: Explicit build gate — only generate, no conversation
agent-config build --spec-file agent-config-spec.json
```

### UX Principles

| Principle | Implementation |
|-----------|----------------|
| **No time pressure** | Conversation takes as long as needed — hours if that's what it takes |
| **Free-form first** | Open-ended prompt → LLM extracts structure, not user filling forms |
| **Targeted follow-ups** | One question at a time, based on gaps in extracted `DraftSpec` |
| **Propose, don't ask** | "I see 3 agent roles. Add research agent?" vs "Which roles?" |
| **Confidence tracking** | Per-field confidence → when all > 0.8, offer generation (but wait for user) |
| **Explain *why*** | "Adding review agent because teams of 2+ benefit from automated PR reviews" |
| **Spec as artifact** | `ProjectSpec` saved as `agent-config-spec.json` + `README.md` — editable, versionable, shareable |
| **Git-native** | `git init` on start — every refinement = commit, full history (see [Git Behavior](#git-behavior)) |
| **Explicit build gate** | No generation until user says "build it" |
| **Power user escape** | `--spec-file`, `--yes`, `--resume` flags for automation |

---

### Git Behavior

```
$ agent-config init
# 1. Creates project directory (or uses current)
# 2. git init (skipped if .git already exists)
# 3. Conversation starts...
# 4. On first spec draft: writes agent-config-spec.json + README.md → git add + commit "spec: initial project specification"
# 5. Each refinement: updates spec → git add + commit "refine: adjusted agent roles / added memory config / etc."
# 6. On 'build it': agent-config build → generates configs → git add + commit "build: generated configs for Hermes, Cursor, Opencode"
```

| Behavior | v0.1 Implementation |
|----------|---------------------|
| **Existing git repo** | Detect `.git` → skip `git init`, commit to current branch |
| **Commit messages** | Auto-generated with prefix: `spec:`, `refine:`, `build:` — user can `git commit --amend` |
| **Branches** | Single branch (`main`) — `--branch` flag later |
| **Remote** | Not in v0.1 — user adds manually |
| **.gitignore** | Auto-generated: Python + agent-config ignores (`.venv/`, `__pycache__/`, `agent-config-output/`, `.env*`) |

---

---

## Generator Architecture

### Registry Pattern (Extensible by Design)

```python
class Generator(ABC):
    @property @abstractmethod
    def target_agents(self) -> list[TargetAgent]: ...
    
    @property @abstractmethod
    def output_files(self) -> list[str]: ...
    
    @abstractmethod
    def generate(self, spec: ProjectSpec) -> dict[str, str]: ...
    
    def validate_output(self, files: dict[str, str]) -> ValidationResult: ...

# Agent-specific generators
class HermesGenerator(Generator):
    target_agents = [TargetAgent.HERMES]
    output_files = ["AGENTS.md", "memory.json", ".hermes/rules.md", "docker-compose.yml"]

class CursorGenerator(Generator):
    target_agents = [TargetAgent.CURSOR]
    output_files = [".cursorrules", ".cursor/mcp.json", "docker-compose.yml"]

# Shared generators (run for ALL projects)
class DockerComposeGenerator(Generator):
    target_agents = []
    output_files = ["docker-compose.yml"]
```

### Generation Pipeline

1. Collect generators matching `spec.target_agents` + shared generators
2. Generate in parallel
3. Resolve conflicts (e.g., merge `docker-compose.yml` from multiple generators)
4. Write to disk
5. Post-generation validation (`docker compose config`, syntax checks)

---

## Output Artifacts Per Agent

### Hermes
| File | Purpose |
|------|---------|
| `AGENTS.md` | Orchestrator + worker agent definitions, prompts, tool permissions, handoff rules |
| `memory.json` | mem0-local config: embedder (Ollama/nomic-embed-text), LLM (Ollama/llama3.2), Qdrant |
| `.hermes/rules.md` | Project-specific rules, conventions, coding standards |
| `.hermes/mcp.json` | MCP server definitions (filesystem, git, github, postgres, etc.) |

### Cursor
| File | Purpose |
|------|---------|
| `.cursorrules` | Project rules, conventions, agent instructions |
| `.cursor/mcp.json` | MCP servers for Cursor's agent mode |
| `.cursor/agents/` | Per-role agent definitions (feature, review, test) |

### Opencode
| File | Purpose |
|------|---------|
| `AGENTS.md` | Same format as Hermes |
| `.opencode/config.json` | Opencode-specific settings, tool config |
| `.opencode/agents/` | Agent definitions |

### Claude Code
| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project context, conventions, agent instructions |
| `.claude/settings.json` | Permissions, model, tool config |
| `.claude/agents/` | Sub-agent definitions |

### Aider
| File | Purpose |
|------|---------|
| `.aider.conf.yml` | Model, conventions, git integration |
| `CONTRIBUTING.md` | Aider reads this for context |

### Shared (Always Generated)
| File | Purpose |
|------|---------|
| `docker-compose.yml` | Ollama, Qdrant, mem0, Postgres, Redis — pre-configured, validated |
| `eval.yaml` | Pytest-based eval harness: benchmarks per agent role, thresholds |
| `eval/` | Test fixtures, custom benchmarks, CI integration |
| `README.md` | Verified run commands, agent-specific quickstarts, troubleshooting |
| `agent-config-spec.json` | The `ProjectSpec` used — for regeneration, sharing, versioning |

---

## Technical Architecture

### Project Structure (v0.1 — CLI Core)

```
agent-config/
├── spec/
│   ├── models.py          # ProjectSpec + all nested models (Pydantic v2)
│   ├── conversation.py    # ConversationState, ConversationTurn, system prompts
│   ├── extractor.py       # LLM-driven spec extraction from conversation
│   ├── questions.py       # Fallback structured questions (for --yes mode)
│   ├── validators.py      # Cross-field validation, inference rules
│   └── inference.py       # Stack detection from description / repo
├── generators/
│   ├── registry.py        # Generator registry, discovery
│   ├── pipeline.py        # Generation orchestration, conflict resolution
│   ├── base.py            # Generator ABC, validation utilities
│   ├── hermes.py          # HermesGenerator
│   ├── cursor.py          # CursorGenerator
│   ├── opencode.py        # OpencodeGenerator
│   ├── claude_code.py     # ClaudeCodeGenerator
│   ├── aider.py           # AiderGenerator
│   ├── codex.py           # CodexGenerator
│   ├── windsurf.py        # WindsurfGenerator
│   ├── zed.py             # ZedGenerator
│   ├── docker_compose.py  # DockerComposeGenerator (shared)
│   ├── eval_yaml.py       # EvalYamlGenerator (shared)
│   └── readme.py          # ReadmeGenerator (shared)
├── templates/             # Jinja2 templates per generator
│   ├── hermes/
│   ├── cursor/
│   ├── shared/
│   └── ...
├── cli.py                 # Typer app: init, generate, validate, doctor
├── validate.py            # Post-generation validation
└── __main__.py
```

### Dependencies

| Category | Packages |
|----------|----------|
| CLI/UX | `typer`, `rich`, `inquirerpy` (fallback mode) |
| Data | `pydantic`, `pydantic-settings`, `pyyaml`, `tomli-w` |
| Templates | `jinja2` |
| Validation | `docker-py` |
| LLM Client | `ollama-python` (local), `openai` (optional), `anthropic` (optional) |
| Inference | `githubkit` (optional) |
| Testing | `pytest`, `pytest-asyncio`, `pytest-mock` |

### Distribution

| Method | Command |
|--------|---------|
| pipx | `pipx install agent-config` |
| uvx | `uvx agent-config init` |
| Docker | `docker run --rm -v .:/workspace agent-config init` |
| Binary | PyInstaller / Nuitka single-file (later) |

---

## Roadmap

### Phase 0: Foundation (Week 1) — **Current**
- [ ] `spec/models.py` — complete `ProjectSpec` with all nested models
- [ ] `spec/conversation.py` — ConversationState, system prompts, turn management
- [ ] `spec/extractor.py` — LLM-driven spec extraction from conversation history
- [ ] `spec/questions.py` — Fallback structured questions (for `--yes` mode)
- [ ] `generators/registry.py` + `pipeline.py` — generator framework
- [ ] `generators/docker_compose.py` — working docker-compose.yml (Ollama, Qdrant, mem0, Postgres)
- [ ] `generators/readme.py` — README with verified commands
- [ ] `cli.py` — `agent-config init` → conversation → spec → generate → validate
- [ ] **Dogfood:** Use it to generate AgentConfig's own config

### Phase 1: Agent Generators (Week 2-3)
- [ ] `generators/hermes.py` — AGENTS.md, memory.json, .hermes/rules.md
- [ ] `generators/cursor.py` — .cursorrules, .cursor/mcp.json
- [ ] `generators/opencode.py` — AGENTS.md, .opencode/config.json
- [ ] `generators/claude_code.py` — CLAUDE.md, .claude/settings.json
- [ ] `generators/eval_yaml.py` — eval.yaml with pytest benchmarks per role
- [ ] Validation: `docker compose up` runs clean for each agent

### Phase 2: Advanced Spec Features (Week 3-4)
- [ ] `spec/inference.py` — detect stack from GitHub repo / local directory
- [ ] `spec/validators.py` — cross-field rules, warnings, suggestions
- [ ] `agent-config-spec.json` save/load/resume
- [ ] Template customization: user-provided Jinja2 overrides

### Phase 3: Web UI (Month 2)
- [ ] FastAPI backend: `/api/spec`, `/api/generate`, `/api/validate`
- [ ] Next.js frontend: conversational UI with streaming responses
- [ ] Auth (optional): save specs, share, team workspaces

### Phase 4: Ecosystem (Month 3+)
- [ ] Template marketplace: community `ProjectSpec` templates
- [ ] `agent-config analyze <repo>` — infer spec from existing codebase
- [ ] CI/CD integration: GitHub Action to validate configs on PR
- [ ] Agent-specific eval benchmarks (SWE-bench, custom)
- [ ] Plugin system for custom generators

---

## Open Questions & Decisions

| # | Question | Options | Leaning |
|---|----------|---------|---------|
| 1 | **Project name** | `agent-config`, `agentcfg`, `acfg`, `genie`, `architect`, other? | `agent-config` |
| 2 | **CLI framework** | `typer`, `click`, `argparse` | `typer` |
| 3 | **Conversation engine** | Local LLM (Ollama/Hermes), API (OpenAI/Anthropic), hybrid | Local-first (Ollama), API fallback |
| 4 | **Default local LLM** | `llama3.2:latest`, `nemotron3:latest`, `qwen2.5:7b` | `llama3.2:latest` |
| 5 | **Default embedder** | `nomic-embed-text`, `mxbai-embed-large`, `bge-m3` | `nomic-embed-text` |
| 6 | **Eval framework** | `pytest`, `vitest`, both, pluggable | `pytest` first, pluggable |
| 7 | **Config file format** | JSON only, also YAML, TOML | JSON (Pydantic native) |
| 8 | **Monorepo vs multi-package** | Single pkg, or core/cli/web split | Single package for v0.1 |
| 9 | **License** | MIT, Apache-2.0, BSD-3 | MIT |
| 10 | **Initial agents** | Hermes, Cursor, Opencode, Claude Code, Aider, Codex, Windsurf, Zed | **Hermes, Cursor, Opencode** |

---

## Success Criteria (v0.1)

| Metric | Target |
|--------|--------|
| **Conversation depth** | Handles hours-long dialogue → complete spec (like this one) |
| **Spec artifact quality** | `agent-config-spec.json` + `README.md` capture full intent |
| **Git history** | Every refinement = commit, full traceability |
| **Build gate** | Zero generation until explicit `agent-config build` |
| **Generated docker-compose** | `docker compose up -d` → all services healthy on first try |
| **Agent coverage** | 3 agents (Hermes, Cursor, Opencode) with distinct, correct configs |
| **Spec completeness** | Single `agent-config init` session captures everything needed |
| **Dogfooding** | AgentConfig's own config generated by AgentConfig |
| **Zero manual edits** | Generated files work without post-generation fixes |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Agent config formats change frequently | High | Medium | Versioned generators; auto-update check; template override system |
| Docker-compose too opinionated | Medium | High | Make infra fully configurable in `ProjectSpec.infra` |
| Conversation goes too long / scope drift | Medium | Medium | Confidence tracking + explicit build gate keeps focus; `--yes` for shortcuts |
| Scope creep | High | High | Strict phase gates; v0.1 = CLI only |
| Competitor adds conversational UI | Low | Medium | Our moat: agent-agnostic + multi-agent + local-first + eval + git-native spec |

---
---

## Getting Started

**Full usage guide:** [`USAGE.md`](USAGE.md)

```bash
# Install (when published)
pipx install agent-config
# or
uvx agent-config init

# Start a new project — conversational spec gathering
# - Free-form dialogue with AI architect
# - Writes agent-config-spec.json + README.md
# - Initializes git repo with spec history
agent-config init

# Resume conversation in existing project directory
agent-config init --resume

# Generate from existing spec (CI, automation, or after "build it")
agent-config build --spec-file agent-config-spec.json

# Validate generated configs
agent-config validate --output-dir ./agent-config-output

# Regenerate after spec changes (conversation or manual edit)
agent-config build --spec-file agent-config-spec.json --force
```

1. Fork & clone
2. `uv sync --dev`
3. `pytest` — all tests pass
4. `agent-config init` — dogfood it
5. PR with tests

---

## License

MIT — see [LICENSE](LICENSE)

---

## Related Projects

- [VStorm](https://github.com/vstorm-co/oss-website) — SaaS scaffold generator (inspiration, different category)
- [mem0](https://github.com/mem0ai/mem0) — Memory layer for AI agents
- [pydantic-ai](https://github.com/pydantic/pydantic-ai) — Agent framework used in generated configs
- [qdrant](https://qdrant.tech/) — Vector database for RAG

---

*Built with the same agents it configures.*