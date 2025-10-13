"""
Edge case tests for CRZ64I components.
"""

import pytest
from crz.compiler.parser import parse
from crz.simulator.simulator import Simulator
from crz.config import load_config


def test_div_zero():
    """Test division by zero in simulator."""
    config = load_config()
    sim = Simulator(config)
    sim.regs["r0"] = 10
    sim.regs["r1"] = 0
    with pytest.raises(ZeroDivisionError):
        sim.execute_op("DIV", ["r2", "r0", "r1"])


def test_memory_bounds():
    """Test memory bounds checking."""
    config = load_config()
    sim = Simulator(config)
    with pytest.raises(ValueError, match="Memory access out of bounds"):
        sim.check_memory_bounds(1024)


def test_invalid_syntax():
    """Test parser with invalid syntax."""
    code = "fn invalid { ADD R1 }"
    with pytest.raises(Exception):  # Lark will raise
        parse(code)


def test_thermal_threshold():
    """Test thermal cooling when above threshold."""
    config = load_config()
    sim = Simulator(config)
    sim.thermal_map["alu"] = 55.0  # Above 50
    sim.update_thermal_advanced("ADD", 2.0)
    assert sim.thermal_map["alu"] < 55.0  # Should be cooled


def test_path_bounding():
    """Test dataflow path bounding."""
    from crz.compiler.dataflow import CFG, BasicBlock

    blocks = [BasicBlock(0, []), BasicBlock(1, [])]
    blocks[0].successors = [1]
    cfg = CFG(blocks)
    paths = cfg.enumerate_paths(max_paths=1)
    assert len(paths) <= 1
