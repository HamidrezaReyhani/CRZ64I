"""
Tests for CRZ64I Semantic Analyzer - Attribute Placement
"""

import pytest
from crz.compiler.parser import parse
from crz.compiler.semantic import SemanticAnalyzer


def test_reversible_on_function():
    """Test that #[reversible] is allowed on functions."""
    code = """
#[reversible] fn main() {
    NOP;
}
"""
    program = parse(code)
    analyzer = SemanticAnalyzer()
    issues = analyzer.analyze(program)
    assert len(issues) == 0


def test_reversible_on_if():
    """Test that #[reversible] is allowed on if blocks."""
    code = """
fn main() {
    #[reversible] if R0 == 1 {
        NOP;
    }
}
"""
    program = parse(code)
    analyzer = SemanticAnalyzer()
    issues = analyzer.analyze(program)
    assert len(issues) == 0


def test_reversible_on_loop():
    """Test that #[reversible] is allowed on loops."""
    code = """
fn main() {
    #[reversible] for i in 0..10 {
        NOP;
    }
}
"""
    program = parse(code)
    analyzer = SemanticAnalyzer()
    issues = analyzer.analyze(program)
    assert len(issues) == 0


def test_reversible_on_instruction_error():
    """Test that #[reversible] is not allowed on instructions."""
    code = """
fn main() {
    #[reversible] ADD R0, R1, R2;
}
"""
    program = parse(code)
    analyzer = SemanticAnalyzer()
    issues = analyzer.analyze(program)
    assert len(issues) == 1
    assert issues[0]["type"] == "error"
    assert "reversible" in issues[0]["message"]
    assert "instruction" in issues[0]["message"]
