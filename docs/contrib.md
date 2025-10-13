# Contributing to CRZ64I

## Development Setup

```bash
git clone https://github.com/your-repo/crz64i.git
cd crz64i
pip install -e .
pip install pytest black mypy
```

## Testing

```bash
pytest
black --check .
mypy src/
```

## Code Style

- Use black for formatting
- Type hints everywhere
- Docstrings for all functions
- Dataclasses for AST/IR

## Adding Instructions

1. Update crz64i.lark grammar
2. Add to AST if needed
3. Implement in simulator
4. Add tests
5. Update docs

## Pull Requests

- Branch from main
- Run full test suite
- Update docs if needed
- Squash commits
