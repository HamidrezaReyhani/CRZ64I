#!/usr/bin/env python3
"""
Quick CRZ64I Testing Examples
"""

from compiler import CRZCompiler

def test_simple():
    """Test simple compilation"""
    compiler = CRZCompiler()

    code = """
    fn main() {
        ADD R0, R1, R2;
    }
    """

    try:
        result = compiler.compile(code)
        print("✅ Simple test PASSED")
        return True
    except Exception as e:
        print(f"❌ Simple test FAILED: {e}")
        return False

def test_attributes():
    """Test attribute handling"""
    compiler = CRZCompiler()

    code = """
    #[fusion]
    #[realtime]
    fn optimized_func(a: i32, b: i32) -> i32 {
        ADD R0, R1, R2;
        return R0;
    }
    """

    try:
        result = compiler.compile(code)
        print("✅ Attributes test PASSED")
        return True
    except Exception as e:
        print(f"❌ Attributes test FAILED: {e}")
        return False

def test_multiple_functions():
    """Test multiple functions"""
    compiler = CRZCompiler()

    code = """
    #[fusion]
    fn func1() {
        LOAD R0, [R1];
    }

    #[realtime]
    fn func2(x: i32) -> i32 {
        ADD R0, R1, R2;
        return R0;
    }
    """

    try:
        result = compiler.compile(code)
        print("✅ Multiple functions test PASSED")
        return True
    except Exception as e:
        print(f"❌ Multiple functions test FAILED: {e}")
        return False

def main():
    print("🚀 CRZ64I Quick Tests")
    print("=" * 30)

    tests = [
        test_simple,
        test_attributes,
        test_multiple_functions
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! CRZ64I is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()
