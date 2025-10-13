"""
Tests for CRZ64I Reversible Block Detection
"""

import pytest
from crz.compiler.parser import parse
from crz.compiler.semantic import SemanticAnalyzer


def test_reversible_store_without_let():
    """Test STORE in reversible function without let tmp = target reports error."""
    code = """
#[reversible] fn main() {
    STORE R0, [R1];
}
"""
    program = parse(code)
    analyzer = SemanticAnalyzer()
    issues = analyzer.analyze(program)
    assert len(issues) == 1
    assert issues[0]["type"] == "error"
    assert (
        "Write to R0 in function main without prior let tmp = R0 or #[no_erase]"
        in issues[0]["message"]
    )
    assert issues[0]["line"] == 3  # Assuming line 3 is the STORE


def test_reversible_store_with_let():
    """Test STORE in reversible function with let tmp = target is ok."""
    code = """
#[reversible] fn main() {
    let tmp = R0;
    STORE R0, [R1];
}
"""
    program = parse(code)
    analyzer = SemanticAnalyzer()
    issues = analyzer.analyze(program)
    assert len(issues) == 0


def test_reversible_store_with_no_erase():
    """Test STORE in reversible function with #[no_erase] is ok."""
    code = """
#[reversible] fn main() {
    #[no_erase] STORE R0, [R1];
}
"""
    program = parse(code)
    analyzer = SemanticAnalyzer()
    issues = analyzer.analyze(program)
    assert len(issues) == 0
