import pytest
from crz.simulator.simulator import Simulator, compile_file
from crz.compiler.parser import parse_text
from crz.compiler.codegen_sim import codegen

def test_sandbox_write_io_denied():
    """Test that WRITE_IO is denied in sandbox."""
    code = """
fn test() {
    WRITE_IO R0, R1;
}
"""
    ast = parse_text(code)
    ir = codegen(ast)
    sim = Simulator()
    sim.sandbox_allow_io = False  # Default
    with pytest.raises(PermissionError, match="WRITE_IO not allowed in sandbox"):
        sim.run_program(ir)

def test_sandbox_dma_start_denied():
    """Test that DMA_START is denied in sandbox."""
    code = """
fn test() {
    DMA_START R0, R1;
}
"""
    ast = parse_text(code)
    ir = codegen(ast)
    sim = Simulator()
    sim.sandbox_allow_dma = False  # Default
    with pytest.raises(PermissionError, match="DMA_START not allowed in sandbox"):
        sim.run_program(ir)

def test_sandbox_write_io_allowed():
    """Test that WRITE_IO is allowed when permitted."""
    code = """
fn test() {
    WRITE_IO R0, R1;
}
"""
    ast = parse_text(code)
    ir = codegen(ast)
    sim = Simulator()
    sim.sandbox_allow_io = True
    # Should not raise
    sim.run_program(ir)

def test_sandbox_dma_start_allowed():
    """Test that DMA_START is allowed when permitted."""
    code = """
fn test() {
    DMA_START R0, R1;
}
"""
    ast = parse_text(code)
    ir = codegen(ast)
    sim = Simulator()
    sim.sandbox_allow_dma = True
    # Should not raise
    sim.run_program(ir)
