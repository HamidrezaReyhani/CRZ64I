#!/usr/bin/env python3
"""
Compute sim_clock_hz by:
 - running CRZ simulator on same logical program and reading sim_cycles
 - running native microbench and measuring wall time (or perf cycles)
 - compute sim_clock_hz = sim_cycles / wall_time

Usage:
  PYTHONPATH=src ./venv/bin/python3 tools/calibrate_cycles_full.py --n_native 1000000
"""
import sys, subprocess, time, json, argparse, re
from pathlib import Path
sys.path.insert(0,'src')
from crz.compiler.parser import parse_text
from crz.compiler.codegen_sim import codegen
from crz.simulator.simulator import Simulator

def run_native(cmd):
    t0 = time.time()
    subprocess.run(cmd, check=True)
    t1 = time.time()
    return t1 - t0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n_native', type=int, default=1000000)
    args = ap.parse_args()
    # load a small CRZ program that matches native micro_add pattern
    ex = Path('examples/micro_add.crz').read_text()
    # remove commented N overrides and replace N token (best effort)
    code = '\n'.join([l for l in ex.splitlines() if not (l.strip().startswith('#') and '=' in l)]) 
    code = code.replace('N', str(args.n_native))
    prog = parse_text(code)
    ops = codegen(prog)
    sim = Simulator()
    res = sim.run(ops)  # expect (cycles, energy, temp, ...)
    sim_cycles = res[0]
    # run native
    wall = run_native(['./bench/micro_add', str(args.n_native)])
    sim_clock_hz = sim_cycles / wall if wall>0 else None
    out = {'sim_cycles': sim_cycles, 'wall_native_s': wall, 'sim_clock_hz': sim_clock_hz}
    Path('bench/calib_cycles.json').write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))

if __name__=='__main__':
    main()
