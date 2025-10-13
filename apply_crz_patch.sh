#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "==> Creating backups (if not present)..."
mkdir -p backups
cp -n src crz_src_bak || true
cp -n src/crz/config.py src/crz/config.py.bak || true
cp -n src/crz/simulator/simulator.py src/crz/simulator/simulator.py.bak || true

echo "==> Writing docs/isa.md..."
mkdir -p docs
cat > docs/isa.md <<'MD'
# CRZ64I — ISA specification, fusion & calibration guide

(این فایل یک مرجع جامع برای ISA، مدل هزینه‌ها، مدل حرارتی، و فرآیند کالیبراسیون است.)
...
(مختصرشده؛ full guidance در repo)
MD

echo "==> Writing tools/op_calibrate.py..."
mkdir -p tools
cat > tools/op_calibrate.py <<'PY'
#!/usr/bin/env python3
# per-op calibration harness (see conversation for usage)
import os, time, subprocess, argparse
def find_rapl():
    for root, dirs, files in os.walk('/sys/class/powercap'):
        for f in files:
            if f == 'energy_uj':
                return os.path.join(root,f)
    return None
def read_rapl(p):
    try:
        with open(p,'r') as fh:
            return int(fh.read().strip())
    except:
        return None
def run_prog_and_measure(cmd):
    rapl=find_rapl()
    if rapl:
        b=read_rapl(rapl)
        t0=time.time()
        subprocess.run(cmd,check=True)
        t1=time.time()
        a=read_rapl(rapl)
        if a is None or b is None:
            return None, t1-t0
        return (a-b)/1e6, t1-t0
    else:
        perf_cmd=['perf','stat','-e','energy-pkg','--']+cmd
        p=subprocess.run(perf_cmd,capture_output=True,text=True)
        for line in p.stderr.splitlines():
            if 'energy' in line and 'pkg' in line:
                try:
                    v=float(line.split()[0])
                    return v, None
                except:
                    pass
        return None, None

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--op', required=True, choices=['ADD','LOAD'])
    ap.add_argument('--iters', type=int, default=1000000)
    ap.add_argument('--size', type=int, default=5000000)
    args=ap.parse_args()
    if args.op=='ADD':
        cmd=['./bench/micro_add', str(args.iters)]
        J,wall=run_prog_and_measure(cmd)
        print("energy(J):",J,"time(s):",wall,"ops:",args.iters)
        if J: print("energy/op (J):", J/float(args.iters))
    else:
        cmd=['./bench/micro_load', str(args.iters), str(args.size)]
        J,wall=run_prog_and_measure(cmd)
        print("energy(J):",J,"time(s):",wall,"loads:",args.iters)
        if J: print("energy/load (J):", J/float(args.iters))
PY
chmod +x tools/op_calibrate.py

echo "==> Writing .github workflow (ci_calibrate.yml)..."
mkdir -p .github/workflows
cat > .github/workflows/ci_calibrate.yml <<'YML'
name: CI - calibrate & smoke
on: [ workflow_dispatch ]
jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with: { python-version: '3.11' }
      - run: |
          python -m venv venv
          . venv/bin/activate
          pip install -U pip
          pip install lark
          . venv/bin/activate && PYTHONPATH=src python -m pytest tests/ -q
YML

echo "==> Patching src/crz/config.py (inplace)..."
python3 - <<'PY'
from pathlib import Path
p=Path('src/crz/config.py')
s=p.read_text()
# replace default energy block by a calibrated example block
old_start = 'return {'
if 'FUSED_LOAD_ADD' in s and '"energy"' in s:
    # naive replace of the literal default-return dictionary block (best-effort)
    s = s.replace(
        '"ADD": 1.0,', '"ADD": 6e-08,'
    ).replace(
        '"LOAD": 0.5,', '"LOAD": 3.5e-07,'
    )
# ensure cycles block exists
if '"cycles"' not in s:
    insert_after = '"thermal": {'
    if insert_after in s:
        s = s.replace('"thermal": {', '"thermal": {')
# set energy_unit and sim_clock_hz defaults
s = s.replace('self.energy_unit = config_dict.get("energy_unit", 1e-9)', 'self.energy_unit = config_dict.get("energy_unit", 1.0)')
s = s.replace('self.sim_clock_hz = config_dict.get("sim_clock_hz", 2.0e8)', 'self.sim_clock_hz = config_dict.get("sim_clock_hz", 17183382.42)')
p.write_text(s)
print("patched config.py (please review src/crz/config.py.bak and src/crz/config.py).")
PY

echo "==> Patching src/crz/simulator/simulator.py (inplace)..."
python3 - <<'PY'
from pathlib import Path
p=Path('src/crz/simulator/simulator.py')
s=p.read_text()

# add wall_clock_s and cycles mapping if not present
if "self.wall_clock_s" not in s:
    s = s.replace("self.cycles = 0", "self.cycles = 0  # simulated cycles\n        self.wall_clock_s = 0.0  # simulated wall-clock (s)")

# update check_memory_bounds signature if needed
s = s.replace("def check_memory_bounds(self, addr):", "def check_memory_bounds(self, addr: int):")

# modify execute_op: insert energy/cycle accounting before opcode handling
if "energy_per_op" not in s:
    s = s.replace("def execute_op(self, mnemonic, operands):", "def execute_op(self, mnemonic: str, operands: list):")
    s = s.replace(
        "        energy = self.config.energy.get(mnemonic, 0.0)\n        self.energy_used += energy * self.config.energy_unit\n        self.update_thermal_advanced(mnemonic, energy)\n        self.cycles += 1\n",
        "        # per-op energy (J)\n        energy_per_op = self.config.energy.get(mnemonic, 0.0)\n        energy_joule = energy_per_op * getattr(self.config, 'energy_unit', 1.0)\n        # cycles cost\n        cost_cycles = self.config.cycles.get(mnemonic, 1)\n        self.cycles += cost_cycles\n        sim_clock_hz = getattr(self.config, 'sim_clock_hz', 1.0)\n        dt = cost_cycles / float(sim_clock_hz) if sim_clock_hz > 0 else 0.0\n        self.wall_clock_s += dt\n        self.energy_used += energy_joule\n        try:\n            self.update_thermal_advanced(mnemonic, energy_joule, dt=dt, cycles=cost_cycles)\n        except TypeError:\n            self.update_thermal_advanced(mnemonic, energy_joule)\n"
    )

# update thermal method signature if present
s = s.replace("def update_thermal_advanced(self, mnemonic: str, energy: float):", "def update_thermal_advanced(self, mnemonic: str, energy_joule: float, dt: float = None, cycles: int = None):")
s = s.replace("energy_joule = energy * self.config.energy_unit  # Convert to Joules\n        power_w = energy_joule / dt  # Watts", "power_w = (energy_joule / dt) if dt and dt>0.0 else 0.0")
s = s.replace("return {\"regs\": dict(self.regs), \"memory\": dict(self.memory)}", "return {\"regs\": dict(self.regs), \"memory\": {str(i): v for i, v in enumerate(self.memory)}}")

p.write_text(s)
print("patched simulator.py (please review src/crz/simulator/simulator.py.bak and src/crz/simulator/simulator.py).")
PY

echo "==> Done. Please run tests and review changes:"
echo "   . venv/bin/activate"
echo "   PYTHONPATH=src ./venv/bin/python3 -m pytest tests/ -q"
echo "   PYTHONPATH=src ./venv/bin/python3 tools/measure_micro_add.py --n 10000 --runs 3 --verbose"
