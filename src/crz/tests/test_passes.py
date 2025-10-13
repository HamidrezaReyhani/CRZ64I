"""
Tests for CRZ64I Passes
"""

import pytest
from crz.compiler.parser import parse
from crz.compiler.passes import run_passes
from crz.compiler.ast import Instr


def test_fusion_pass():
    """Test fusion of LOAD; ADD."""
    code = """
fn main() {
    LOAD R0, [R1];
    ADD R0, R0, 5;
}
"""
    program = parse(code)
    config = {}
    result = run_passes(program, ["fusion"], config)
    func = result.declarations[0]
    assert len(func.body) == 1
    fused = func.body[0]
    assert isinstance(fused, Instr)
    assert fused.mnemonic == "FUSED_LOAD_ADD"
    assert fused.operands == ["R0", "R1", "5"]


def test_reversible_emulation_pass():
    """Test insertion of SAVE_DELTA/RESTORE_DELTA."""
    code = """
#[reversible] fn main() {
    ADD R0, R1, R2;
}
"""
    program = parse(code)
    config = {}
    result = run_passes(program, ["reversible_emulation"], config)
    func = result.declarations[0]
    assert len(func.body) == 3
    assert func.body[0].mnemonic == "SAVE_DELTA"
    assert func.body[1].mnemonic == "ADD"
    assert func.body[2].mnemonic == "RESTORE_DELTA"


def test_energy_profile_pass():
    """Test energy annotation."""
    code = """
fn main() {
    ADD R0, R1, R2;
}
"""
    program = parse(code)
    config = {"energy_table": {"ADD": {"energy": 1.5, "latency": 2}}}
    result = run_passes(program, ["energy_profile"], config)
    func = result.declarations[0]
    add = func.body[0]
    energy_attr = next((attr for attr in add.attrs if attr.name == "energy"), None)
    assert energy_attr.value == "1.5"


def test_multiple_passes():
    """Test running multiple passes."""
    code = """
fn main() {
    LOAD R0, [R1];
    ADD R0, R0, 5;
}
"""
    program = parse(code)
    config = {"energy_table": {"FUSED_LOAD_ADD": {"energy": 3.0, "latency": 3}}}
    result = run_passes(program, ["fusion", "energy_profile"], config)
    func = result.declarations[0]
    assert len(func.body) == 1
    fused = func.body[0]
    assert fused.mnemonic == "FUSED_LOAD_ADD"
    energy_attr = next((attr for attr in fused.attrs if attr.name == "energy"), None)
    assert energy_attr.value == "3.0"


def test_no_fusion_if_not_matching():
    """Test no fusion if pattern not matched."""
    code = """
fn main() {
    ADD R0, R1, R2;
    LOAD R3, [R4];
}
"""
    program = parse(code)
    config = {}
    result = run_passes(program, ["fusion"], config)
    func = result.declarations[0]
    assert len(func.body) == 2
    assert func.body[0].mnemonic == "ADD"
    assert func.body[1].mnemonic == "LOAD"


def test_reversible_emulation_with_no_erase():
    """Test reversible emulation skips #[no_erase]."""
    code = """
#[reversible] fn main() {
    #[no_erase] ADD R0, R1, R2;
}
"""
    program = parse(code)
    config = {}
    result = run_passes(program, ["reversible_emulation"], config)
    func = result.declarations[0]
    assert len(func.body) == 1
    assert func.body[0].mnemonic == "ADD"


def test_energy_profile_multiple_instr():
    """Test energy on multiple instructions."""
    code = """
fn main() {
    ADD R0, R1, R2;
    MUL R3, R4, R5;
}
"""
    program = parse(code)
    config = {"energy_table": {"ADD": {"energy": 1.0}, "MUL": {"energy": 5.0}}}
    result = run_passes(program, ["energy_profile"], config)
    func = result.declarations[0]
    add_energy = next(
        (attr for attr in func.body[0].attrs if attr.name == "energy"), None
    )
    mul_energy = next(
        (attr for attr in func.body[1].attrs if attr.name == "energy"), None
    )
    assert add_energy.value == "1.0"
    assert mul_energy.value == "5.0"
