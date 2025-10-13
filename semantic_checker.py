# semantic_checker.py
# CRZ64I Semantic Checker

from instructions import INSTRUCTIONS


class SemanticChecker:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.symbol_table = {}
        self.current_function = None
        self.reversible_functions = set()
        self.realtime_functions = set()

    def check(self, ast):
        """Main entry point for semantic analysis"""
        self.errors = []
        self.warnings = []
        self.symbol_table = {}
        self.current_function = None
        self.reversible_functions = set()
        self.realtime_functions = set()

        for node in ast:
            self.check_node(node)

        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "valid": len(self.errors) == 0,
        }

    def check_node(self, node):
        """Recursively check AST nodes"""
        node_type = node.get("type")
        if node_type == "function":
            self.check_function(node)
        elif node_type == "declaration":
            self.check_declaration(node)
        elif node_type == "instruction":
            self.check_instruction(node)
        elif node_type == "if":
            self.check_if(node)
        elif node_type == "for":
            self.check_for(node)
        elif node_type == "return":
            self.check_return(node)
        elif node_type == "binary_op":
            self.check_binary_op(node)
        elif node_type == "call":
            self.check_call(node)
        # Add more node types as needed

    def check_function(self, node):
        """Check function declaration"""
        name = node["name"]
        self.current_function = name
        params = node["parameters"]
        body = node["body"]
        attributes = node.get("attributes", [])

        # Check attributes
        self.check_attributes(attributes, node)

        # Add function to symbol table
        self.symbol_table[name] = {
            "type": "function",
            "parameters": {p["name"]: p["type"] for p in params},
            "return_type": None,  # Infer or default
        }

        # Check parameters
        for param in params:
            self.check_parameter(param)

        # Check body statements
        for stmt in body:
            self.check_node(stmt)

        self.current_function = None

    def check_attributes(self, attributes, node):
        """Validate function/block attributes"""
        for attr in attributes:
            attr_name = attr["name"]
            attr_value = attr.get("value")

            if attr_name == "reversible":
                self.reversible_functions.add(self.current_function)
                # Check if function body supports reversibility
                self.check_reversibility(node)
            elif attr_name == "realtime":
                self.realtime_functions.add(self.current_function)
                # Check for deterministic behavior
                self.check_realtime_constraints(node)
            elif attr_name == "power":
                if attr_value not in ["low", "med", "high"]:
                    self.errors.append(
                        f"Invalid power level '{attr_value}' in {self.current_function}"
                    )
            elif attr_name == "fusion":
                # Fusion hint - no semantic check needed
                pass
            elif attr_name == "no_erase":
                # No-erase hint - check for information preservation
                self.check_no_erase(node)
            elif attr_name == "thermal_hint":
                if attr_value is None or not attr_value.isdigit():
                    self.errors.append(
                        f"Thermal hint must be numeric in {self.current_function}"
                    )
            else:
                self.warnings.append(
                    f"Unknown attribute '{attr_name}' in {self.current_function}"
                )

    def check_reversibility(self, node):
        """Check if function is reversible (no information erasure)"""
        body = node["body"]
        for stmt in body:
            if stmt["type"] == "instruction":
                mnemonic = stmt["mnemonic"]
                if mnemonic in ["STORE", "STOREF"] and not self.has_save_delta(stmt):
                    self.errors.append(
                        f"Reversible function {self.current_function} has erasing STORE without SAVE_DELTA"
                    )
            # Check for other erasing operations

    def check_realtime_constraints(self, node):
        """Check realtime constraints (no blocking operations, deterministic)"""
        body = node["body"]
        for stmt in body:
            if stmt["type"] == "instruction":
                mnemonic = stmt["mnemonic"]
                if mnemonic in ["SLEEP", "YIELD", "DMA_START"]:
                    self.errors.append(
                        f"Realtime function {self.current_function} contains blocking operation {mnemonic}"
                    )
            elif stmt["type"] == "call":
                # Check if called function is realtime
                if stmt["name"] not in self.realtime_functions:
                    self.warnings.append(
                        f"Realtime function {self.current_function} calls non-realtime {stmt['name']}"
                    )

    def check_no_erase(self, node):
        """Check no-erase constraints"""
        # Implementation for preventing information erasure
        # This would involve dataflow analysis to ensure writes don't overwrite without backup
        pass

    def has_save_delta(self, instruction_node):
        """Check if instruction is preceded by SAVE_DELTA"""
        # This requires context from the full AST
        # For now, simplistic check
        return any(
            op.get("mnemonic") == "SAVE_DELTA"
            for op in instruction_node.get("preceding", [])
        )

    def check_declaration(self, node):
        """Check variable declaration"""
        name = node["name"]
        type_ = node["var_type"]
        expr = node["expression"]

        # Type checking
        expr_type = self.infer_type(expr)
        if type_ and expr_type != type_:
            self.errors.append(
                f"Type mismatch in declaration of {name}: expected {type_}, got {expr_type}"
            )

        # Add to symbol table (local scope)
        if self.current_function:
            if self.current_function not in self.symbol_table:
                self.symbol_table[self.current_function] = {"locals": {}}
            self.symbol_table[self.current_function]["locals"][name] = (
                type_ or expr_type
            )

    def check_parameter(self, param):
        """Check function parameter"""
        name = param["name"]
        type_ = param["type"]
        if self.current_function:
            if self.current_function not in self.symbol_table:
                self.symbol_table[self.current_function] = {"parameters": {}}
            self.symbol_table[self.current_function]["parameters"][name] = type_

    def check_instruction(self, node):
        """Check instruction semantics"""
        mnemonic = node["mnemonic"]
        operands = node["operands"]

        if mnemonic not in INSTRUCTIONS:
            self.errors.append(
                f"Unknown instruction '{mnemonic}' in {self.current_function}"
            )
            return

        instr_info = INSTRUCTIONS[mnemonic]
        expected_operands = instr_info["operands"]
        format_ = instr_info["format"]

        if len(operands) != expected_operands:
            self.errors.append(
                f"Instruction {mnemonic} expects {expected_operands} operands, got {len(operands)}"
            )

        # Check operand types based on format
        self.check_operands(operands, format_, mnemonic)

        # Special checks for certain instructions
        if mnemonic in ["SAVE_DELTA", "RESTORE_DELTA"]:
            self.check_reversible_instruction(node)
        elif mnemonic in ["SET_PWR_MODE", "SLEEP"]:
            self.check_power_instruction(node)

    def check_operands(self, operands, format_, mnemonic):
        """Validate operand types for instruction format"""
        for i, op in enumerate(operands):
            op_type = op["type"]
            if format_ == "R" and i == 0:  # Destination register
                if op_type != "register":
                    self.errors.append(
                        f"{mnemonic} destination must be register, got {op_type}"
                    )
            elif format_ == "I" and i > 0:  # Immediate
                # Special case for LOAD/STORE: allow memory references
                if mnemonic in ["LOAD", "STORE"] and op_type == "memory":
                    continue
                if op_type not in ["immediate", "label"]:
                    self.errors.append(
                        f"{mnemonic} immediate operand expected, got {op_type}"
                    )
            elif format_ == "V":  # Vector
                if op_type not in ["vector_register", "memory"]:
                    self.errors.append(
                        f"{mnemonic} vector operand expected, got {op_type}"
                    )
            # Add more format checks

    def check_reversible_instruction(self, node):
        """Special checks for reversible instructions"""
        if (
            self.current_function
            and self.current_function not in self.reversible_functions
        ):
            self.warnings.append(
                f"Reversible instruction {node['mnemonic']} in non-reversible function {self.current_function}"
            )

    def check_power_instruction(self, node):
        """Check power management instructions"""
        # Ensure proper mode values, etc.
        pass

    def check_if(self, node):
        """Check if statement"""
        condition = node["condition"]
        cond_type = self.infer_type(condition)
        if cond_type != "i32":  # Assuming boolean as i32 != 0
            self.warnings.append(
                f"If condition should be integer type, got {cond_type}"
            )

        for stmt in node["then"]:
            self.check_node(stmt)
        if node["else"]:
            for stmt in node["else"]:
                self.check_node(stmt)

    def check_for(self, node):
        """Check for loop"""
        start = node["start"]
        end = node["end"]
        start_type = self.infer_type(start)
        end_type = self.infer_type(end)
        if start_type != end_type or start_type not in ["i32", "i64"]:
            self.errors.append("For loop bounds must be integer types of same size")

        # Add loop variable to local scope
        var = node["variable"]
        if self.current_function:
            self.symbol_table[self.current_function]["locals"][var] = "i32"  # Default

        for stmt in node["body"]:
            self.check_node(stmt)

    def check_return(self, node):
        """Check return statement"""
        if node["expression"]:
            expr_type = self.infer_type(node["expression"])
            # Check against function return type
            if (
                self.current_function
                and self.symbol_table.get(self.current_function, {}).get("return_type")
                != expr_type
            ):
                self.warnings.append(
                    f"Return type mismatch in {self.current_function}: expected {self.symbol_table[self.current_function]['return_type']}, got {expr_type}"
                )

    def check_binary_op(self, node):
        """Check binary operation type compatibility"""
        left_type = self.infer_type(node["left"])
        right_type = self.infer_type(node["right"])
        op = node["operator"]

        if left_type != right_type:
            self.warnings.append(
                f"Binary operation {op} operands have different types: {left_type} and {right_type}"
            )

        # Specific op checks
        if op in ["+", "-", "*", "/", "%"] and left_type not in [
            "i32",
            "i64",
            "f32",
            "f64",
        ]:
            self.errors.append(f"Arithmetic operation {op} requires numeric types")

    def check_call(self, node):
        """Check function call"""
        name = node["name"]
        if name not in self.symbol_table:
            self.errors.append(f"Undefined function call to {name}")
            return

        func_info = self.symbol_table[name]
        args = node["arguments"]
        param_types = list(func_info["parameters"].values())

        if len(args) != len(param_types):
            self.errors.append(
                f"Function {name} expects {len(param_types)} arguments, got {len(args)}"
            )

        for i, arg in enumerate(args):
            if i < len(param_types):
                arg_type = self.infer_type(arg)
                if arg_type != param_types[i]:
                    self.warnings.append(
                        f"Argument {i+1} type mismatch for {name}: expected {param_types[i]}, got {arg_type}"
                    )

    def infer_type(self, node):
        """Simple type inference for expressions"""
        node_type = node.get("type")
        if node_type == "literal":
            if "." in node["value"]:
                return "f64"
            else:
                return "i32"
        elif node_type == "identifier":
            # Look up in symbol table
            if self.current_function:
                local = (
                    self.symbol_table.get(self.current_function, {})
                    .get("locals", {})
                    .get(node["value"])
                )
                if local:
                    return local
                param = (
                    self.symbol_table.get(self.current_function, {})
                    .get("parameters", {})
                    .get(node["value"])
                )
                if param:
                    return param
            return "i32"  # Default
        elif node_type == "binary_op":
            return self.infer_type(node["left"])  # Assume left type
        elif node_type in ["register", "vector_register"]:
            return "i64" if node_type == "register" else "vec<4,i32>"
        elif node_type == "memory":
            return "i64"  # Default memory access
        else:
            return "void"

    def report(self):
        """Generate report of checks"""
        report = {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "reversible_functions": list(self.reversible_functions),
            "realtime_functions": list(self.realtime_functions),
        }
        return report


# Example usage
if __name__ == "__main__":
    from grammar import CRZParser

    parser = CRZParser()
    # Example code
    sample_code = """
    #[reversible]
    fn add(a: i32, b: i32) -> i32 {
        let result = a + b;
        return result;
    }
    
    #[realtime]
    fn fast_loop(n: i32) {
        for i in 0..n {
            ADD R1, R2, R3;
        }
    }
    """

    ast = parser.parse(sample_code)
    checker = SemanticChecker()
    result = checker.check(ast)
    print("Semantic Check Result:", result)
