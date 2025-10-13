#!/usr/bin/env python3
"""
CRZ64I Testing Suite
Comprehensive testing for the CRZ64I compiler toolchain
"""

import sys
import os
from compiler import CRZCompiler
from grammar import CRZParser
from semantic_checker import SemanticChecker
from fusion_pass import FusionPass
from reversible_pass import ReversiblePass
from harness import BenchmarkHarness

def test_basic_parsing():
    """Test basic parsing functionality"""
    print("=== Testing Basic Parsing ===")

    parser = CRZParser()

    # Test 1: Simple instruction
    code1 = "ADD R0, R1, R2;"
    ast1 = parser.parse(code1)
    print(f"✓ Simple instruction: {len(ast1)} nodes parsed")

    # Test 2: Function with attributes
    code2 = """
    #[fusion]
    fn test_func() {
        ADD R0, R1, R2;
    }
    """
    ast2 = parser.parse(code2)
    print(f"✓ Function with attributes: {len(ast2)} nodes parsed")

    # Test 3: Multiple functions
    code3 = """
    #[realtime]
    fn func1() {
        LOAD R0, [R1];
    }

    #[fusion]
    fn func2() {
        ADD R0, R1, R2;
        STORE R0, [R3];
    }
    """
    ast3 = parser.parse(code3)
    print(f"✓ Multiple functions: {len(ast3)} functions parsed")

def test_semantic_analysis():
    """Test semantic analysis"""
    print("\n=== Testing Semantic Analysis ===")

    parser = CRZParser()
    checker = SemanticChecker()

    # Test valid code
    valid_code = """
    #[fusion]
    #[realtime]
    fn valid_func(a: i32, b: ptr) -> i32 {
        ADD R0, R1, R2;
        return R0;
    }
    """
    ast = parser.parse(valid_code)
    result = checker.check(ast)
    print(f"✓ Valid code: {'PASS' if result['valid'] else 'FAIL'}")

    # Test invalid attributes
    invalid_code = """
    #[invalid_attr]
    fn test() {
        INVALID_INSTR R0, R1;
    }
    """
    ast = parser.parse(invalid_code)
    result = checker.check(ast)
    print(f"✓ Invalid attributes detected: {'PASS' if not result['valid'] else 'FAIL'}")

def test_optimization_passes():
    """Test optimization passes"""
    print("\n=== Testing Optimization Passes ===")

    parser = CRZParser()
    fusion_pass = FusionPass()
    reversible_pass = ReversiblePass()

    # Test fusion pass
    fusion_code = """
    fn test_fusion() {
        LOAD R1, [R0];
        ADD R2, R1, R3;
        STORE R2, [R4];
    }
    """
    ast = parser.parse(fusion_code)
    fused_ast = fusion_pass.apply(ast)
    print("✓ Fusion pass applied")

    # Test reversible pass
    reversible_code = """
    #[reversible]
    fn test_reversible() {
        ADD R0, R1, R2;
        STORE R0, [R3];
    }
    """
    ast = parser.parse(reversible_code)
    reversible_ast = reversible_pass.apply(ast)
    print("✓ Reversible pass applied")

def test_full_compilation():
    """Test full compilation pipeline"""
    print("\n=== Testing Full Compilation ===")

    compiler = CRZCompiler()

    test_cases = [
        ("Simple function", """
        fn simple() {
            ADD R0, R1, R2;
        }
        """),

        ("Function with attributes", """
        #[fusion]
        #[realtime]
        fn attributed_func(x: i32) -> i32 {
            ADD R0, R1, R2;
            return R0;
        }
        """),

        ("Multiple functions", """
        #[fusion]
        fn func1() {
            LOAD R0, [R1];
        }

        #[realtime]
        fn func2(a: i32, b: i32) -> i32 {
            ADD R0, R1, R2;
            return R0;
        }
        """)
    ]

    for name, code in test_cases:
        try:
            result = compiler.compile(code)
            print(f"✓ {name}: Compilation successful")
        except Exception as e:
            print(f"✗ {name}: Compilation failed - {e}")

def test_benchmarking():
    """Test benchmarking capabilities"""
    print("\n=== Testing Benchmarking ===")

    harness = BenchmarkHarness()

    # Test RAPL availability
    rapl_available = harness.rapl_available
    print(f"✓ RAPL energy measurement: {'Available' if rapl_available else 'Not available (requires root)'}")

    # Test basic benchmarking (may be slow)
    try:
        print("Running microbenchmarks for ADD instruction...")
        result = harness.run_microbenchmark('ADD', iterations=1000)
        print(f"✓ Benchmark completed: {result['iterations']} iterations")
    except Exception as e:
        print(f"✗ Benchmark failed: {e}")

def test_examples():
    """Test example files"""
    print("\n=== Testing Example Files ===")

    example_dir = "examples"
    if os.path.exists(example_dir):
        for file in os.listdir(example_dir):
            if file.endswith('.crz'):
                filepath = os.path.join(example_dir, file)
                try:
                    with open(filepath, 'r') as f:
                        code = f.read()

                    compiler = CRZCompiler()
                    result = compiler.compile(code)
                    print(f"✓ {file}: Compiled successfully")
                except Exception as e:
                    print(f"✗ {file}: Compilation failed - {e}")
    else:
        print("! No examples directory found")

def interactive_test():
    """Interactive testing mode"""
    print("\n=== Interactive Testing ===")
    print("Enter CRZ64I code to test (press Ctrl+D to finish):")

    compiler = CRZCompiler()
    code_lines = []

    try:
        while True:
            line = input()
            code_lines.append(line)
    except EOFError:
        pass

    code = '\n'.join(code_lines)

    if code.strip():
        try:
            result = compiler.compile(code)
            print("✓ Compilation successful!")
            print(f"Generated {len(result['machine_code'])} machine code lines")
        except Exception as e:
            print(f"✗ Compilation failed: {e}")
    else:
        print("No code entered")

def main():
    """Main testing function"""
    print("CRZ64I Compiler Testing Suite")
    print("=" * 40)

    # Run all tests
    test_basic_parsing()
    test_semantic_analysis()
    test_optimization_passes()
    test_full_compilation()
    test_benchmarking()
    test_examples()

    # Interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_test()

    print("\n" + "=" * 40)
    print("Testing complete!")
    print("\nTo run interactive testing:")
    print("  python3 test_crz64i.py --interactive")
    print("\nTo test a specific file:")
    print("  python3 -c \"from compiler import CRZCompiler; c = CRZCompiler(); result = c.compile(open('file.crz').read())\"")

if __name__ == "__main__":
    main()
