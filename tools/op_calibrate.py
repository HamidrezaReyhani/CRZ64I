#!/usr/bin/env python3
"""
Measure energy per-op using bench microbenchmarks.
Usage:
  sudo ./venv/bin/python3 tools/op_calibrate.py --op ADD --iters 20000000
  sudo ./venv/bin/python3 tools/op_calibrate.py --op LOAD --iters 2000000 --size 5000000
"""
import os, time, subprocess, argparse

def find_rapl():
    for root, dirs, files in os.walk('/sys/class/powercap'):
        for f in files:
            if f == 'energy_uj':
                return os.path.join(root, f)
    return None

def read_rapl(path):
    try:
        with open(path,'r') as fh:
            return int(fh.read().strip())
    except:
        return None

def run_and_measure(cmd):
    rapl = find_rapl()
    if rapl:
        before = read_rapl(rapl)
        t0 = time.time()
        subprocess.run(cmd, check=True)
        t1 = time.time()
        after = read_rapl(rapl)
        if before is None or after is None:
            return None, t1-t0
        return (after - before) / 1e6, t1 - t0   # Joules, seconds
    else:
        perf_cmd = ['perf','stat','-e','power/energy-pkg/','--'] + cmd
        p = subprocess.run(perf_cmd, capture_output=True, text=True)
        for line in p.stderr.splitlines():
            if 'energy' in line and 'pkg' in line:
                try:
                    val = float(line.strip().split()[0])
                    return val, None
                except:
                    pass
        return None, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--op', required=True, choices=['ADD','LOAD'], help='Which microbench to run')
    ap.add_argument('--iters', type=int, default=10000000, help='Number of iterations/ops')
    ap.add_argument('--size', type=int, default=5000000, help='Array size for LOAD bench')
    args = ap.parse_args()

    if args.op == 'ADD':
        cmd = ['./bench/micro_add', str(args.iters)]
        J, t = run_and_measure(cmd)
        print("energy(J):", J, "time(s):", t, "ops:", args.iters)
        if J:
            print("energy per op (J):", J/float(args.iters))
    else:  # LOAD
        cmd = ['./bench/micro_load', str(args.iters), str(args.size)]
        J, t = run_and_measure(cmd)
        print("energy(J):", J, "time(s):", t, "loads:", args.iters)
        if J:
            print("energy per load (J):", J/float(args.iters))

if __name__ == '__main__':
    main()
