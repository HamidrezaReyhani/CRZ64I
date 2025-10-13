"""CRZ64I configuration loader."""

import json
from typing import Any, Dict


def load_config(file_path: str = "config.json") -> Dict[str, Any]:
    """Load configuration from config.json or return defaults."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Default config
        return {
            "energy": {
                "ADD": 4.5e-08,  # Updated with measured energy per op in Joules
                "SUB": 6e-08,
                "MUL": 1.2e-6,
                "DIV": 3.0e-6,
                "LOAD": 4.0000000000000003e-07,  # Updated with measured per load
                "STORE": 4.0000000000000003e-07,
                "JMP": 1e-8,
                "BR_IF": 2.5e-7,
                "LABEL": 0.0,
                "BRANCH": 3.0e-7,
                "FUSED_LOAD_ADD": 4.1e-07,  # LOAD + ADD energy
            },
            "thermal": {
                "base_temp": 25.0,
                "heat_factor": 0.1,
                "heat_capacity": 100.0,  # J/K, adjust based on hardware
                "thermal_resistance": 0.5,  # K/W, adjust based on hardware
            },
            # real-time cycle cost model: cycles per opcode (sim cycles)
            "cycles": {
                "ADD": 4.5e-08,
                "SUB": 1,
                "MUL": 3,
                "DIV": 10,
                "LOAD": 4.0000000000000003e-07,
                "STORE": 4.0000000000000003e-07,
                "JMP": 1,
                "BR_IF": 2,
                "LABEL": 0,
                "BRANCH": 1,
                "FUSED_LOAD_ADD": 2,  # cheaper than LOAD(3)+ADD(1)=4
            },
            "cores": 4,
            "energy_unit": 1.0,  # Updated to Joules
            "sim_clock_hz": 343180684.9654721,  # Measured from calibrate_cycles.py
            "memory_limit": None,  # optional hard cap, or None for no limit
        }


class Config:
    """Configuration class."""

    def __init__(self, config_dict=None) -> None:
        if config_dict is None:
            config_dict = load_config("config.json")
        self.energy = config_dict["energy"]
        self.thermal = config_dict["thermal"]
        self.cycles = config_dict.get("cycles", {})
        self.cores = config_dict["cores"]
        self.energy_unit = config_dict.get("energy_unit", 1.0)
        self.sim_clock_hz = config_dict.get("sim_clock_hz", 17183382.42)
        self.memory_limit = config_dict.get("memory_limit", None)
