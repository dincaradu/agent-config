"""
AgentConfig CLI — Main entry point.

Commands:
    init       Start conversational spec gathering
    build      Generate configs from existing spec
    validate   Validate generated configs
    doctor     Check environment and dependencies
"""

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from spec.models import ProjectSpec

app = typer.Typer(
    name="agent-config",
    help="Universal AI agent configuration generator",
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()


def get_project_dir(project_dir: str | None = None) -> Path:
    """Get project directory, create if needed."""
    if project_dir:
        path = Path(project_dir).resolve()
    else:
        path = Path.cwd()
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


@app.command()
def init(
    project_dir: str | None = typer.Argument(None, help="Project directory (default: current)"),
    spec_file: str | None = typer.Option(None, "--spec-file", "-s", help="Start from existing spec file"),
    resume: bool = typer.Option(False, "--resume", "-r", help="Resume previous conversation in this directory"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Accept all defaults, skip conversation"),
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

    # Load existing spec if provided or resuming
    spec = None
    spec_path = project_path / "agent-config-spec.json"

    if spec_file:
        spec = ProjectSpec.from_json_file(str(spec_file))
        console.print(f"[green]Loaded spec from {spec_file}[/green]")
    elif resume and spec_path.exists():
        spec = ProjectSpec.from_json_file(spec_path)
        console.print(f"[green]Resumed conversation from {spec_path}[/green]")

    if spec is None:
        # New project - start with minimal spec
        spec = ProjectSpec(
            project_name=project_path.name,
            product_description="",
            product_type=ProjectSpec.model_fields["product_type"].default,
        )

    if yes:
        # TODO: Implement --yes mode with structured questions
        console.print("[yellow]--yes mode not yet implemented[/yellow]")
        raise typer.Exit(1)

    # Start conversation
    console.print("\n[bold]Let's talk about your project.[/bold]")
    console.print("Describe it like you're explaining to a senior engineer who'll architect it with you.")
    console.print("Take your time — this isn't a race.\n")

    # Get product description
    if not spec.product_description:
        description = Prompt.ask(
            "[cyan]What are you building?[/cyan]",
            default=spec.product_description or "",
        )
        spec.product_description = description

    # TODO: Implement full LLM-driven conversation engine
    # For now, collect basic fields interactively

    # Project type
    console.print("\n[cyan]Project type:[/cyan]")
    for i, pt in enumerate(ProjectSpec.model_fields["product_type"].default.__class__, 1):
        console.print(f"  {i}. {pt.value}")

    # Save spec
    spec.to_json_file(str(spec_path))
    commit_spec(project_path, "spec: initial project specification")

    console.print(f"\n[green]✓[/green] Spec saved to [bold]{spec_path}[/bold]")
    console.print("\nNext steps:")
    console.print("  • Run [bold]agent-config init --resume[/bold] to continue refining")
    console.print("  • Run [bold]agent-config build[/bold] when ready to generate configs")


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
