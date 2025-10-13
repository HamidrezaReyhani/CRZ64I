"""
Tests for CRZ64I Dataflow Analyzer
"""

import pytest
from crz.compiler.parser import parse
from crz.compiler.dataflow import DataflowAnalyzer


def test_reversible_branching_write():
    """Test detection on branching path."""
    code = """
#[reversible] fn main() {
    let tmp = R0;
    if x > 0 {
        ADD R0, R1, R2;  // This should be error on this path
    } else {
        NOP;
    }
}
"""
    program = parse(code)
    func = program.declarations[0]
    analyzer = DataflowAnalyzer(func)
    errors = analyzer.analyze()
    assert len(errors) > 0
    assert "Write to R0" in errors[0]["message"]


def test_reversible_no_error_with_let():
    """Test no error when let is before all paths."""
    code = """
#[reversible] fn main() {
    let tmp = R0;
    if x > 0 {
        ADD R0, R1, R2;
    } else {
        ADD R0, R3, R4;
    }
}
"""
    program = parse(code)
    func = program.declarations[0]
    analyzer = DataflowAnalyzer(func)
    errors = analyzer.analyze()
    assert len(errors) == 0


def test_reversible_loop_write():
    """Test detection in loop."""
    code = """
#[reversible] fn main() {
    for i in 0..10 {
        ADD R0, R1, R2;  // Error without let
    }
}
"""
    program = parse(code)
    func = program.declarations[0]
    analyzer = DataflowAnalyzer(func)
    errors = analyzer.analyze()
    assert len(errors) > 0
    assert "Write to R0" in errors[0]["message"]


def test_reversible_nested_if():
    """Test nested if."""
    code = """
#[reversible] fn main() {
    let tmp = R0;
    if x > 0 {
        if y > 0 {
            ADD R0, R1, R2;
        }
    }
}
"""
    program = parse(code)
    func = program.declarations[0]
    analyzer = DataflowAnalyzer(func)
    errors = analyzer.analyze()
    assert len(errors) == 0


def test_reversible_multiple_targets():
    """Test multiple targets."""
    code = """
#[reversible] fn main() {
    let tmp1 = R0;
    let tmp2 = R1;
    ADD R0, R2, R3;
    SUB R1, R4, R5;
}
"""
    program = parse(code)
    func = program.declarations[0]
    analyzer = DataflowAnalyzer(func)
    errors = analyzer.analyze()
    assert len(errors) == 0


def test_reversible_write_after_let():
    """Test write after let."""
    code = """
#[reversible] fn main() {
    ADD R0, R1, R2;
    let tmp = R0;
}
"""
    program = parse(code)
    func = program.declarations[0]
    analyzer = DataflowAnalyzer(func)
    errors = analyzer.analyze()
    assert len(errors) > 0
    assert "Write to R0" in errors[0]["message"]
