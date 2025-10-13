#!/usr/bin/env python3
"""
tools/op_calibrate_full.py
Run many repeats of microbench, use RAPL if available (handle wraparound),
compute median energy per op and emit JSON + patch for src/crz/config.py.

Usage:
  sudo ./venv/bin/python3 tools/op_calibrate_full.py --op ADD --iters 20000000 --runs 7
  sudo ./venv/bin/python3 tools/op_calibrate_full.py --op LOAD --iters 2000000 --size 5000000 --runs 7
"""
import os, time, subprocess, argparse, statistics, json, re
from pathlib import Path


def find_rapl():
    for root, dirs, files in os.walk("/sys/class/powercap"):
        if "energy_uj" in files:
            return os.path.join(root, "energy_uj"), os.path.join(
                root, "max_energy_range_uj"
            )
    return None, None


def read_int_file(path):
    try:
        with open(path, "r") as f:
            return int(f.read().strip())
    except:
        return None


def measure_once(cmd, rapl_path, max_range_path):
    if rapl_path:
        before = read_int_file(rapl_path)
        t0 = time.time()
        subprocess.run(cmd, check=True)
        t1 = time.time()
        after = read_int_file(rapl_path)
        if before is None or after is None:
            return None, t1 - t0
        max_range = read_int_file(max_range_path) or 0
        delta = after - before
        if max_range and delta < 0:
            # wraparound
            delta = (after + max_range) - before
        return delta / 1e6, t1 - t0  # Joules, seconds
    else:
        perf_cmd = ["perf", "stat", "-x,", "-e", "power/energy-pkg", "--"] + cmd
        p = subprocess.run(perf_cmd, capture_output=True, text=True)
        # parse perf csv-like stderr lines
        for line in p.stderr.splitlines():
            # perf sometimes prints: "12345.00, joules, power/energy-pkg"
            parts = [s.strip() for s in line.split(",") if s.strip()]
            if len(parts) >= 3 and "power/energy-pkg" in parts[-1]:
                try:
                    val = float(parts[0])
                    return val, None
                except:
                    pass
        # fallback parse textual
        for line in p.stderr.splitlines():
            if "energy" in line and "pkg" in line:
                toks = re.findall(r"([0-9]+\.[0-9]+|[0-9]+)", line)
                if toks:
                    try:
                        return float(toks[0]), None
                    except:
                        pass
        return None, None


def run_many(op, iters, size, runs, pin_core):
    rapl_path, max_range = find_rapl()
    results = []
    for i in range(runs):
        if op == "ADD":
            cmd = ["./bench/micro_add", str(iters)]
        else:
            cmd = ["./bench/micro_load", str(iters), str(size)]
        if pin_core is not None:
            cmd = ["taskset", "-c", str(pin_core)] + cmd
        J, t = measure_once(cmd, rapl_path, max_range)
        results.append((J, t))
        print(f"run {i}: energy(J)={J} time(s)={t}")
    # filter out None energy results
    energies = [r[0] for r in results if r[0] is not None]
    times = [r[1] for r in results if r[1] is not None]
    if not energies:
        return None
    median_J = statistics.median(energies)
    mean_J = statistics.mean(energies)
    median_t = statistics.median([x for x in times if x is not None]) if times else None
    per_op = median_J / float(iters)
    return {
        "op": op,
        "iters": iters,
        "runs": runs,
        "median_energy_J": median_J,
        "mean_energy_J": mean_J,
        "median_time_s": median_t,
        "energy_per_op_J": per_op,
        "raw": results,
    }


def write_patch(cfg_path: Path, key_name: str, value: float, out_patch: Path):
    old = cfg_path.read_text()
    new = old
    # Replace inside "energy" dict pattern "KEY": <num>
    pat = r'("' + re.escape(key_name) + r'"\s*:\s*)([0-9eE\+\-\.]+)'
    if re.search(pat, old):
        new = re.sub(pat, lambda m: m.group(1) + repr(value), old)
    else:
        # fallback: insert into energy dict (naive)
        new = old.replace(
            '"energy": {',
            '"energy": {\n                "' + key_name + '": ' + repr(value) + ",",
        )
    # write patch as unified diff
    import difflib

    diff = difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=str(cfg_path),
        tofile=str(cfg_path) + ".updated",
    )
    out_patch.write_text("".join(diff))
    # also write the new file
    backup = cfg_path.with_suffix(".bak")
    if not backup.exists():
        cfg_path.rename(backup)
        cfg_path.write_text(new)
    else:
        cfg_path.write_text(new)
    return out_patch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--op", required=True, choices=["ADD", "LOAD"])
    ap.add_argument("--iters", type=int, default=10000000)
    ap.add_argument("--size", type=int, default=5000000)
    ap.add_argument("--runs", type=int, default=7)
    ap.add_argument("--pin", type=int, default=0)
    ap.add_argument("--write-patch", action="store_true")
    args = ap.parse_args()

    print(
        "WARNING: Run as sudo for RAPL access (recommended). Using pin/core and performance governor reduces noise."
    )
    res = run_many(args.op, args.iters, args.size, args.runs, args.pin)
    if res is None:
        print("No valid energy samples collected (perf/RAPL fallback failed).")
        return
    out = Path("bench") / f"calib_{args.op.lower()}.json"
    out.write_text(json.dumps(res, indent=2))
    print("Wrote", out)
    print("energy per op (J):", res["energy_per_op_J"])
    if args.write_patch:
        cfg = Path("src/crz/config.py")
        patch = Path("crz_calib_patch.diff")
        key = "ADD" if args.op == "ADD" else "LOAD"
        write_patch(cfg, key, res["energy_per_op_J"], patch)
        print("Patch written to", patch)


if __name__ == "__main__":
    main()
