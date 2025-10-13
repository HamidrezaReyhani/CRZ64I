#!/usr/bin/env python3
import sys
sys.path.insert(0,'src')
from crz.compiler.parser import parse_text
from crz.compiler.codegen_sim import codegen
from crz.compiler.passes import run_passes
from crz.simulator.simulator import Simulator
from instructions import INSTRUCTIONS

def run_prog(crz_code, apply_fusion=False):
    prog = parse_text(crz_code)
    ops = codegen(prog, apply_fusion=apply_fusion)
    sim = Simulator()
    sim.run(ops)
    return sim.get_state()

# Templates for minimal CRZ programs per opcode
OP_TEMPLATES = {
    'ADD': "start:\n  LOAD r1,[0]\n  ADD r2,r1,1\n  STORE r2,[1]\n  HALT\n",
    'SUB': "start:\n  LOAD r1,[0]\n  SUB r2,r1,1\n  STORE r2,[1]\n  HALT\n",
    'MUL': "start:\n  LOAD r1,[0]\n  MUL r2,r1,2\n  STORE r2,[1]\n  HALT\n",
    'DIV': "start:\n  LOAD r1,[0]\n  DIV r2,r1,2\n  STORE r2,[1]\n  HALT\n",
    'AND': "start:\n  LOAD r1,[0]\n  AND r2,r1,1\n  STORE r2,[1]\n  HALT\n",
    'OR': "start:\n  LOAD r1,[0]\n  OR r2,r1,1\n  STORE r2,[1]\n  HALT\n",
    'XOR': "start:\n  LOAD r1,[0]\n  XOR r2,r1,1\n  STORE r2,[1]\n  HALT\n",
    'SHL': "start:\n  LOAD r1,[0]\n  SHL r2,r1,1\n  STORE r2,[1]\n  HALT\n",
    'SHR': "start:\n  LOAD r1,[0]\n  SHR r2,r1,1\n  STORE r2,[1]\n  HALT\n",
    'POPCNT': "start:\n  LOAD r1,[0]\n  POPCNT r2,r1\n  STORE r2,[1]\n  HALT\n",
    'LOAD': "start:\n  LOAD r1,[0]\n  STORE r1,[1]\n  HALT\n",
    'STORE': "start:\n  LOAD r1,[0]\n  STORE r1,[1]\n  HALT\n",
    'BR_IF': "start:\n  LOAD r1,[0]\n  BR_IF GT,r1,0,end\n  STORE r1,[1]\n  end:\n  HALT\n",
    'JMP': "start:\n  JMP end\n  STORE r1,[1]\n  end:\n  HALT\n",
    'NOP': "start:\n  NOP\n  HALT\n",
    'HALT': "start:\n  HALT\n",
    # Add more as needed, for now focus on key ones
}

def compare_states(s1, s2):
    diffs = []
    for r in sorted(set(list(s1['regs'].keys()) + list(s2['regs'].keys()))):
        a = s1['regs'].get(r, 0)
        b = s2['regs'].get(r, 0)
        if isinstance(a, float) or isinstance(b, float):
            if abs(a - b) > 1e-9:
                diffs.append(f"R{r}: {a} != {b}")
        else:
            if a != b:
                diffs.append(f"R{r}: {a} != {b}")
    for addr in sorted(set(list(s1['memory'].keys()) + list(s2['memory'].keys()))):
        a = s1['memory'].get(addr, 0)
        b = s2['memory'].get(addr, 0)
        if a != b:
            diffs.append(f"MEM[{addr}]: {a} != {b}")
    return diffs

if __name__ == '__main__':
    ops_to_test = list(OP_TEMPLATES.keys())
    failures = []
    for op in ops_to_test:
        code = OP_TEMPLATES.get(op, "start:\n  HALT\n")
        try:
            s_uc = run_prog(code, apply_fusion=False)
            s_c = run_prog(code, apply_fusion=True)
            diffs = compare_states(s_uc, s_c)
            if diffs:
                print(f"MISMATCH {op}: {diffs}")
                failures.append(op)
        except Exception as e:
            print(f"ERROR {op}: {e}")
            failures.append(op)
    print("Failures:", failures)
    if not failures:
        print("All semantic tests passed!")
