"""
Generators package — Auto-registers all generators on import.
"""

# Import all generators to trigger @register_generator decorators
from generators import (
    base,  # noqa: F401
    cursor,  # noqa: F401
    docker_compose,  # noqa: F401
    eval_yaml,  # noqa: F401
    hermes,  # noqa: F401
    opencode,  # noqa: F401
    pipeline,  # noqa: F401
    readme,  # noqa: F401
)
from generators.base import (
    Generator,
    ValidationResult,
    get_generators_for_agents,
    get_shared_generators,
)
from generators.pipeline import GenerationResult, generate_all

__all__ = [
    "GenerationResult",
    "Generator",
    "ValidationResult",
    "generate_all",
    "get_generators_for_agents",
    "get_shared_generators",
]
