"""
Tests for CRZ64I Simulator
"""

import pytest
from pathlib import Path
from crz.compiler.parser import parse
from crz.compiler.passes import run_passes
from crz.compiler.codegen_sim import generate_simulator_code as codegen_sim
from crz.simulator.simulator import Simulator


def test_simulator_add():
    """Test ADD instruction."""
    code = """
fn main() {
    ADD R0, R1, 5;
}
"""
    program = parse(code)
    config = {}
    optimized = run_passes(program, [], config)
    sim_ir = codegen_sim(optimized)
    sim = Simulator()
    initial_state = {"registers": {"R1": 10}}
    cycles, energy, temp, final_state = sim.run(sim_ir, initial_state, metrics=True)
    assert final_state["registers"]["R0"] == 15
    assert cycles == 1
    assert energy > 0


def test_simulator_fibonacci():
    """Test fibonacci computation for n=10."""
    code = Path("examples/fibonacci.crz").read_text()
    program = parse(code)
    config = {}
    optimized = run_passes(program, [], config)
    sim_ir = codegen_sim(optimized)
    sim = Simulator()
    initial_state = {"registers": {"R3": 10}}  # n=10
    cycles, energy, temp, final_state = sim.run(sim_ir, initial_state, metrics=True)
    assert final_state["registers"]["R0"] == 55  # fib(10)=55


def test_simulator_energy_model():
    """Test energy consumption."""
    code = """
fn main() {
    ADD R0, R1, R2;
    MUL R3, R4, R5;
}
"""
    program = parse(code)
    config = {}
    optimized = run_passes(program, [], config)
    sim_ir = codegen_sim(optimized)
    sim = Simulator()
    initial_state = {"registers": {"R1": 1, "R2": 2, "R4": 3, "R5": 4}}
    cycles, energy, temp, final_state = sim.run(sim_ir, initial_state, metrics=True)
    assert energy > 0
    assert "total_energy" in sim.get_energy_report()


def test_simulator_thermal_model():
    """Test thermal hotspots."""
    code = """
fn main() {
    ADD R0, R1, R2;
    MUL R3, R4, R5;
}
"""
    program = parse(code)
    config = {}
    optimized = run_passes(program, [], config)
    sim_ir = codegen_sim(optimized)
    sim = Simulator()
    initial_state = {"registers": {"R1": 1, "R2": 2, "R4": 3, "R5": 4}}
    cycles, energy, temp, final_state = sim.run(sim_ir, initial_state, metrics=True)
    report = sim.get_energy_report()
    assert "thermal_hotspots" in report
    assert report["thermal_hotspots"]["alu"] > 25.0


def test_simulator_fused_op():
    """Test fused operation."""
    code = """
fn main() {
    FUSED_LOAD_ADD R0, R1, 5;
}
"""
    program = parse(code)
    config = {}
    optimized = run_passes(program, [], config)
    sim_ir = codegen_sim(optimized)
    sim = Simulator()
    initial_state = {"registers": {"R1": 10}}
    cycles, energy, temp, final_state = sim.run(sim_ir, initial_state, metrics=True)
    assert final_state["registers"]["R0"] == 15  # Assuming fused loads from memory + add
    assert energy < 5.0  # Lower energy for fused


def test_simulator_memory_access():
    """Test memory load/store."""
    code = """
fn main() {
    STORE 42, [R1];
    LOAD R0, [R1];
}
"""
    program = parse(code)
    config = {}
    optimized = run_passes(program, [], config)
    sim_ir = codegen_sim(optimized)
    sim = Simulator()
    initial_state = {"registers": {"R1": 100}}  # Memory address
    cycles, energy, temp, final_state = sim.run(sim_ir, initial_state, metrics=True)
    assert final_state["registers"]["R0"] == 42
    assert 100 in sim.memory
    assert sim.memory[100] == 42


def test_simulator_branch():
    """Test branch instruction."""
    code = """
fn main() {
    ADD R0, R1, 0;  // Set Z flag
    JZ 5;  // Jump if zero
}
"""
    program = parse(code)
    config = {}
    optimized = run_passes(program, [], config)
    sim_ir = codegen_sim(optimized)
    sim = Simulator()
    initial_state = {"registers": {"R1": 0}}
    cycles, energy, temp, final_state = sim.run(sim_ir, initial_state, metrics=True)
    # Assuming pc jumps, but since sequential, check flags
    assert sim.get_flag("Z")
