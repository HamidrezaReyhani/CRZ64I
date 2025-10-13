#!/bin/bash
set -e

# Run tests
pytest

# Lint
black --check .

# Type check
mypy src

# Build
python -m build

# Get version
version=$(python -c "from setuptools_scm import get_version; print(get_version())")

# Tag
git tag v$version

# Draft release
gh release create v$version --draft --title "v$version" --notes "Release v$version"
