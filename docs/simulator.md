# CRZ64I Simulator

## Features

- **Registers**: R0-R31 (64-bit), V0-V15 (vector)
- **Memory**: Addressable dictionary
- **Energy Model**: Configurable per-op energy
- **Thermal Model**: Passive cooling, hotspots
- **Metrics**: Cycles, joules, temperature

## API

```python
from crz.simulator.simulator import Simulator

sim = Simulator()
cycles, energy, temp, state = sim.run(ir, initial_state, metrics=True)
```

## CLI

```bash
crzsim run file.crz --n=10 --report=out.csv
```

## Energy Config

Load from JSON:

```json
{
  "ADD": {"energy": 1.5, "latency": 2},
  "LOAD": {"energy": 2.0, "latency": 3}
}
```

## Thermal Hotspots

Tracks temperature by component (ALU, MEM, etc.).
