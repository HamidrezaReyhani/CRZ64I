"""
Tests for CRZ64I Semantic Analyzer
"""

import pytest
from crz.compiler.parser import parse
from crz.compiler.semantic import SemanticAnalyzer


def test_invalid_attribute_on_function():
    code = """
#[invalid] fn main() {
    NOP;
}
"""
    program = parse(code)
    analyzer = SemanticAnalyzer()
    issues = analyzer.analyze(program)
    assert len(issues) == 1
    assert issues[0]["type"] == "error"
    assert "invalid" in issues[0]["message"]


def test_realtime_with_load():
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


def test_realtime_dma_start():
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


def test_reversible_write_without_let():
    code = """
#[reversible] fn main() {
    ADD R0, R1, R2;
}
"""
    program = parse(code)
    analyzer = SemanticAnalyzer()
    issues = analyzer.analyze(program)
    assert len(issues) == 1
    assert issues[0]["type"] == "error"
    assert "without prior let" in issues[0]["message"]


def test_reversible_write_with_let():
    code = """
#[reversible] fn main() {
    let tmp = R0;
    ADD R0, R1, R2;
}
"""
    program = parse(code)
    analyzer = SemanticAnalyzer()
    issues = analyzer.analyze(program)
    assert len(issues) == 0


def test_reversible_write_with_no_erase():
    code = """
#[reversible] fn main() {
    #[no_erase] ADD R0, R1, R2;
}
"""
    program = parse(code)
    analyzer = SemanticAnalyzer()
    issues = analyzer.analyze(program)
    assert len(issues) == 0


def test_valid_attributes():
    code = """
#[fusion] fn main() {
    #[fusion] ADD R0, R1, R2;
}
"""
    program = parse(code)
    analyzer = SemanticAnalyzer()
    issues = analyzer.analyze(program)
    assert len(issues) == 0


def test_invalid_attribute_on_instruction():
    code = """
fn main() {
    #[invalid] ADD R0, R1, R2;
}
"""
    program = parse(code)
    analyzer = SemanticAnalyzer()
    issues = analyzer.analyze(program)
    assert len(issues) == 1
    assert issues[0]["type"] == "error"
    assert "invalid" in issues[0]["message"]


def test_realtime_with_store():
    code = """
#[realtime] fn main() {
    STORE R0, [R1];
}
"""
    program = parse(code)
    analyzer = SemanticAnalyzer()
    issues = analyzer.analyze(program)
    assert len(issues) == 1
    assert issues[0]["type"] == "error"
    assert issues[0]["message"] == "Realtime violation: STORE inside realtime function."


def test_reversible_multiple_writes():
    code = """
#[reversible] fn main() {
    let tmp1 = R0;
    ADD R0, R1, R2;
    let tmp2 = R3;
    SUB R3, R4, R5;
}
"""
    program = parse(code)
    analyzer = SemanticAnalyzer()
    issues = analyzer.analyze(program)
    assert len(issues) == 0


def test_reversible_write_without_let_in_loop():
    code = """
#[reversible] fn main() {
    for i in 0..10 {
        ADD R0, R1, R2;
    }
}
"""
    program = parse(code)
    analyzer = SemanticAnalyzer()
    issues = analyzer.analyze(program)
    assert len(issues) == 1
    assert issues[0]["type"] == "error"
    assert "without prior let" in issues[0]["message"]


def test_power_attribute():
    code = """
#[power="low"] fn main() {
    NOP;
}
"""
    program = parse(code)
    analyzer = SemanticAnalyzer()
    issues = analyzer.analyze(program)
    assert len(issues) == 0


def test_thermal_hint_attribute():
    code = """
#[thermal_hint="cool"] fn main() {
    NOP;
}
"""
    program = parse(code)
    analyzer = SemanticAnalyzer()
    issues = analyzer.analyze(program)
    assert len(issues) == 0
