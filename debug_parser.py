from src.crz.compiler.parser import parse

code = """#[fusion]
#[realtime]
fn attributed_func(x: i32) -> i32 {
    ADD R0, R1, R2;
    return R0;
}"""

try:
    ast = parse(code)
    print("Parsed successfully")
    print(ast.to_json())
except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
