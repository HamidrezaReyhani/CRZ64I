# grammar.py
# CRZ64I Grammar and Parser

import re
from instructions import INSTRUCTIONS

class CRZParser:
    def __init__(self):
        self.labels = {}
        self.instructions = []

    def parse_line(self, line):
        line = line.strip()
        if not line or line.startswith('#'):
            return None
        if ':' in line:
            label, rest = line.split(':', 1)
            self.labels[label.strip()] = len(self.instructions)
            line = rest.strip()
        if not line:
            return None
        # Simple parse: mnemonic operands;
        parts = re.split(r'[,\s]+', line.rstrip(';'))
        mnemonic = parts[0].upper()
        operands = parts[1:]
        if mnemonic in INSTRUCTIONS:
            return {'mnemonic': mnemonic, 'operands': operands}
        return None

    def parse(self, code):
        self.instructions = []
        self.labels = {}
        for line in code.split('\n'):
            instr = self.parse_line(line)
            if instr:
                self.instructions.append(instr)
        return self.instructions, self.labels
