"""
Pytest configuration for AgentConfig evaluation harness.
Project: test-project
"""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def project_spec():
    """Load the project spec for testing."""
    import json
    spec_path = Path(__file__).parent.parent / "agent-config-spec.json"
    if spec_path.exists():
        with open(spec_path) as f:
            return json.load(f)
    return {}


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory for test isolation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_python_code():
    """Sample Python code for testing agents."""
    return '''
def hello(name: str) -> str:
    """Greets a person."""
    return f"Hello, {name}"

class Calculator:
    """Simple calculator."""
    
    def add(self, a: int, b: int) -> int:
        return a + b
    
    def divide(self, a: int, b: int) -> float:
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
'''


@pytest.fixture
def vulnerable_code():
    """Code with security issues for review agent testing."""
    return '''
import sqlite3

def get_user(user_id: str):
    """VULNERABLE: SQL injection via string interpolation."""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE id = '{user_id}'"  # SQL injection!
    cursor.execute(query)
    return cursor.fetchone()

def process_file(filename: str):
    """VULNERABLE: Path traversal."""
    with open(filename, 'r') as f:  # No path validation!
        return f.read()
'''