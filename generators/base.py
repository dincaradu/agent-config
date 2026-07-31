"""
Generator base classes and registry.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from spec.models import ProjectSpec, TargetAgent


@dataclass
class ValidationResult:
    """Result of output validation."""
    valid: bool
    errors: list[str] | None = None
    warnings: list[str] | None = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class Generator(ABC):
    """Base generator protocol."""

    @property
    @abstractmethod
    def target_agents(self) -> list[TargetAgent]:
        """Which agents this generator produces configs for. Empty = all agents."""
        ...

    @property
    @abstractmethod
    def output_files(self) -> list[str]:
        """Filenames this generator produces."""
        ...

    @abstractmethod
    def generate(self, spec: ProjectSpec) -> dict[str, str]:
        """Generate files from spec. Returns filename -> content mapping."""
        ...

    def validate_output(self, files: dict[str, str]) -> ValidationResult:
        """Validate generated output. Override for custom validation."""
        return ValidationResult(valid=True)

    def write_files(self, files: dict[str, str], output_dir: Path) -> None:
        """Write generated files to output directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in files.items():
            file_path = output_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)


# Registry of all generators
_ALL_GENERATORS: list[type[Generator]] = []


def register_generator(generator_class: type[Generator]) -> type[Generator]:
    """Decorator to register a generator class."""
    _ALL_GENERATORS.append(generator_class)
    return generator_class


def get_generators_for_agents(target_agents: list[TargetAgent]) -> list[Generator]:
    """Get all generators matching the target agents."""
    instances = []
    for gen_class in _ALL_GENERATORS:
        instance = gen_class()
        if not instance.target_agents or any(a in target_agents for a in instance.target_agents):
            instances.append(instance)
    return instances


def get_shared_generators() -> list[Generator]:
    """Get generators that run for all projects (empty target_agents)."""
    return [gen_class() for gen_class in _ALL_GENERATORS if not gen_class().target_agents]
