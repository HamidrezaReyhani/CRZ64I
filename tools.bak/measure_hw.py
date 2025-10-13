#!/usr/bin/env python3
import os, subprocess, time, sys

# try find energy_uj path
def find_rapl():
    for root,dirs,files in os.walk('/sys/class/powercap'):
        for f in files:
            if f == 'energy_uj':
                return os.path.join(root,f)
    return None

RAPL = find_rapl()

def read_rapl(path):
    with open(path,'r') as fh:
        return int(fh.read().strip())

def run_measure(cmd, args):
    if RAPL:
        before = read_rapl(RAPL)
        t0 = time.time()
        subprocess.run([cmd]+args, check=True)
        t1 = time.time()
        after = read_rapl(RAPL)
        energy_j = (after - before)/1e6
        return energy_j, t1-t0, None
    else:
        # fallback perf
        perf_cmd = ['perf','stat','-e','energy-pkg,cycles,branches','--']+[cmd]+args
        p = subprocess.run(perf_cmd, capture_output=True, text=True)
        # parse stderr for energy-pkg and cycles
        energy = None; cycles = None
        for line in p.stderr.splitlines():
            if 'energy-pkg' in line:
                try:
                    energy = float(line.strip().split()[0])
                except: pass
            if 'cycles' in line and 'cycles:' in line:
                try: cycles = int(line.strip().split()[0].replace(',',''))
                except: pass
        return energy, None, cycles

if __name__=='__main__':
    if len(sys.argv) < 2:
        print("usage: measure_hw.py <cmd> [args...]")
        sys.exit(1)
    cmd = sys.argv[1]
    args = sys.argv[2:]
    e, t, cycles = run_measure(cmd, args)
    print("energy_J:", e, "time_s:", t, "cycles:", cycles)
