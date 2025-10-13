# compiler.py
# Minimal CRZCompiler PoC: parse tiny assembly-ish CRZ64I, basic semantic checks,
# simple optimization passes: fusion (merge LOAD+ADD -> fused pseudo-op) and reversible emulation.
# Returns a dict with 'ast' (list of instructions) and metadata.
import re, copy

class CRZCompiler:
    def __init__(self):
        self.op_latency = {
            'ADD':1,'SUB':1,'MUL':3,'DIV':6,'LOAD':3,'STORE':3,'FMA':4,'VDOT32':4,
            'BR':1,'BR_IF':2,'CALL':4,'RET':4,'NOP':1,'HALT':1
        }

    def parse(self, code):
        lines = []
        attributes = []
        for L in code.splitlines():
            s = L.strip()
            if not s or s.startswith('//'): continue
            if s.startswith('#[') and s.endswith(']'):
                attr = s[2:-1]
                attributes.append(attr)
                continue
            # remove trailing ';'
            if s.endswith(';'): s = s[:-1].strip()
            lines.append(s)
        # naive parse: split tokens
        instrs = []
        for l in lines:
            m = re.match(r'fn\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)\s*\{?', l)
            if m:
                instrs.append({'op':'FUNC','name':m.group(1),'args': [a.strip() for a in m.group(2).split(',') if a.strip()], 'attributes': attributes})
                attributes = []  # reset for next
                continue
            if l=='}': instrs.append({'op':'END_FUNC'}); continue
            # label?
            if re.match(r'^[A-Za-z_][A-Za-z0-9_]*:$', l):
                instrs.append({'op':'LABEL','label':l[:-1]}); continue
            parts = l.split(None,1)
            op = parts[0].upper()
            args = []
            if len(parts)>1:
                args = [a.strip() for a in parts[1].split(',')]
            instrs.append({'op':op,'args':args,'raw':l})
        return instrs

    def semantic(self, ast):
        # trivial checks: known ops
        known = set(list(self.op_latency.keys()) + ['FUNC','END_FUNC','LABEL'])
        warns = []
        for i,instr in enumerate(ast):
            if instr['op'] not in known:
                warns.append(f"Unknown op '{instr['op']}' at idx {i}")
        return warns

    def fusion_pass(self, ast):
        # simple fusion: LOAD rX, [addr]; ADD rY, rX, K  -> FUSED_LOAD_ADD rY, [addr], K
        out = []
        i=0
        while i < len(ast):
            ins = ast[i]
            if ins['op']=='LOAD' and i+1 < len(ast):
                n = ast[i+1]
                if n['op']=='ADD':
                    # check pattern ADD dst, src, imm  where src equals LOAD dest
                    load_dst = ins['args'][0]
                    add_dst = n['args'][0]
                    add_a = n['args'][1]
                    add_b = n['args'][2] if len(n['args'])>2 else None
                    if add_a==load_dst:
                        fused = {'op':'FUSED_LOAD_ADD','args':[add_dst, ins['args'][1], add_b], 'raw': f"FUSED_LOAD_ADD {add_dst}, {ins['args'][1]}, {add_b}"}
                        out.append(fused)
                        i += 2
                        continue
            out.append(ins)
            i += 1
        return out

    def reversible_pass(self, ast):
        # conservative: insert SAVE_DELTA before any STORE in a reversible function block if not present.
        out=[]
        in_func=False
        reversible=False
        for instr in ast:
            if instr['op']=='FUNC':
                in_func=True
                reversible = 'reversible' in instr.get('attributes', [])
                out.append(instr); continue
            if instr['op']=='END_FUNC':
                in_func=False
                reversible=False
                out.append(instr); continue
            # if STORE and in reversible -> insert SAVE_DELTA
            if in_func and reversible and instr['op']=='STORE':
                # naive: insert SAVE_DELTA tmp, target
                tgt = instr['args'][1] if len(instr['args'])>1 else instr['args'][0]
                out.append({'op':'SAVE_DELTA','args':['__sav', tgt], 'raw':f"SAVE_DELTA __sav, {tgt}"})
            out.append(instr)
        return out

    def codegen(self, ast):
        # lower to a linear instruction list (no binary encoding). Expand FUSED into micro-sequence.
        flat=[]
        for ins in ast:
            op=ins['op']
            if op=='FUSED_LOAD_ADD':
                # lower to LOAD; ADD but keep marked fused for latency saving
                flat.append({'op':'LOAD','args':[ins['args'][0], ins['args'][1], '/*fused_dst*/'], 'fused':True})
                flat.append({'op':'ADD','args':[ins['args'][0], ins['args'][0], ins['args'][2]], 'fused':True})
                continue
            flat.append(ins)
        return flat

    def compile(self, code):
        ast = self.parse(code)
        warns = self.semantic(ast)
        # optimization passes
        ast2 = self.fusion_pass(ast)
        ast3 = self.reversible_pass(ast2)
        final = self.codegen(ast3)
        return {'ast': final, 'warnings': warns, 'passes': ['fusion','reversible_emulation']}

if __name__=='__main__':
    import sys
    c = CRZCompiler()
    code = sys.stdin.read() if not sys.stdin.isatty() else "ADD R0, R1, 5; HALT;"
    res = c.compile(code)
    print("Compiled", len(res['ast']), "instrs")
