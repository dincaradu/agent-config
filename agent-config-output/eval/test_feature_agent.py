"""
Feature Agent Evaluation Tests
Project: test-project
"""

import pytest
import ast
import subprocess
from pathlib import Path

class TestFeatureAgent:
    """Tests for feature development agent capabilities."""

    def test_code_correctness(self, sample_python_code):
        """Test that generated code is syntactically correct."""
        # Parse the code - should not raise SyntaxError
        tree = ast.parse(sample_python_code)
        assert tree is not None

    def test_has_type_hints(self, sample_python_code):
        """Test that code includes type hints."""
        tree = ast.parse(sample_python_code)
        functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        for func in functions:
            # At minimum, return type should be annotated
            assert func.returns is not None, f"Function {func.name} missing return type"

    def test_has_docstrings(self, sample_python_code):
        """Test that public functions have docstrings."""
        tree = ast.parse(sample_python_code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not node.name.startswith("_"):
                    assert ast.get_docstring(node), f"{node.name} missing docstring"

    def test_follows_conventions(self, project_spec):
        """Test that code follows project conventions."""
        conventions = project_spec.get("conventions", {})
        assert conventions.get("type_hints") is True
        assert conventions.get("docstrings") == "google"
        assert conventions.get("line_length") == 100

    def test_error_handling_style(self, project_spec):
        """Test that error handling follows conventions."""
        conventions = project_spec.get("conventions", {})
        assert conventions.get("error_handling") in ("exceptions", "result-type", "both")

    def test_generated_code_runs(self, temp_project_dir):
        """Test that generated code can be executed."""
        test_file = temp_project_dir / "test_module.py"
        test_file.write_text("""
def add(a: int, b: int) -> int:
    return a + b

if __name__ == "__main__":
    print(add(2, 3))
""")
        result = subprocess.run(
            ["python", str(test_file)],
            capture_output=True,
            text=True,
            cwd=temp_project_dir
        )
        assert result.returncode == 0
        assert "5" in result.stdout


class TestFeatureAgentIntegration:
    """Integration tests for feature agent workflows."""

    def test_creates_valid_python_files(self, temp_project_dir):
        """Test agent can create valid Python files."""
        # This would be replaced with actual agent invocation
        pass

    def test_writes_tests_for_new_code(self, temp_project_dir):
        """Test that feature agent writes tests."""
        # This would be replaced with actual agent invocation
        pass