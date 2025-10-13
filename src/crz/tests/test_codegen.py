"""
Tests for CRZ64I Codegen
"""

import pytest
from crz.compiler.parser import parse
from crz.compiler.codegen_sim import generate_simulator_code as codegen_sim
from crz.compiler.codegen_riscv import generate_riscv_code as codegen_riscv


def test_codegen_sim():
    """Test simulator IR generation."""
    code = """
fn main() {
    ADD R0, R1, R2;
    LOAD R3, [R4];
}
"""
    program = parse(code)
    ir = codegen_sim(program)
    assert len(ir) == 2
    assert ir[0].op == "ADD"
    assert ir[0].args == ["R0", "R1", "R2"]
    assert not ir[0].fused
    assert ir[1].op == "LOAD"


def test_codegen_riscv():
    """Test RISC-V textual generation."""
    code = """
fn main() {
    ADD R0, R1, R2;
}
"""
    program = parse(code)
    riscv = codegen_riscv(program)
    assert "main:" in riscv
    assert "add R0, R1, R2" in riscv


def test_codegen_sim_fused():
    """Test fused op in simulator IR."""
    code = """
fn main() {
    FUSED_LOAD_ADD R0, R1, 5;
}
"""
    program = parse(code)
    ir = codegen_sim(program)
    assert len(ir) == 1
    assert ir[0].op == "FUSED_LOAD_ADD"
    assert ir[0].fused


def test_codegen_riscv_jump():
    """Test jump in RISC-V."""
    code = """
fn main() {
    JMP label;
}
"""
    program = parse(code)
    riscv = codegen_riscv(program)
    assert "j label" in riscv


def test_codegen_sim_multiple_functions():
    """Test multiple functions."""
    code = """
fn foo() {
    ADD R0, R1, R2;
}
fn main() {
    CALL foo;
}
"""
    program = parse(code)
    ir = codegen_sim(program)
    # Assume ir is for main, with call
    assert len(ir) == 1
    assert ir[0].op == "CALL"


def test_codegen_riscv_return():
    """Test return in RISC-V."""
    code = """
fn main() {
    RET;
}
"""
    program = parse(code)
    riscv = codegen_riscv(program)
    assert "ret" in riscv


def test_codegen_sim_vector():
    """Test vector op."""
    code = """
fn main() {
    VADD V0, V1, V2;
}
"""
    program = parse(code)
    ir = codegen_sim(program)
    assert len(ir) == 1
    assert ir[0].op == "VADD"
    assert ir[0].args == ["V0", "V1", "V2"]


def test_codegen_riscv_vector():
    """Test vector in RISC-V (placeholder)."""
    code = """
fn main() {
    VADD V0, V1, V2;
}
"""
    program = parse(code)
    riscv = codegen_riscv(program)
    assert "VADD" in riscv  # Placeholder
