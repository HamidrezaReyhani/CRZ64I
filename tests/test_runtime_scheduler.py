import pytest
from crz.simulator.simulator import Simulator
from crz.runtime.runtime import Runtime


def test_thermal_migration():
    """Test that thermal_hint causes migration and temp decrease."""
    sim = Simulator()
    runtime = Runtime(sim)

    # Simulate heating ops
    ops = [
        {"op": "ADD", "args": ["r0", "r1", "r2"]} for _ in range(50)
    ]  # Many ops to heat

    # Set thermal hint
    runtime.interpret_hints([{"name": "thermal_hint", "value": "cool"}])

    # Run and check temp decrease
    temp_before = max(sim.thermal_map.values()) if sim.thermal_map else 25.0
    runtime.run_with_hints(ops)
    temp_after = max(sim.thermal_map.values()) if sim.thermal_map else 25.0

    assert (
        temp_after < temp_before
    ), f"Max temp after migration {temp_after} should be less than before {temp_before}"
