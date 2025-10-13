#!/usr/bin/env python3
from pathlib import Path
import json, re, sys

p = Path("src/crz/config.py")
text = p.read_text()

# مقادیر جدید را اینجا قرار بده (مقادیر نمونه — جایگزین کن با خروجی واقعی)
new_values = {
    "ADD": 6e-08,
    "LOAD": 3.5e-07,
    "STORE": 3.5e-07,
    "FUSED_LOAD_ADD": 4.1e-07,
    "sim_clock_hz": 17183382.42,
    "energy_unit": 1.0,
}

# replace simple numeric literal patterns for those keys (robust-ish)
for k, v in new_values.items():
    if k == "sim_clock_hz" or k == "energy_unit":
        # replace top-level assignment in the dictionary near sim_clock_hz
        text = re.sub(r'("sim_clock_hz"\s*:\s*)[0-9eE+\-\.]+', r"\1" + repr(v), text)
        text = re.sub(r'("energy_unit"\s*:\s*)[0-9eE+\-\.]+', r"\1" + repr(v), text)
    else:
        # replace inside "energy" or "cycles" dict entries
        pattern = r'("' + k + r'"\s*:\s*)[0-9eE+\-\.]+'
        text = re.sub(pattern, lambda m: m.group(1) + repr(v), text)

p.write_text(text)
print("config.py updated. Please review src/crz/config.py.bak and src/crz/config.py")
