"""
Eval Generator — Generates eval.yaml and eval/ test harness for pytest benchmarks.
"""

from __future__ import annotations

from generators.base import Generator, ValidationResult, register_generator
from spec.models import AgentRole, ProjectSpec, TargetAgent


@register_generator
class EvalGenerator(Generator):
    """Generates evaluation harness with pytest benchmarks per agent role."""

    @property
    def target_agents(self) -> list[TargetAgent]:
        return []  # Shared - runs for all projects

    @property
    def output_files(self) -> list[str]:
        return ["eval.yaml", "eval/__init__.py", "eval/conftest.py", "eval/test_feature_agent.py", "eval/test_review_agent.py"]

    def generate(self, spec: ProjectSpec) -> dict[str, str]:
        """Generate eval harness files from spec."""
        files = {}

        files["eval.yaml"] = self._generate_eval_yaml(spec)
        files["eval/__init__.py"] = "# AgentConfig Evaluation Harness\n"
        files["eval/conftest.py"] = self._generate_conftest(spec)
        files["eval/test_feature_agent.py"] = self._generate_feature_tests(spec)
        files["eval/test_review_agent.py"] = self._generate_review_tests(spec)

        return files

    def _generate_eval_yaml(self, spec: ProjectSpec) -> str:
        lines = [
            "# AgentConfig Evaluation Configuration",
            f"# Project: {spec.project_name}",
            f"# Generated: {spec.updated_at.isoformat()}",
            "",
            "version: \"1.0\"",
            f"project: {spec.project_name}",
            f"framework: {spec.eval_config.framework.value}",
            "",
            "# Global thresholds",
            "thresholds:",
        ]

        for key, value in spec.eval_config.thresholds.items():
            lines.append(f"  {key}: {value}")

        if not spec.eval_config.thresholds:
            lines.append("  default: 0.8")

        lines.extend([
            "",
            "# Benchmarks per agent role",
            "benchmarks:",
        ])

        if spec.agent_team.orchestrator:
            lines.extend([
                "  - name: orchestrator_task_decomposition",
                "    agent_role: orchestrator",
                "    test: eval/test_orchestrator.py::test_task_decomposition",
                "    threshold: 0.85",
                "    description: Orchestrator correctly breaks down complex tasks",
            ])

        for role in spec.agent_team.workers:
            if role == AgentRole.FEATURE:
                lines.extend([
                    "  - name: feature_code_correctness",
                    "    agent_role: feature",
                    "    test: eval/test_feature_agent.py::test_code_correctness",
                    "    threshold: 0.85",
                    "    description: Feature agent produces syntactically correct code",
                ])
                lines.extend([
                    "  - name: feature_test_coverage",
                    "    agent_role: feature",
                    "    test: eval/test_feature_agent.py::test_has_tests",
                    "    threshold: 0.80",
                    "    description: Feature agent writes tests for new code",
                ])
                lines.extend([
                    "  - name: feature_conventions",
                    "    agent_role: feature",
                    "    test: eval/test_feature_agent.py::test_follows_conventions",
                    "    threshold: 0.90",
                    "    description: Feature agent follows project conventions",
                ])

            elif role == AgentRole.REVIEW:
                lines.extend([
                    "  - name: review_security_detection",
                    "    agent_role: review",
                    "    test: eval/test_review_agent.py::test_detects_security_issues",
                    "    threshold: 0.90",
                    "    description: Review agent catches security vulnerabilities",
                ])
                lines.extend([
                    "  - name: review_correctness",
                    "    agent_role: review",
                    "    test: eval/test_review_agent.py::test_correctness_check",
                    "    threshold: 0.85",
                    "    description: Review agent identifies logic errors",
                ])

            elif role == AgentRole.TEST:
                lines.extend([
                    "  - name: test_coverage_generation",
                    "    agent_role: test",
                    "    test: eval/test_test_agent.py::test_generates_tests",
                    "    threshold: 0.80",
                    "    description: Test agent generates comprehensive tests",
                ])

            elif role == AgentRole.RESEARCH:
                lines.extend([
                    "  - name: research_accuracy",
                    "    agent_role: research",
                    "    test: eval/test_research_agent.py::test_accurate_findings",
                    "    threshold: 0.80",
                    "    description: Research agent provides accurate information",
                ])

            elif role == AgentRole.DOCS:
                lines.extend([
                    "  - name: docs_completeness",
                    "    agent_role: docs",
                    "    test: eval/test_docs_agent.py::test_complete_documentation",
                    "    threshold: 0.85",
                    "    description: Docs agent maintains complete documentation",
                ])

            elif role == AgentRole.DEPS:
                lines.extend([
                    "  - name: deps_security_updates",
                    "    agent_role: deps",
                    "    test: eval/test_deps_agent.py::test_finds_security_updates",
                    "    threshold: 0.90",
                    "    description: Deps agent identifies security updates",
                ])

        return "\n".join(lines)

    def _generate_conftest(self, spec: ProjectSpec) -> str:
        """Generate pytest conftest.py with shared fixtures."""
        lines = [
            '"""',
            'Pytest configuration for AgentConfig evaluation harness.',
            f'Project: {spec.project_name}',
            '"""',
            '',
            'import pytest',
            'import tempfile',
            'from pathlib import Path',
            '',
            '',
            '@pytest.fixture',
            'def project_spec():',
            '    """Load the project spec for testing."""',
            '    import json',
            '    spec_path = Path(__file__).parent.parent / "agent-config-spec.json"',
            '    if spec_path.exists():',
            '        with open(spec_path) as f:',
            '            return json.load(f)',
            '    return {}',
            '',
            '',
            '@pytest.fixture',
            'def temp_project_dir():',
            '    """Create a temporary directory for test isolation."""',
            '    with tempfile.TemporaryDirectory() as tmpdir:',
            '        yield Path(tmpdir)',
            '',
            '',
            '@pytest.fixture',
            'def sample_python_code():',
            '    """Sample Python code for testing agents."""',
            '    return \'\'\'',
            'def hello(name: str) -> str:',
            '    """Greets a person."""',
            '    return f"Hello, {name}"',
            '',
            'class Calculator:',
            '    """Simple calculator."""',
            '    ',
            '    def add(self, a: int, b: int) -> int:',
            '        return a + b',
            '    ',
            '    def divide(self, a: int, b: int) -> float:',
            '        if b == 0:',
            '            raise ValueError("Cannot divide by zero")',
            '        return a / b',
            '\'\'\'',
            '',
            '',
            '@pytest.fixture',
            'def vulnerable_code():',
            '    """Code with security issues for review agent testing."""',
            '    return \'\'\'',
            'import sqlite3',
            '',
            'def get_user(user_id: str):',
            '    """VULNERABLE: SQL injection via string interpolation."""',
            '    conn = sqlite3.connect("users.db")',
            '    cursor = conn.cursor()',
            '    query = f"SELECT * FROM users WHERE id = \'{user_id}\'"  # SQL injection!',
            '    cursor.execute(query)',
            '    return cursor.fetchone()',
            '',
            'def process_file(filename: str):',
            '    """VULNERABLE: Path traversal."""',
            '    with open(filename, \'r\') as f:  # No path validation!',
            '        return f.read()',
            '\'\'\'',
        ]
        return "\n".join(lines)

    def _generate_feature_tests(self, spec: ProjectSpec) -> str:
        lines = [
            '"""',
            'Feature Agent Evaluation Tests',
            f'Project: {spec.project_name}',
            '"""',
            '',
            'import pytest',
            'import ast',
            'import subprocess',
            'from pathlib import Path',
            '',
            'class TestFeatureAgent:',
            '    """Tests for feature development agent capabilities."""',
            '',
            '    def test_code_correctness(self, sample_python_code):',
            '        """Test that generated code is syntactically correct."""',
            '        # Parse the code - should not raise SyntaxError',
            '        tree = ast.parse(sample_python_code)',
            '        assert tree is not None',
            '',
            '    def test_has_type_hints(self, sample_python_code):',
            '        """Test that code includes type hints."""',
            '        tree = ast.parse(sample_python_code)',
            '        functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]',
            '        for func in functions:',
            '            # At minimum, return type should be annotated',
            '            assert func.returns is not None, f"Function {func.name} missing return type"',
            '',
            '    def test_has_docstrings(self, sample_python_code):',
            '        """Test that public functions have docstrings."""',
            '        tree = ast.parse(sample_python_code)',
            '        for node in ast.walk(tree):',
            '            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):',
            '                if not node.name.startswith("_"):',
            '                    assert ast.get_docstring(node), f"{node.name} missing docstring"',
            '',
            '    def test_follows_conventions(self, project_spec):',
            '        """Test that code follows project conventions."""',
            '        conventions = project_spec.get("conventions", {})',
            '        assert conventions.get("type_hints") is True',
            '        assert conventions.get("docstrings") == "google"',
            '        assert conventions.get("line_length") == 100',
            '',
            '    def test_error_handling_style(self, project_spec):',
            '        """Test that error handling follows conventions."""',
            '        conventions = project_spec.get("conventions", {})',
            '        assert conventions.get("error_handling") in ("exceptions", "result-type", "both")',
            '',
            '    def test_generated_code_runs(self, temp_project_dir):',
            '        """Test that generated code can be executed."""',
            '        test_file = temp_project_dir / "test_module.py"',
            '        test_file.write_text("""',
            'def add(a: int, b: int) -> int:',
            '    return a + b',
            '',
            'if __name__ == "__main__":',
            '    print(add(2, 3))',
            '""")',
            '        result = subprocess.run(',
            '            ["python", str(test_file)],',
            '            capture_output=True,',
            '            text=True,',
            '            cwd=temp_project_dir',
            '        )',
            '        assert result.returncode == 0',
            '        assert "5" in result.stdout',
            '',
            '',
            'class TestFeatureAgentIntegration:',
            '    """Integration tests for feature agent workflows."""',
            '',
            '    def test_creates_valid_python_files(self, temp_project_dir):',
            '        """Test agent can create valid Python files."""',
            '        # This would be replaced with actual agent invocation',
            '        pass',
            '',
            '    def test_writes_tests_for_new_code(self, temp_project_dir):',
            '        """Test that feature agent writes tests."""',
            '        # This would be replaced with actual agent invocation',
            '        pass',
        ]
        return "\n".join(lines)

    def _generate_review_tests(self, spec: ProjectSpec) -> str:
        lines = [
            '"""',
            'Review Agent Evaluation Tests',
            f'Project: {spec.project_name}',
            '"""',
            '',
            'import pytest',
            'import ast',
            'from pathlib import Path',
            '',
            'class TestReviewAgent:',
            '    """Tests for code review agent capabilities."""',
            '',
            '    def test_detects_sql_injection(self, vulnerable_code):',
            '        """Test that review agent catches SQL injection."""',
            '        tree = ast.parse(vulnerable_code)',
            '        # Look for f-string in execute() call',
            '        issues = []',
            '        for node in ast.walk(tree):',
            '            if isinstance(node, ast.Call):',
            '                if hasattr(node.func, "attr") and node.func.attr == "execute":',
            '                    for arg in node.args:',
            '                        if isinstance(arg, ast.JoinedStr):  # f-string',
            '                            issues.append("SQL injection via f-string in execute()")',
            '        assert len(issues) > 0, "Should detect SQL injection"',
            '',
            '    def test_detects_path_traversal(self, vulnerable_code):',
            '        """Test that review agent catches path traversal."""',
            '        tree = ast.parse(vulnerable_code)',
            '        issues = []',
            '        for node in ast.walk(tree):',
            '            if isinstance(node, ast.Call):',
            '                if hasattr(node.func, "attr") and node.func.attr == "open":',
            '                    # Check if filename parameter is validated',
            '                    issues.append("Path traversal risk in open()")',
            '        assert len(issues) > 0, "Should detect path traversal"',
            '',
            '    def test_correctness_check(self, sample_python_code):',
            '        """Test review agent identifies logic errors."""',
            '        # This would check for common logic issues',
            '        pass',
            '',
            '    def test_performance_issues(self):',
            '        """Test detection of performance anti-patterns."""',
            '        # N+1 queries, memory leaks, etc.',
            '        pass',
            '',
            '    def test_security_best_practices(self, project_spec):',
            '        """Test security conventions are followed."""',
            '        conventions = project_spec.get("conventions", {})',
            '        # Verify security-relevant conventions',
            '        assert conventions.get("error_handling") in ("exceptions", "both")',
            '',
            '',
            'class TestReviewAgentIntegration:',
            '    """Integration tests for review agent workflows."""',
            '',
            '    def test_reviews_pull_request(self, temp_project_dir):',
            '        """Test agent can review a PR."""',
            '        pass',
            '',
            '    def test_provides_actionable_feedback(self, temp_project_dir):',
            '        """Test feedback is specific and actionable."""',
            '        pass',
        ]
        return "\n".join(lines)

    def validate_output(self, files: dict[str, str]) -> ValidationResult:
        """Validate generated eval configs."""
        errors = []

        try:
            import yaml
            yaml.safe_load(files.get("eval.yaml", ""))
        except Exception as e:
            errors.append(f"eval.yaml invalid YAML: {e}")

        try:
            import ast
            for fname in ["eval/conftest.py", "eval/test_feature_agent.py", "eval/test_review_agent.py"]:
                content = files.get(fname, "")
                if content:
                    ast.parse(content)
        except SyntaxError as e:
            errors.append(f"Python syntax error: {e}")

        return ValidationResult(valid=len(errors) == 0, errors=errors)
