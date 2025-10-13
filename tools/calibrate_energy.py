#!/usr/bin/env python3
import subprocess, time, os, sys, math

RAPL_PATH = None
# detect RAPL path
for root, dirs, files in os.walk("/sys/class/powercap"):
    for f in files:
        if f == "energy_uj":
            RAPL_PATH = os.path.join(root, f)
            break
    if RAPL_PATH:
        break


def read_rapl():
    if not RAPL_PATH:
        return None
    with open(RAPL_PATH, "r") as fh:
        return int(fh.read().strip())


def run_and_measure(cmd, args):
    if RAPL_PATH:
        before = read_rapl()
        t0 = time.time()
        subprocess.run([cmd] + args, check=True)
        t1 = time.time()
        after = read_rapl()
        energy_uj = after - before
        return energy_uj / 1e6, t1 - t0  # Joule, seconds
    else:
        # fallback to perf: perf prints to stderr energy-pkg in joules sometimes in uJ
        perf_cmd = ["perf", "stat", "-e", "energy-pkg", "--"] + [cmd] + args
        p = subprocess.run(perf_cmd, capture_output=True, text=True)
        # parse stderr for 'energy-pkg' line
        for line in p.stderr.splitlines():
            if "energy" in line and "pkg" in line:
                tokens = line.strip().split()
                # tokens like:  12345.00 joules energy-pkg
                try:
                    val = float(tokens[0])
                    return val, None
                except:
                    continue
        return None, None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: calibrate_energy.py [micro_add|micro_load] [N] [size_for_load]")
        sys.exit(1)
    prog = sys.argv[1]
    if prog == "micro_add":
        cmd = "./bench/micro_add"
        N = [sys.argv[2]] if len(sys.argv) > 2 else ["100000000"]
        J, s = run_and_measure(cmd, N)
        print("result energy(J):", J, "time(s):", s, "ops:", int(N[0]))
        if J:
            print("energy per op (J):", J / float(N[0]))
    elif prog == "micro_load":
        cmd = "./bench/micro_load"
        N = sys.argv[2] if len(sys.argv) > 2 else "1000000"
        size = sys.argv[3] if len(sys.argv) > 3 else "10000000"
        J, s = run_and_measure(cmd, [N, size])
        print("energy(J):", J, "time(s):", s, "loads:", int(N))
        if J:
            print("energy per load (J):", J / float(N))
    else:
        print("unknown prog")
