#!/usr/bin/env python3
import subprocess, json, time, sys
sys.path.insert(0,'src')
from crz.compiler.parser import parse_text
from crz.compiler.codegen_sim import codegen
from crz.simulator.simulator import Simulator

code = open('examples/micro_add.crz').read()
code = '\n'.join(line for line in code.split('\n') if not line.strip().startswith('#'))
code = code.replace('#N=100000', '')  # remove the comment line
N = '10000'
code = code.replace('N', N)  # replace N with 10000 for faster simulation
program = parse_text(code)
ops = codegen(program)
sim = Simulator()
res = sim.run(ops)  # returns cycles, energy, temp
sim_cycles = res[0]
print("sim cycles:", sim_cycles)
# run native micro_add equivalent and measure time
t0=time.time()
subprocess.run(['./bench/micro_add', N], check=True)
t1=time.time()
print("native wall time:", t1-t0)
print("sim_clock_hz:", sim_cycles / (t1-t0))
