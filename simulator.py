# simulator.py
# Minimal CRZSimulator PoC: executes compiler AST sequentially.
# Keeps simple models: cycles/op, energy per cycle, temperature delta.
import math, time

class CRZSimulator:
    def __init__(self):
        # regs simple integer regs R0..R31 and vector regs not implemented
        self.regs = {i:0 for i in range(32)}
        self.pc = 0
        self.cycles = 0
        self.energy = 0.0
        self.temp = 20.0  # ambient base
        # per-op costs (cycles, energy per cycle Joules)
        self.costs = {
            'ADD':(1,0.3),'SUB':(1,0.3),'MUL':(3,0.6),'DIV':(6,1.2),
            'LOAD':(3,0.4),'STORE':(3,0.4),'FMA':(4,0.8),'VDOT32':(4,0.9),

    def _step_cost(self, opname, fused=False):
        if opname in self.costs:
            c,e = self.costs[opname]
        else:
            c,e = (1,0.2)
        # fused reduce cycles a bit
        if fused:
            c = max(1, int(math.ceil(c*0.6)))
            e *= 0.9
        return c,e

    def _apply_cost(self, opname, fused=False):
        c,e = self._step_cost(opname,fused)
        self.cycles += c
        self.energy += c*e
        # simple thermal model: temp increases proportional to energy added, relaxes slowly
        self.temp += (c*e)*0.1
        # passive cooling toward ambient 20 with small factor
        self.temp -= (self.temp-20.0)*0.01

    def _parse_reg(self, tok):
        tok = tok.strip()
        m = None
        # R<number>
        if tok.upper().startswith('R'):
            try:
                idx = int(tok[1:])
                return idx
            except:
                return None
        # immediate integer
        try:
            return int(tok)
        except:
            return None

    def run(self, ast):
        # execute linear AST
        self.pc = 0
        instrs = ast
        while self.pc < len(instrs):
            ins = instrs[self.pc]
            op = ins['op']
            fused = ins.get('fused', False)
            # emulate small set
            if op=='ADD':
                dst = self._parse_reg(ins['args'][0])
                a = self._parse_reg(ins['args'][1])
                b = self._parse_reg(ins['args'][2])
                aval = self.regs.get(a,0) if isinstance(a,int) and a in self.regs else (a if isinstance(a,int) else 0)
                bval = self.regs.get(b,0) if isinstance(b,int) and b in self.regs else (b if isinstance(b,int) else 0)
                self.regs[dst] = aval + bval
                self._apply_cost('ADD', fused)
                self.pc += 1
                continue
            if op=='LOAD':
                # LOAD dst, [addr]  or LOAD dst, imm
                dst = self._parse_reg(ins['args'][0])
                src = ins['args'][1] if len(ins['args'])>1 else None
                # if src numeric immediate, load immediate
                val = 0
                try:
                    if isinstance(src,str) and src.startswith('['):
                        # memory not implemented: use hash of addr
                        addr = src.strip()
                        val = hash(addr) & 0xffff
                    else:
                        val = int(src)
                except:
                    val = 0
                self.regs[dst] = val
                self._apply_cost('LOAD', fused)
                self.pc += 1
                continue
            if op=='STORE':
                # noop except cost
                self._apply_cost('STORE', fused)
                self.pc += 1
                continue
            if op=='BR_IF':
                # BR_IF 'cond_op reg1', reg2, label
                cond_str, reg2_str, label = ins['args']
                cond_op, reg1_str = cond_str.split()
                reg1 = self._parse_reg(reg1_str)
                reg2 = self._parse_reg(reg2_str)
                val1 = self.regs.get(reg1,0)
                val2 = self.regs.get(reg2,0)
                cond = False
                if cond_op == 'LT':
                    cond = val1 < val2
                elif cond_op == 'LE':
                    cond = val1 <= val2
                elif cond_op == 'GT':
                    cond = val1 > val2
                elif cond_op == 'GE':
                    cond = val1 >= val2
                elif cond_op == 'EQ':
                    cond = val1 == val2
                elif cond_op == 'NE':
                    cond = val1 != val2
                if cond:
                    # jump to label
                    for idx, i in enumerate(instrs):
                        if i.get('op')=='LABEL' and i.get('name')==label:
                            self.pc = idx
                            break
                else:
                    self.pc += 1
                self._apply_cost('BR_IF', fused)
                continue
            if op=='FUSED_LOAD_ADD':
                # handled as sequence in compiler; if appears here just charge fused cost
                self._apply_cost('FUSED_LOAD_ADD', fused=True)
                self.pc += 1
                continue
            if op=='HALT':
                self._apply_cost('HALT', fused)
                break
            if op=='LABEL':
                self.pc += 1
                continue
            if op=='FUNC' or op=='END_FUNC':
                self.pc += 1
                continue
            # fallback: charge default
            self._apply_cost(op, fused)
            self.pc += 1
        # return summary metrics
        return self.cycles, round(self.energy,6), round(self.temp,6)

if __name__=='__main__':
    # quick smoke test
    from compiler import CRZCompiler
    c = CRZCompiler()
    ast = c.compile("ADD R0, R1, 5; HALT;")['ast']
    sim = CRZSimulator()
    sim.regs[1]=10
    cycles,energy,temp = sim.run(ast)
    print("Result R0:", sim.regs[0], "cycles", cycles, "energy", energy, "temp", temp)
