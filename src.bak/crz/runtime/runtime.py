"""
CRZ64I Runtime and ABI

Handles hint interpretation, fast path, yield, migration.
"""

from typing import Dict, List, Any, Optional
from ..simulator.simulator import Simulator


class Policy:
    """Policy for applying hints."""

    def apply_hint(self, hint, runtime):
        if hint == "thermal_hint":
            for comp in runtime.simulator.thermal_map:
                runtime.simulator.thermal_map[comp] *= 0.95


class Runtime:
    """CRZ64I Runtime."""

    def __init__(self, simulator: Simulator):
        self.simulator = simulator
        self.hints: Dict[str, Any] = {}
        self.fast_path_active = False
        self.migration_state: Optional[Dict[str, Any]] = None
        self.policy = Policy()

    def interpret_hints(self, hints: List[Dict[str, str]]):
        """Interpret runtime hints."""
        for hint in hints:
            name = hint["name"]
            value = hint.get("value")
            if name == "power":
                self.hints["energy_mode"] = value  # e.g., "low"
            elif name == "thermal_hint":
                self.hints["thermal_hint"] = value  # e.g., "cool"
            elif name == "reversible_hint":
                self.hints["reversible"] = True
            # More hints

    def handle_fast_path_enter(self):
        """Enter fast path mode."""
        self.fast_path_active = True
        # Optimize execution, e.g., skip checks
        print("Entering fast path")

    def handle_yield(self):
        """Handle yield for migration."""
        self.migration_state = {
            "regs": self.simulator.regs.copy(),
            "pc": self.simulator.pc,
            "energy": self.simulator.energy_used,
        }
        print("Yielding for migration")

    def migrate_to(self, new_runtime: 'Runtime'):
        """Migrate state to new runtime."""
        if self.migration_state:
            new_runtime.simulator.regs = self.migration_state["regs"]
            new_runtime.simulator.pc = self.migration_state["pc"]
            new_runtime.simulator.energy_used = self.migration_state["energy"]
            print("Migrated state")

    def migrate_to_cooler_core(self):
        """Migrate to a cooler simulated core."""
        # In simulation, just reset thermal or log
        for comp in self.simulator.thermal_map:
            self.simulator.thermal_map[comp] *= 0.8  # Cool significantly
        print("Migrated to cooler core, thermal reduced")

    def run_with_hints(self, ops: List[Dict[str, Any]]):
        """Run ops with hint handling."""
        i = 0
        while i < len(ops):
            op = ops[i]
            # Check for special ops
            if op["op"] == "FAST_PATH_ENTER":
                self.handle_fast_path_enter()
            elif op["op"] == "YIELD":
                self.handle_yield()
                break  # Pause
            else:
                self.simulator.execute_op(op["op"], op["args"])
                # Apply hints
                if self.hints.get("energy_mode") == "low":
                    self.simulator.energy_used *= 0.9  # Reduce energy
                if self.hints.get("thermal_hint") == "cool":
                    self.policy.apply_hint("thermal_hint", self)
                # Thermal-aware migration
                max_temp = max(self.simulator.thermal_map.values()) if self.simulator.thermal_map else 0
                if max_temp > 50.0:  # Threshold
                    self.migrate_to_cooler_core()
            i += 1

    def get_runtime_report(self) -> Dict[str, Any]:
        """Get runtime report."""
        return {
            "fast_path_active": self.fast_path_active,
            "hints": self.hints,
            "migration_ready": self.migration_state is not None,
            "simulator_report": self.simulator.get_energy_report(),
        }
