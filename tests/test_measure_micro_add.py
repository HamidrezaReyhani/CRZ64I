import subprocess
import os
import pytest


def test_measure_micro_add():
    """Test the measure_micro_add script with small parameters."""
    # Run the script
    result = subprocess.run(
        [
            "/home/crzc/CRZ64I/venv/bin/python3",
            "tools/measure_micro_add.py",
            "--n",
            "100",
            "--runs",
            "3",
            "--out",
            "test_results.csv",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "Microbench: micro_add N=100 runs=3" in result.stdout
    assert "Improvement" in result.stdout
    assert os.path.exists("test_results.csv")

    # Check CSV content
    with open("test_results.csv", "r") as f:
        lines = f.readlines()
    assert len(lines) == 7  # header + 6 runs (3 uncompiled + 3 compiled)

    # Clean up
    os.remove("test_results.csv")
