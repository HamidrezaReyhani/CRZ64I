"""
Tests for CRZ64I Semantic Analyzer - Realtime Constraints
"""

import pytest
from crz.compiler.parser import parse
from crz.compiler.semantic import SemanticAnalyzer


def test_realtime_violation_dma_start():
    """Test that DMA_START inside realtime function raises violation."""
    code = """
#[realtime] fn main() {
    DMA_START R0, R1, R2;
}
"""
    program = parse(code)
    analyzer = SemanticAnalyzer()
    issues = analyzer.analyze(program)
    assert len(issues) == 1
    assert issues[0]["type"] == "error"
    assert (
        issues[0]["message"]
        == "Realtime violation: DMA_START inside realtime function."
    )


def test_realtime_violation_dynamic_alloc():
    """Test that dynamic alloc ops inside realtime function raise violation."""
    code = """
#[realtime] fn main() {
    LOAD R0, [R1];
}
"""
    program = parse(code)
    analyzer = SemanticAnalyzer()
    issues = analyzer.analyze(program)
    assert len(issues) == 1
    assert issues[0]["type"] == "error"
    assert issues[0]["message"] == "Realtime violation: LOAD inside realtime function."
