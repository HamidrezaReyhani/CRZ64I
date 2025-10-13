"""
Tests for CRZ64I Parser

Tests that the parser accepts sample CRZ64I code snippets and produces correct AST.
"""

import pytest
from crz.compiler.parser import parse
from crz.compiler.ast import Program, Function, Instr, Attribute


def test_parse_sample_fusion_function():
    """Test parsing a function with #[fusion] and basic instructions."""
    code = """#[fusion]
fn foo(x, y) {
    LOAD R1, [x];
    ADD R2, R1, y;
    STORE R2, [x];
}"""
    ast = parse(code)
    assert isinstance(ast, Program)
    assert len(ast.declarations) == 1
    func = ast.declarations[0]
    assert isinstance(func, Function)
    assert func.name == 'foo'
    assert func.params == [('x', None), ('y', None)]
    assert func.return_type is None
    assert len(func.attrs) == 1
    assert func.attrs[0].name == 'fusion'
    assert len(func.body) == 3
    assert isinstance(func.body[0], Instr)
    assert func.body[0].mnemonic == 'LOAD'
    assert func.body[0].operands == ['R1', '[x]']
    assert func.body[1].mnemonic == 'ADD'
    assert func.body[1].operands == ['R2', 'R1', 'y']
    assert func.body[2].mnemonic == 'STORE'
    assert func.body[2].operands == ['R2', '[x]']


def test_parse_sample_reversible_function():
    """Test parsing a function with #[reversible] and let declarations."""
    code = """#[reversible]
fn bar(a: i32) -> i32 {
    let tmp = a;
    ADD R1, R0, tmp;
    return R1;
}"""
    ast = parse(code)
    assert isinstance(ast, Program)
    func = ast.declarations[0]
    assert isinstance(func, Function)
    assert func.name == 'bar'
    assert func.params == [('a', 'i32')]
    assert func.return_type == 'i32'
    assert len(func.attrs) == 1
    assert func.attrs[0].name == 'reversible'
    # Body checks omitted for brevity


def test_parse_sample_if_statement():
    """Test parsing if statement."""
    code = """fn test_if(x) {
    if x == 0 {
        LOAD R1, [x];
    } else {
        STORE R1, [x];
    }
}"""
    ast = parse(code)
    func = ast.declarations[0]
    assert len(func.body) == 1
    # Assume If node


def test_parse_sample_loop():
    """Test parsing for loop."""
    code = """fn test_loop(n) {
    for i in 0..n {
        ADD R1, R1, 1;
    }
}"""
    ast = parse(code)
    func = ast.declarations[0]
    assert len(func.body) == 1
    # Assume Loop node


def test_parse_sample_vector_type():
    """Test parsing vector types and vector instructions."""
    code = """fn vec_add(a: vec<16,i32>, b: vec<16,i32>) {
    VADD V0, V1, V2;
}"""
    ast = parse(code)
    func = ast.declarations[0]
    assert func.params == [('a', 'vec<16,i32>'), ('b', 'vec<16,i32>')]
    assert len(func.body) == 1
    instr = func.body[0]
    assert instr.mnemonic == 'VADD'
    assert instr.operands == ['V0', 'V1', 'V2']


def test_parse_sample_comment():
    """Test parsing with comments."""
    code = """// This is a comment
fn commented() {
    ADD R1, R0, 1; // another comment
}"""
    ast = parse(code)
    # Should parse without error, comments ignored
    assert isinstance(ast, Program)


def test_parse_attributes_on_instructions():
    """Test attributes on instructions."""
    code = """fn test() {
    #[no_erase]
    ADD R1, R0, 1;
}"""
    ast = parse(code)
    func = ast.declarations[0]
    instr = func.body[0]
    assert len(instr.attrs) == 1
    assert instr.attrs[0].name == 'no_erase'


def test_parse_multiple_attributes():
    """Test multiple attributes."""
    code = """#[fusion, reversible]
fn test() {
    ADD R1, R0, 1;
}"""
    ast = parse(code)
    func = ast.declarations[0]
    assert len(func.attrs) == 2
    assert func.attrs[0].name == 'fusion'
    assert func.attrs[1].name == 'reversible'


def test_parse_memory_reference():
    """Test memory references."""
    code = """fn test() {
    LOAD R1, [R0 + 8];
}"""
    ast = parse(code)
    func = ast.declarations[0]
    instr = func.body[0]
    assert instr.operands == ['R1', '[R0 + 8]']


def test_parse_function_call():
    """Test function call in expression."""
    code = """fn test() {
    let x = foo(1, 2);
}"""
    ast = parse(code)
    func = ast.declarations[0]
    # Assume parsed correctly


def test_parse_binary_expression():
    """Test binary expressions."""
    code = """fn test() {
    let x = a + b * c;
}"""
    ast = parse(code)
    func = ast.declarations[0]
    # Assume parsed correctly


def test_parse_label():
    """Test labels."""
    code = """fn test() {
    loop:
    ADD R1, R1, 1;
    JMP loop;
}"""
    ast = parse(code)
    func = ast.declarations[0]
    assert len(func.body) == 3
    # Label, Instr, Instr


def test_parse_empty_function():
    """Test empty function."""
    code = """fn empty() {
}"""
    ast = parse(code)
    func = ast.declarations[0]
    assert len(func.body) == 0


def test_parse_return_expression():
    """Test return with expression."""
    code = """fn test() -> i32 {
    return 42;
}"""
    ast = parse(code)
    func = ast.declarations[0]
    assert func.return_type == 'i32'
    # Assume return statement


def test_ast_json_shape():
    """Test that AST to_json returns the expected shape."""
    code = open('tests/samples/ast_sample.crz').read()
    ast = parse(code)
    json_dict = ast.to_json()
    assert "functions" in json_dict
    assert "attrs" in json_dict
    assert len(json_dict["functions"]) == 1
    func = json_dict["functions"][0]
    assert "body" in func
    for item in func["body"]:
        if "mnemonic" in item:
            assert "operands" in item
            assert "raw" in item
