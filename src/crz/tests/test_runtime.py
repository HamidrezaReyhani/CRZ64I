"""
Tests for CRZ64I Runtime
"""

import pytest
from crz.runtime.runtime import Runtime
from crz.compiler.parser import parse
from crz.compiler.passes import run_passes
from crz.compiler.codegen_sim import generate_simulator_code as codegen_sim
from crz.simulator.simulator import Simulator


def test_runtime_power_hint():
    """Test power hint adjusts energy."""
    sim = Simulator()
    runtime = Runtime(sim)
    hints = [{"name": "power", "value": "low"}]
    runtime.interpret_hints(hints)
    assert runtime.hints["energy_mode"] == "low"


def test_thermal_migration():
    """Test thermal-aware scheduling."""
    sim = Simulator()
    runtime = Runtime(sim)
    hints = [{"name": "thermal_hint", "value": "cool"}]
    runtime.interpret_hints(hints)
    assert runtime.hints["thermal_action"] == "cool"


def test_fast_path_enter():
    """Test fast path enter."""
    sim = Simulator()
    runtime = Runtime(sim)
    runtime.handle_fast_path_enter()
    assert runtime.fast_path_active


def test_yield_for_migration():
    """Test yield for migration."""
    sim = Simulator()
    runtime = Runtime(sim)
    runtime.handle_yield()
    assert runtime.migration_state is not None
    assert runtime.migration_state["pc"] == sim.pc


def test_migrate_to_new_runtime():
    """Test migration to new runtime."""
    sim1 = Simulator()
    runtime1 = Runtime(sim1)
    runtime1.handle_yield()
    sim2 = Simulator()
    runtime2 = Runtime(sim2)
    runtime1.migrate_to(runtime2)
    assert runtime2.simulator.pc == runtime1.migration_state["pc"]


def test_runtime_with_hints_energy():
    """Test runtime with energy hint."""
    code = """
fn main() {
    ADD R0, R1, R2;
}
"""
    program = parse(code)
    config = {}
    optimized = run_passes(program, [], config)
    sim_ir = codegen_sim(optimized)
    sim = Simulator()
    runtime = Runtime(sim)
    hints = [{"name": "power", "value": "low"}]
    runtime.interpret_hints(hints)
    runtime.run_with_hints(sim_ir)
    report = runtime.get_runtime_report()
    assert "energy_mode" in report["hints"]
    assert report["hints"]["energy_mode"] == "low"


def test_runtime_with_hints_thermal():
    """Test runtime with thermal hint."""
    code = """
fn main() {
    ADD R0, R1, R2;
}
"""
    program = parse(code)
    config = {}
    optimized = run_passes(program, [], config)
    sim_ir = codegen_sim(optimized)
    sim = Simulator()
    runtime = Runtime(sim)
    hints = [{"name": "thermal_hint", "value": "cool"}]
    runtime.interpret_hints(hints)
    runtime.run_with_hints(sim_ir)
    report = runtime.get_runtime_report()
    assert "thermal_action" in report["hints"]
    assert report["hints"]["thermal_action"] == "cool"


def test_runtime_fast_path():
    """Test fast path in runtime."""
    code = """
fn main() {
    FAST_PATH_ENTER;
    ADD R0, R1, R2;
}
"""
    program = parse(code)
    config = {}
    optimized = run_passes(program, [], config)
    sim_ir = codegen_sim(optimized)
    sim = Simulator()
    runtime = Runtime(sim)
    runtime.run_with_hints(sim_ir)
    assert runtime.fast_path_active


def test_runtime_yield():
    """Test yield in runtime."""
    code = """
fn main() {
    ADD R0, R1, R2;
    YIELD;
    MUL R3, R4, R5;
}
"""
    program = parse(code)
    config = {}
    optimized = run_passes(program, [], config)
    sim_ir = codegen_sim(optimized)
    sim = Simulator()
    runtime = Runtime(sim)
    runtime.run_with_hints(sim_ir)
    assert runtime.migration_state is not None
    # Should stop at YIELD


def test_runtime_report():
    """Test runtime report."""
    sim = Simulator()
    runtime = Runtime(sim)
    report = runtime.get_runtime_report()
    assert "fast_path_active" in report
    assert "hints" in report
    assert "migration_ready" in report
    assert "simulator_report" in report
