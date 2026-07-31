"""
AgentConfig CLI — Main entry point.

Commands:
    init       Start conversational spec gathering
    build      Generate configs from existing spec
    validate   Validate generated configs
    doctor     Check environment and dependencies
"""

import asyncio
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from spec import (
    ConversationState,
    ConversationPhase,
    CONVERSATION_SYSTEM_PROMPT,
    extract_spec_from_conversation,
    merge_spec_data,
    ProjectSpec,
)

app = typer.Typer(
    name="agent-config",
    help="Universal AI agent configuration generator",
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()


def get_project_dir(project_dir: str | None = None) -> Path:
    """Get project directory, create if needed."""
    path = Path(project_dir).resolve() if project_dir else Path.cwd()
    path.mkdir(parents=True, exist_ok=True)
    return path


def init_git_repo(project_dir: Path) -> bool:
    """Initialize git repo if not already initialized."""
    import git

    git_dir = project_dir / ".git"
    if git_dir.exists():
        console.print("[dim]Git repo already exists, using existing[/dim]")
        return False

    try:
        repo = git.Repo.init(project_dir)
        # Create .gitignore
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
env/
.pytest_cache/
.mypy_cache/
.ruff_cache/

# Agent-config
agent-config-output/
agent-config-spec.json
*.log

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""
        (project_dir / ".gitignore").write_text(gitignore_content)

        # Initial commit
        repo.index.add([".gitignore"])
        repo.index.commit("chore: initial commit with .gitignore")
        console.print("[green]✓[/green] Git repository initialized")
        return True
    except Exception as e:
        console.print(f"[yellow]Warning: Could not initialize git: {e}[/yellow]")
        return False


def commit_spec(project_dir: Path, message: str) -> bool:
    """Commit spec changes to git."""
    import git

    try:
        repo = git.Repo(project_dir)
        spec_file = project_dir / "agent-config-spec.json"
        readme_file = project_dir / "README.md"

        files_to_add = []
        if spec_file.exists():
            files_to_add.append("agent-config-spec.json")
        if readme_file.exists():
            files_to_add.append("README.md")

        if files_to_add:
            repo.index.add(files_to_add)
            repo.index.commit(message)
            console.print(f"[dim]Git commit: {message}[/dim]")
            return True
    except Exception as e:
        console.print(f"[yellow]Warning: Could not commit: {e}[/yellow]")
    return False


def save_conversation(state: ConversationState, project_dir: Path) -> None:
    """Save conversation state to disk."""
    if state.project_dir is None:
        state.project_dir = project_dir
    session_file = state.project_dir / ".agent-config-session.json"
    session_file.write_text(json.dumps(state.to_json(), indent=2, default=str))


def load_conversation(project_dir: Path) -> ConversationState | None:
    """Load conversation state from disk."""
    session_file = project_dir / ".agent-config-session.json"
    if not session_file.exists():
        return None
    data = json.loads(session_file.read_text())
    state = ConversationState.from_json(data)
    state.project_dir = project_dir
    return state


async def run_conversation(
    state: ConversationState,
    project_dir: Path,
    ollama_model: str = "llama3.2:latest",
) -> ConversationState:
    """Run the conversational spec elicitation loop."""
    
    # Initialize Ollama client with configurable URL
    import ollama
    ollama_base_url = "http://ollama:11434"
    if state.draft_spec and state.draft_spec.infra.ollama.enabled:
        ollama_base_url = state.draft_spec.infra.ollama.base_url
    ollama_client = ollama.AsyncClient(host=ollama_base_url)
    
    # Phase 1: Elicitation - open-ended description
    if state.phase == ConversationPhase.ELICITATION:
        console.print("\n[bold]Let's talk about your project.[/bold]")
        console.print("Describe it like you're explaining to a senior engineer who'll architect it with you.")
        console.print("Take your time — this isn't a race.\n")
        
        # Get initial description if not set
        if not state.draft_spec or not state.draft_spec.product_description:
            description = Prompt.ask(
                "[cyan]What are you building?[/cyan]",
                default="",
            )
            if description:
                state.add_turn("user", description)
                project_name = state.project_dir.name if state.project_dir else "project"
                state.draft_spec = state.draft_spec or ProjectSpec(
                    project_name=project_name,
                    product_description=description,
                )
        
        # Extract initial spec
        extraction = await extract_spec_from_conversation(state, ollama_client)
        base_spec = state.draft_spec or ProjectSpec(project_name="project", product_description="")
        state.draft_spec = merge_spec_data(
            base_spec,
            extraction.spec_data,
            extraction.confidence,
        )
        state.confidence.update(extraction.confidence)
        state.pending_questions = extraction.next_questions
        state.phase = ConversationPhase.REFINEMENT
        
        # Show extracted understanding
        console.print("\n[bold]Here's what I understand so far:[/bold]")
        if state.draft_spec:
            _show_spec_summary(state.draft_spec)
        
        if extraction.next_questions:
            console.print("\n[dim]I have some questions to clarify...[/dim]")
    
    # Phase 2: Refinement - iterative Q&A
    while state.phase == ConversationPhase.REFINEMENT:
        # Check if we're confident enough
        if state.draft_spec and state.draft_spec.all_confident(0.8) and not state.pending_questions:
            console.print("\n[green]I have a clear picture of your project.[/green]")
            state.phase = ConversationPhase.CONFIRMATION
            break
        
        # Ask next question
        if state.pending_questions:
            question = state.pending_questions.pop(0)
        else:
            # Generate a question based on gaps
            question = _generate_followup_question(state.draft_spec)
        
        console.print(f"\n[cyan]{question}[/cyan]")
        answer = Prompt.ask("[bold]Your answer[/bold]", default="")
        
        if not answer.strip():
            console.print("[yellow]Skipping...[/yellow]")
            continue
        
        state.add_turn("assistant", question)
        state.add_turn("user", answer)
        
        # Re-extract with new info
        extraction = await extract_spec_from_conversation(state, ollama_client)
        state.draft_spec = merge_spec_data(state.draft_spec, extraction.spec_data, extraction.confidence)
        state.confidence.update(extraction.confidence)
        state.pending_questions = extraction.next_questions
        
        # Show updated understanding
        console.print("\n[bold]Updated understanding:[/bold]")
        if state.draft_spec:
            _show_spec_summary(state.draft_spec)
        
        # Save progress
        state.updated_at = datetime.utcnow()
        if state.project_dir:
            save_conversation(state, state.project_dir)
            commit_spec(state.project_dir, f"refine: {question[:50]}")
    
    # Phase 3: Confirmation
    if state.phase == ConversationPhase.CONFIRMATION:
        console.print("\n[bold]Final specification:[/bold]")
        if state.draft_spec:
            _show_spec_summary(state.draft_spec)
        
        confirm = Prompt.ask(
            "\n[bold]Ready to generate configs?[/bold] (yes/no)",
            choices=["yes", "no"],
            default="yes",
        )
        
        if confirm == "yes":
            # Save final spec
            if state.project_dir:
                spec_path = state.project_dir / "agent-config-spec.json"
                if state.draft_spec:
                    state.draft_spec.to_json_file(str(spec_path))
                save_conversation(state, state.project_dir)
                commit_spec(state.project_dir, "spec: finalized project specification")
                console.print(f"\n[green]✓[/green] Spec saved to [bold]{spec_path}[/bold]")
                console.print("\nNext step: Run [bold]agent-config build[/bold] to generate configs")
            else:
                console.print("[yellow]Error: project_dir not set[/yellow]")
        else:
            console.print("[yellow]Specification saved. Resume anytime with --resume[/yellow]")
    
    return state


def _show_spec_summary(spec: ProjectSpec) -> None:
    """Display a readable summary of the current spec."""
    console.print(f"  Project: [green]{spec.project_name}[/green]")
    console.print(f"  Type: {spec.product_type.value}")
    console.print(f"  Description: {spec.product_description[:100]}..." if len(spec.product_description) > 100 else f"  Description: {spec.product_description}")
    console.print(f"  Target agents: {', '.join(a.value for a in spec.target_agents)}")
    console.print(f"  Local-first: {spec.local_first}")
    console.print(f"  Language: {spec.tech_stack.language.value}")
    if spec.tech_stack.frontend.value != "none":
        console.print(f"  Frontend: {spec.tech_stack.frontend.value}")
    if spec.tech_stack.backend.value != "none":
        console.print(f"  Backend: {spec.tech_stack.backend.value}")
    if spec.tech_stack.database.value != "none":
        console.print(f"  Database: {spec.tech_stack.database.value}")
    
    # Show confidence
    low_confidence = [f for f, c in spec._confidence.items() if c < 0.8]
    if low_confidence:
        console.print(f"  [yellow]Low confidence:[/yellow] {', '.join(low_confidence)}")


def _generate_followup_question(spec: ProjectSpec) -> str:
    """Generate a contextual follow-up question based on spec gaps."""
    questions = []
    
    if spec.tech_stack.frontend.value == "none" and spec.product_type.value in ["saas", "mobile"]:
        questions.append("What frontend framework would you like? (Next.js, React, Vue, etc.)")
    
    if spec.tech_stack.database.value == "none" and spec.product_type.value != "cli":
        questions.append("What database? (PostgreSQL, MySQL, SQLite, etc.)")
    
    if not spec.agent_team.workers.get("test") and not spec.agent_team.workers.get("research"):
        questions.append("Would you like a test generation agent or research agent?")
    
    if not spec.eval_config.benchmarks:
        questions.append("What does 'done' look like for this project? How will you verify quality?")
    
    if not spec.rag_sources:
        questions.append("Any existing docs, code, or APIs the agents should know about?")
    
    return questions[0] if questions else "Anything else you'd like to add or clarify?"


@app.command()
def init(
    project_dir: str | None = typer.Argument(None, help="Project directory (default: current)"),
    spec_file: str | None = typer.Option(None, "--spec-file", "-s", help="Start from existing spec file"),
    resume: bool = typer.Option(False, "--resume", "-r", help="Resume previous conversation in this directory"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Accept all defaults, skip conversation"),
    ollama_model: str = typer.Option("llama3.2:latest", "--model", "-m", help="Ollama model to use"),
):
    """
    Start conversational spec gathering for a new project.
    
    This is the main entry point. You'll have a natural conversation with an AI architect
    to describe your project, then refine the specification until you're ready to build.
    """
    project_path = get_project_dir(project_dir)
    
    console.print(Panel.fit(
        f"[bold cyan]AgentConfig v0.1[/bold cyan]\n"
        f"Project: [green]{project_path.name}[/green]\n"
        f"Directory: {project_path}",
        title="🚀 Initializing",
        border_style="cyan",
    ))
    
    # Initialize git
    init_git_repo(project_path)
    
    # Load or create conversation state
    state = None
    
    if spec_file:
        spec = ProjectSpec.from_json_file(spec_file)
        state = ConversationState(
            draft_spec=spec,
            project_dir=project_path,
            phase=ConversationPhase.REFINEMENT,
            session_id=str(uuid.uuid4())[:8],
        )
        console.print(f"[green]Loaded spec from {spec_file}[/green]")
    elif resume:
        state = load_conversation(project_path)
        if state:
            state.project_dir = project_path
            console.print(f"[green]Resumed conversation from {project_path}[/green]")
        else:
            console.print("[yellow]No previous conversation found. Starting fresh.[/yellow]")
    
    if state is None:
        # New project
        state = ConversationState(
            draft_spec=ProjectSpec(
                project_name=project_path.name,
                product_description="",
            ),
            project_dir=project_path,
            phase=ConversationPhase.ELICITATION,
            session_id=str(uuid.uuid4())[:8],
        )
    
    if yes:
        console.print("[yellow]--yes mode: using defaults for unspecified fields[/yellow]")
        # TODO: implement structured questions mode
        spec_path = project_path / "agent-config-spec.json"
        state.draft_spec = state.draft_spec or ProjectSpec(
            project_name=project_path.name,
            product_description="A project configured with AgentConfig",
        )
        state.draft_spec.to_json_file(str(project_path / "agent-config-spec.json"))
        commit_spec(project_path, "spec: initial project specification (--yes mode)")
        console.print(f"\n[green]✓[/green] Spec saved (minimal). Run [bold]agent-config build[/bold] to generate.")
        return
    
    # Run the conversation (async)
    console.print("\n[dim]Starting conversation engine...[/dim]")
    state = asyncio.run(run_conversation(state, project_path, ollama_model))
    
    console.print(f"\n[dim]Session: {state.session_id}[/dim]")
    console.print("Resume anytime with: [bold]agent-config init --resume[/bold]")


@app.command()
def build(
    project_dir: str | None = typer.Argument(None, help="Project directory (default: current)"),
    spec_file: str | None = typer.Option(None, "--spec-file", "-s", help="Spec file to use"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing generated configs"),
):
    """
    Generate agent configurations from spec.
    
    This is the explicit build gate — no generation happens until you run this.
    """
    from generators.pipeline import generate_all
    
    project_path = get_project_dir(project_dir)
    
    spec_path = Path(spec_file) if spec_file else project_path / "agent-config-spec.json"
    
    if not spec_path.exists():
        console.print(f"[red]Spec file not found: {spec_path}[/red]")
        console.print("Run [bold]agent-config init[/bold] first, or provide --spec-file")
        raise typer.Exit(1)
    
    spec = ProjectSpec.from_json_file(str(spec_path))
    
    console.print(Panel.fit(
        f"[bold]Generating configs for:[/bold] {spec.project_name}\n"
        f"Target agents: {', '.join(a.value for a in spec.target_agents)}",
        title="🔨 Building",
        border_style="green",
    ))
    
    output_dir = project_path / "agent-config-output"
    result = generate_all(spec, output_dir, force=force)
    
    if result.success:
        console.print(f"\n[green]✓[/green] Generated {len(result.files_generated)} files to [bold]{output_dir}[/bold]")
        for f in result.files_generated:
            console.print(f"  • {f}")
        if result.warnings:
            for w in result.warnings:
                console.print(f"  [yellow]⚠[/yellow] {w}")
        
        # Commit
        try:
            import git
            repo = git.Repo(project_path)
            repo.index.add([str(output_dir / f) for f in result.files_generated])
            repo.index.commit(f"build: generated configs for {', '.join(a.value for a in spec.target_agents)}")
            console.print("[dim]Git commit: build[/dim]")
        except Exception:
            pass
    else:
        console.print("[red]Generation failed:[/red]")
        for e in result.errors:
            console.print(f"  • {e}")
        raise typer.Exit(1)


@app.command()
def validate(
    project_dir: str | None = typer.Argument(None, help="Project directory (default: current)"),
    output_dir: str | None = typer.Option(None, "--output-dir", "-o", help="Output directory to validate"),
):
    """Validate generated configurations."""
    console.print("[yellow]Validate command not yet implemented[/yellow]")


@app.command()
def doctor():
    """Check environment and dependencies."""
    console.print(Panel.fit(
        "[bold]Environment Check[/bold]",
        title="🩺 Doctor",
        border_style="blue",
    ))
    
    checks = [
        ("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"),
        ("Platform", sys.platform),
        ("Working Dir", str(Path.cwd())),
    ]
    
    for name, value in checks:
        console.print(f"  {name}: [green]{value}[/green]")
    
    # Check Ollama
    import subprocess
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            console.print("  Ollama: [green]Available[/green]")
        else:
            console.print("  Ollama: [yellow]Not running[/yellow]")
    except FileNotFoundError:
        console.print("  Ollama: [red]Not installed[/red]")
    except Exception:
        console.print("  Ollama: [yellow]Error checking[/yellow]")
    
    # Check Docker
    try:
        result = subprocess.run(["docker", "version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            console.print("  Docker: [green]Available[/green]")
        else:
            console.print("  Docker: [yellow]Not running[/yellow]")
    except FileNotFoundError:
        console.print("  Docker: [red]Not installed[/red]")


if __name__ == "__main__":
    app()