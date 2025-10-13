#!/usr/bin/env python3
import argparse, re
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--add", type=float, help="energy per ADD (J)")
ap.add_argument("--load", type=float, help="energy per LOAD (J)")
ap.add_argument("--store", type=float, help="energy per STORE (J)")
ap.add_argument("--fused", type=float, help="energy per FUSED_LOAD_ADD (J)")
ap.add_argument("--sim_clock_hz", type=float, help="sim_clock_hz")
args = ap.parse_args()

p = Path("src/crz/config.py")
if not p.exists():
    raise SystemExit("src/crz/config.py not found")
text = p.read_text()
bak = p.with_suffix(".py.bak")
if not bak.exists():
    bak.write_text(text)


def replace_key(key, val, txt):
    if val is None:
        return txt
    pattern = rf'("{key}"\s*:\s*)([0-9eE+\-\.]+)'
    return re.sub(pattern, lambda m: m.group(1) + repr(val), txt)


repls = {
    "ADD": args.add,
    "LOAD": args.load,
    "STORE": args.store,
    "FUSED_LOAD_ADD": args.fused,
}

for k, v in repls.items():
    text = replace_key(k, v, text)

if args.sim_clock_hz is not None:
    text = re.sub(
        r'("sim_clock_hz"\s*:\s*)[0-9eE+\-\.]+',
        lambda m: m.group(1) + repr(args.sim_clock_hz),
        text,
    )

p.write_text(text)
print("Updated src/crz/config.py (backup at {})".format(bak))
