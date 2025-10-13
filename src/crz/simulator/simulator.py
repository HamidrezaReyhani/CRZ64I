"""

CRZ64I Simulator

Executes CRZ64I ops, tracks energy, thermal hotspots.
"""

import json
from typing import Dict, List, Any
from pathlib import Path
from ..config import load_config, Config
from crz.compiler.parser import parse_text
from crz.compiler.codegen_sim import codegen
from ..compiler.ast import Instr



def compile_file(path: str):
    with open(path, 'r') as f:
        code = f.read()
    program = parse_text(code)
    return codegen(program)


class Simulator:
    """CRZ64I Simulator."""

    def __init__(self, config = None):
        if config is None:
            config = Config()
        elif isinstance(config, dict):
            config = Config(config)
        self.config = config
        self.regs: Dict[str, int] = {f"r{i}": 0 for i in range(32)}
        self.memory: List[int] = []
        self.pc = 0
        self.flags = {"Z": 0, "N": 0}
        self.energy_used = 0.0
        self.thermal_map: Dict[str, float] = {}  # Component to temperature
        self.labels: Dict[str, int] = {}
        self.backup_regs: Dict[str, int] = {}
        self.sandbox_allow_io = False
        self.sandbox_allow_dma = False
        self.cycles = 0
        self._op_counts: Dict[str, int] = {}
        self.wall_clock_s = 0.0  # Wall clock time in seconds

    def check_memory_bounds(self, addr: int):
        """Check and auto-grow memory bounds."""
        # reject negative addresses
        if addr < 0:
            raise ValueError(f"Memory access out of bounds: negative address {addr}")

        # optional max guard if config has memory_limit
        mem_limit = getattr(self.config, 'memory_limit', None)
        if mem_limit is not None and addr >= mem_limit:
            raise ValueError(f"Memory access out of bounds: requested {addr} >= memory_limit {mem_limit}")

        # auto-grow: extend underlying memory list to include addr
        if addr >= len(self.memory):
            needed = addr - len(self.memory) + 1
            # keep growth deterministic and efficient
            self.memory.extend([0] * needed)

    def get_val(self, s: str) -> int:
        """Get value from register or literal."""
        s = s.strip()
        if '+' in s:
            left, right = s.split('+', 1)
            return self.get_val(left) + self.get_val(right)
        elif s.isdigit() or (s.startswith('-') and s[1:].isdigit()):
            return int(s)
        return self.regs.get(s, 0)

    def execute_op(self, mnemonic: str, operands: List[str]):
        """Execute a single operation."""
        # --- compute energy for this opcode (per-op energy from config) ---
        energy = self.config.energy.get(mnemonic, 0.0)

        # --- compute cycles cost for this opcode (real-time cost model) ---
        cost_cycles = self.config.cycles.get(mnemonic, 1)

        # increment simulator cycle counter by opcode cost
        # (simulator stores total cycles executed)
        self.cycles += cost_cycles

        # convert cycles -> real time dt using sim_clock_hz
        sim_clock_hz = getattr(self.config, "sim_clock_hz", 1.0)
        dt = cost_cycles / float(sim_clock_hz) if sim_clock_hz > 0 else 0.0

        # --- energy accounting ---
        # energy in config is per-op in Joules (energy_unit should be 1.0 for J)
        energy_joule = energy * getattr(self.config, "energy_unit", 1.0)
        # accumulate energy (total Joules)
        self.energy_used += energy_joule

        # update wall-clock-like measurement reported by simulator
        self.wall_clock_s += dt

        # update thermal model using duration dt and energy_joule
        # uses update_thermal_advanced which expects energy in Joules and dt computed there if needed
        if hasattr(self, "update_thermal_advanced"):
            # call with mnemonic and energy_joule (function will compute dt from cycles if needed)
            try:
                self.update_thermal_advanced(mnemonic, energy_joule, dt=dt, cycles=cost_cycles)
            except TypeError:
                # backward compatibility: if update_thermal_advanced signature differs, call older form
                self.update_thermal_advanced(mnemonic, energy_joule)

        self._op_counts[mnemonic] = self._op_counts.get(mnemonic, 0) + 1

        if mnemonic == "ADD":
            rd, rs1, rs2 = operands
            self.regs[rd] = self.get_val(rs1) + self.get_val(rs2)
        elif mnemonic == "SUB":
            rd, rs1, rs2 = operands
            self.regs[rd] = self.get_val(rs1) - self.get_val(rs2)
        elif mnemonic == "MUL":
            rd, rs1, rs2 = operands
            self.regs[rd] = self.get_val(rs1) * self.get_val(rs2)
        elif mnemonic == "DIV":
            rd, rs1, rs2 = operands
            rs2_val = self.get_val(rs2)
            if rs2_val == 0:
                self.regs[rd] = 0  # Handle division by zero
            else:
                self.regs[rd] = self.get_val(rs1) // rs2_val
        elif mnemonic == "LOAD":
            rd, mem_ref = operands
            addr_str = mem_ref[1:-1]  # Remove [ ]
            addr = self.get_val(addr_str)
            self.check_memory_bounds(addr)
            self.regs[rd] = self.memory[addr]
        elif mnemonic == "STORE":
            rs, mem_ref = operands
            addr_str = mem_ref[1:-1]
            addr = self.get_val(addr_str)
            self.check_memory_bounds(addr)
            self.memory[addr] = self.regs[rs]
        elif mnemonic == "JMP":
            label = operands[0]
            if label.isdigit():
                self.pc = int(label) - 1
            else:
                self.pc = self.labels[label] - 1
        elif mnemonic == "JZ":
            if self.flags["Z"]:
                label = operands[0]
                if label.isdigit():
                    self.pc = int(label) - 1
                else:
                    self.pc = self.labels[label] - 1
        elif mnemonic == "JNZ":
            if not self.flags["Z"]:
                label = operands[0]
                if label.isdigit():
                    self.pc = int(label) - 1
                else:
                    self.pc = self.labels[label] - 1
        elif mnemonic == "BR_IF":
            if len(operands) == 2:
                # Old format: flag, label
                flag, label = operands
                if self.flags[flag]:
                    if label.isdigit():
                        self.pc = int(label) - 1
                    else:
                        self.pc = self.labels[label] - 1
            elif len(operands) == 4:
                # New format: condition, var, end, label
                condition, var, end, label = operands
                if condition == "LT":
                    if self.get_val(var) < self.get_val(end):
                        if label.isdigit():
                            self.pc = int(label) - 1
                        else:
                            self.pc = self.labels[label] - 1
                # Add other conditions if needed
        elif mnemonic == "LABEL":
            self.labels[operands[0]] = self.pc
        elif mnemonic == "CALL":
            # Simple call, no stack
            self.pc = self.labels[operands[0]] - 1
        elif mnemonic == "RET":
            # Simple ret
            pass
        elif mnemonic == "FUSED_ADD_MUL":
            # Fused add mul: rd = rs1 + rs2 * rs3
            rd, rs1, rs2, rs3 = operands
            self.regs[rd] = self.get_val(rs1) + self.get_val(rs2) * self.get_val(rs3)
        elif mnemonic == "FUSED_LOAD_ADD":
            # supported operand formats:
            #  - new: [load_dst, add_dst, mem_ref, imm_or_reg]
            #  - old/fallback: [add_dst, mem_ref, imm_or_reg]  (back-compat)
            if len(operands) == 4:
                load_dst, add_dst, mem_ref, imm = operands
            elif len(operands) == 3:
                # legacy: no explicit load_dst -> assume the ADD source register
                # but legacy loses original load_dst; to preserve semantics best
                # we treat add_dst as both load_dst and add_dst (least bad fallback)
                add_dst, mem_ref, imm = operands
                load_dst = add_dst
            else:
                raise ValueError(f"FUSED_LOAD_ADD: unexpected operands {operands}")

            # normalize mem_ref: accept "[a + i]" or "a + i"
            if isinstance(mem_ref, str) and mem_ref.startswith('[') and mem_ref.endswith(']'):
                addr_str = mem_ref[1:-1]
            else:
                addr_str = mem_ref

            addr = self.get_val(addr_str)
            self.check_memory_bounds(addr)

            # load value
            val = self.memory[addr]
            # write load destination (preserve semantics of LOAD)
            self.regs[load_dst] = val

            # resolve immediate/reg for add
            try:
                imm_val = int(imm)
            except Exception:
                imm_val = self.get_val(imm)

            # compute add result and write
            self.regs[add_dst] = val + imm_val

            # account for STORE energy/cycles handled elsewhere (this op only does load+add)
            # update op counts:
            self._op_counts["FUSED_LOAD_ADD"] = self._op_counts.get("FUSED_LOAD_ADD", 0) + 1
            # energy, cycles, thermal already handled earlier in execute_op (top of function)
        elif mnemonic == "SAVE_DELTA":
            self.backup_regs = self.regs.copy()
        elif mnemonic == "RESTORE_DELTA":
            self.regs = self.backup_regs.copy()
        elif mnemonic == "WRITE_IO":
            if not self.sandbox_allow_io:
                raise PermissionError("WRITE_IO not allowed in sandbox")
            # Simulate IO write
            pass
        elif mnemonic == "DMA_START":
            if not self.sandbox_allow_dma:
                raise PermissionError("DMA_START not allowed in sandbox")
            # Simulate DMA start
            pass
        # Update flags
        if mnemonic in ["ADD", "SUB", "MUL", "DIV", "LOAD", "FUSED_ADD_MUL", "FUSED_LOAD_ADD"]:
            rd = operands[0]
            self.flags["Z"] = 1 if self.regs[rd] == 0 else 0
            self.flags["N"] = 1 if self.regs[rd] < 0 else 0

    def update_thermal_advanced(self, mnemonic: str, energy_joule: float, dt: float = None, cycles: int = None):
        """Update thermal hotspots using physics-based heating over duration dt (seconds).
        energy_joule: energy consumed in this opcode (Joules).
        dt: duration in seconds (optional). If not provided, will attempt to compute using cycles and config.sim_clock_hz.
        """
        component = "alu" if mnemonic in ["ADD", "SUB", "MUL", "DIV", "FUSED_LOAD_ADD"] else "control"
        current_temp = self.thermal_map.get(component, self.config.thermal.get("base_temp", 25.0))
        ambient_temp = self.config.thermal.get("base_temp", 25.0)
        heat_capacity = self.config.thermal.get("heat_capacity", 100.0)  # J/K
        thermal_resistance = self.config.thermal.get("thermal_resistance", 0.5)  # K/W
        if dt is None:
            if cycles is not None:
                sim_clock_hz = getattr(self.config, 'sim_clock_hz', 1.0)
                dt = cycles / float(sim_clock_hz) if sim_clock_hz > 0 else 0.0
            else:
                # fallback small dt
                dt = 0.0
        # instantaneous power over dt (avoid div by zero)
        power_w = (energy_joule / dt) if dt and dt > 0.0 else 0.0
        # Newton cooling + heating: dT = (power - (T - ambient)/R) * (dt / C)
        dT = (power_w - (current_temp - ambient_temp) / thermal_resistance) * (dt / heat_capacity) if dt and dt > 0.0 else 0.0
        new_temp = current_temp + dT
        self.thermal_map[component] = new_temp

    def get_reg(self, reg: str) -> int:
        return self.regs[reg]

    def set_reg(self, reg: str, val: int):
        self.regs[reg] = val

    def get_flag(self, flag: str) -> bool:
        return self.flags[flag] == 1

    def run_program(self, ops):
        """Run a list of ops."""
        # Pre-build labels
        self.labels = {}
        for i, op in enumerate(ops):
            if hasattr(op, 'mnemonic') and op.mnemonic == "LABEL":
                self.labels[op.operands[0]] = i
            elif isinstance(op, dict) and op.get("op") == "LABEL":
                self.labels[op["args"][0]] = i
        while self.pc < len(ops):
            op = ops[self.pc]
            if hasattr(op, 'mnemonic'):
                mnemonic = op.mnemonic
                operands = op.operands
            elif isinstance(op, dict):
                mnemonic = op["op"]
                operands = op["args"]
            else:
                print(f"Unknown op type: {type(op)}")
                self.pc += 1
                continue
            self.execute_op(mnemonic, operands)
            self.pc += 1

    def run(self, ops: List[Dict[str, Any]], metrics: bool = True):
        """Run ops and optionally return metrics."""
        self.cycles = 0
        self.energy_used = 0.0
        self._op_counts = {}
        self.run_program(ops)
        if metrics:
            cycles = self.cycles
            energy = self.energy_used
            temp = max(self.thermal_map.values()) if self.thermal_map else 25.0
            return cycles, energy, temp
        return None

    def get_energy_report(self) -> Dict[str, float]:
        """Get energy report."""
        return {"total_energy": self.energy_used, "thermal_hotspots": self.thermal_map}

    def get_state(self):
        """Get current simulator state for semantic equivalence checks."""
        return {"regs": dict(self.regs), "memory": {str(i): v for i, v in enumerate(self.memory)}}
