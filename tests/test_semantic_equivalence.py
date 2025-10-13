import sys

sys.path.insert(0, "src")
from crz.compiler.parser import parse_text
from crz.compiler.codegen_sim import codegen
from crz.compiler.passes import run_passes
from crz.simulator.simulator import Simulator


def run_uncompiled(code):
    prog = parse_text(code)
    ops = codegen(prog)
    sim = Simulator()
    sim.run(ops)
    return sim.get_state()


def run_compiled(code):
    prog = parse_text(code)
    compiled_prog = run_passes(prog, ["fusion", "reversible"])
    ops = codegen(compiled_prog)
    sim = Simulator()
    sim.run(ops)
    return sim.get_state()


def compare_states(s1, s2):
    diffs = []
    for r in sorted(set(list(s1["regs"].keys()) + list(s2["regs"].keys()))):
        a = s1["regs"].get(r, 0)
        b = s2["regs"].get(r, 0)
        if isinstance(a, float) or isinstance(b, float):
            if abs(a - b) > 1e-9:
                diffs.append(f"R{r}: {a} != {b}")
        else:
            if a != b:
                diffs.append(f"R{r}: {a} != {b}")
    for addr in sorted(set(list(s1["memory"].keys()) + list(s2["memory"].keys()))):
        a = s1["memory"].get(addr, 0)
        b = s2["memory"].get(addr, 0)
        if a != b:
            diffs.append(f"MEM[{addr}]: {a} != {b}")
    return diffs


def test_equivalence_micro_add():
    # Use the same substitution as measure_micro_add.py
    import re

    with open("examples/micro_add.crz", "r") as f:
        lines = f.readlines()
    # Remove lines starting with # and containing =
    lines = [
        line
        for line in lines
        if not (line.strip().startswith("#") and "=" in line.strip())
    ]
    code = "".join(lines)
    # Replace N in the code
    code = code.replace("N", "100")
    # Replace uppercase R with lowercase r for registers (e.g., R1 -> r1)
    code = re.sub(r"\bR(\d+)\b", r"r\1", code)
    s_uc = run_uncompiled(code)
    s_c = run_compiled(code)
    diffs = compare_states(s_uc, s_c)
    assert not diffs, "Semantic differences found:\n" + "\n".join(diffs[:100])
