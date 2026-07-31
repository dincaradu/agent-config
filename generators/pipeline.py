"""
Generation Pipeline — Orchestrates generators, resolves conflicts, writes output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from generators.base import (
    get_generators_for_agents,
    get_shared_generators,
)
from spec.models import ProjectSpec


@dataclass
class GenerationResult:
    """Result of the generation pipeline."""
    success: bool
    files_generated: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def generate_all(spec: ProjectSpec, output_dir: Path, force: bool = False) -> GenerationResult:
    """
    Run the complete generation pipeline.
    
    1. Collect agent-specific generators + shared generators
    2. Generate files from each
    3. Resolve conflicts (e.g., merge docker-compose.yml)
    4. Validate all output
    5. Write to disk
    """
    result = GenerationResult(success=True)

    # 1. Collect generators
    agent_generators = get_generators_for_agents(spec.target_agents)
    shared_generators = get_shared_generators()
    all_generators = agent_generators + shared_generators

    print(f"Running {len(all_generators)} generators...")
    for gen in all_generators:
        print(f"  - {gen.__class__.__name__}: {', '.join(gen.output_files)}")

    # 2. Generate files from each generator
    all_files: dict[str, str] = {}
    generator_sources: dict[str, str] = {}  # filename -> generator name

    for gen in all_generators:
        try:
            files = gen.generate(spec)

            # Validate this generator's output
            validation = gen.validate_output(files)
            if not validation.valid:
                result.success = False
                result.errors.extend([f"{gen.__class__.__name__}: {e}" for e in validation.errors])
            if validation.warnings:
                result.warnings.extend([f"{gen.__class__.__name__}: {w}" for w in validation.warnings])

            # Track conflicts
            for filename in files:
                if filename in all_files:
                    # Conflict! We'll resolve in step 3
                    if filename not in generator_sources:
                        generator_sources[filename] = gen.__class__.__name__
                    generator_sources[filename] += f", {gen.__class__.__name__}"
                else:
                    generator_sources[filename] = gen.__class__.__name__
                all_files[filename] = files[filename]

        except Exception as e:
            result.success = False
            result.errors.append(f"{gen.__class__.__name__} failed: {e}")

    # 3. Resolve conflicts
    if "docker-compose.yml" in all_files:
        # Multiple generators produce docker-compose.yml - they should be compatible
        # For now, DockerComposeGenerator is the only one that should produce it
        # But if others do, we'd merge here
        pass

    # 4. Write to disk
    if result.success:
        output_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in all_files.items():
            file_path = output_dir / filename
            if file_path.exists() and not force:
                result.warnings.append(f"Skipping existing file: {filename} (use --force to overwrite)")
                continue
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            result.files_generated.append(filename)
            print(f"  Generated: {filename}")

    return result
