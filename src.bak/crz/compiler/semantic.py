"""
CRZ64I Semantic Analyzer

Performs semantic checks on the CRZ64I AST, including attribute placement validation,
realtime constraints, and reversible dataflow checks.
"""

from typing import List, Dict, Any, Set
from rich.console import Console
from .ast import Program, Function, Instr, If, Loop, Statement, Attribute, LocalDecl


class SemanticAnalyzer:
    """Analyzes the AST for semantic errors and warnings."""

    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.console = Console()

    def analyze(self, program: Program) -> List[Dict[str, Any]]:
        """Analyze the program and return list of issues."""
        self.errors = []
        self.warnings = []
        self.visit_program(program)
        return self.errors + self.warnings

    def log_issue(self, message: str, meta: Any, level: str = 'error'):
        """Log an issue with location."""
        line = meta.line if meta else 0
        column = meta.column if meta else 0
        if level == 'error':
            self.console.print(f"[red]Error at {line}:{column}: {message}[/red]")
            self.errors.append(
                {"type": "error", "message": message, "line": line, "column": column}
            )
        else:
            self.console.print(f"[yellow]Warning at {line}:{column}: {message}[/yellow]")
            self.warnings.append(
                {"type": "warning", "message": message, "line": line, "column": column}
            )

    def visit_program(self, program: Program):
        """Visit program."""
        for decl in program.declarations:
            if isinstance(decl, Function):
                self.visit_function(decl)

    def visit_function(self, func: Function):
        """Visit function."""
        # Check attribute placement
        self.check_attrs(func.attrs, "function", func.meta)
        # Check realtime and reversible
        in_realtime = any(attr.name == "realtime" for attr in func.attrs)
        in_reversible = any(attr.name == "reversible" for attr in func.attrs)
        self.visit_block(func.body, in_realtime, in_reversible, set(), func.name)

    def visit_block(
        self, block: List[Statement], in_realtime: bool, in_reversible: bool, saved_targets: Set[str], func_name: str
    ):
        """Visit a block of statements."""
        for stmt in block:
            if isinstance(stmt, Instr):
                self.check_attrs(stmt.attrs, "instruction", stmt.meta)
                if in_realtime:
                    self.check_realtime_instr(stmt)
                if in_reversible:
                    self.check_reversible_write(stmt, saved_targets, func_name)
            elif isinstance(stmt, If):
                self.check_attrs(stmt.attrs, "if", stmt.meta)
                realtime = in_realtime or any(
                    attr.name == "realtime" for attr in stmt.attrs
                )
                reversible = in_reversible or any(
                    attr.name == "reversible" for attr in stmt.attrs
                )
                self.visit_block(stmt.then_block, realtime, reversible, saved_targets, func_name)
                if stmt.else_block:
                    self.visit_block(stmt.else_block, realtime, reversible, saved_targets, func_name)
            elif isinstance(stmt, Loop):
                self.check_attrs(stmt.attrs, "loop", stmt.meta)
                realtime = in_realtime or any(
                    attr.name == "realtime" for attr in stmt.attrs
                )
                reversible = in_reversible or any(
                    attr.name == "reversible" for attr in stmt.attrs
                )
                self.visit_block(stmt.body, realtime, reversible, saved_targets, func_name)
            elif isinstance(stmt, LocalDecl):
                if in_reversible:
                    saved_targets.add(stmt.name)
                    # Also save the assigned variable if it's a register
                    if stmt.expr in [f"R{i}" for i in range(32)]:
                        saved_targets.add(stmt.expr)

    def check_attrs(self, attrs: List[Attribute], context: str, meta: Any):
        """Check if attributes are allowed in context."""
        allowed = {
            "function": ["fusion", "reversible", "realtime", "power", "thermal_hint"],
            "instruction": ["fusion", "no_erase"],
            "if": ["reversible", "realtime"],
            "loop": ["reversible", "realtime"],
        }.get(context, [])
        for attr in attrs:
            if attr.name not in allowed:
                self.log_issue(
                    f"Attribute #[{attr.name}] not allowed on {context}", meta
                )

    def check_realtime_instr(self, instr: Instr):
        """Check realtime constraints on instruction."""
        # Dynamic allocation ops
        dynamic_ops = ["LOAD", "STORE", "VLOAD", "VSTORE"]
        if instr.mnemonic in dynamic_ops:
            self.log_issue(
                f"Realtime violation: {instr.mnemonic} inside realtime function.",
                instr.meta,
            )
        # DMA_START
        if instr.mnemonic == "DMA_START":
            self.log_issue(
                "Realtime violation: DMA_START inside realtime function.",
                instr.meta,
            )

    def check_reversible_write(self, instr: Instr, saved_targets: Set[str], func_name: str):
        """Check reversible write."""
        write_ops = [
            "ADD",
            "SUB",
            "MUL",
            "DIV",
            "AND",
            "OR",
            "XOR",
            "SHL",
            "SHR",
            "POPCNT",
            "LOAD",
            "STORE",
            "ATOMIC_INC",
            "VADD",
            "VSUB",
            "VMUL",
            "VDOT32",
            "VSHL",
            "VSHR",
            "VFMA",
            "VREDUCE_SUM",
            "FADD",
            "FSUB",
            "FMUL",
            "FMA",
            "REV_ADD",
            "REV_SWAP",
            "CRC32",
            "HASH_INIT",
            "HASH_UPDATE",
            "HASH_FINAL",
            "PROFILE_START",
            "PROFILE_STOP",
        ]
        if instr.mnemonic in write_ops and instr.operands:
            target = instr.operands[0]
            has_no_erase = any(attr.name == "no_erase" for attr in instr.attrs)
            if target not in saved_targets and not has_no_erase:
                self.log_issue(
                    f"Write to {target} in function {func_name} without prior let tmp = {target} or #[no_erase]",
                    instr.meta,
                )
