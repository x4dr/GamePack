# GamePack Development Guidelines

This document contains guidelines and commands for agentic coding agents working on the GamePack repository.

## Project Overview

GamePack is a Python 3.14+ game mechanics library factored out from NossiNet. It provides dice rolling, character management, and wiki parsing functionality for tabletop RPG systems.

## Essential Commands

### Testing
```bash
# Run all tests
uv run python -m pytest

# Run single test file
uv run python -m pytest tests/test_Dice.py

# Run specific test method
uv run python -m pytest tests/test_Dice.py::TestDice::test_param -v

# Run tests with coverage
uv run python -m pytest --cov=gamepack
```

### Code Formatting and Linting
```bash
# Format code (Black)
uv run black .

# Type check with mypy strict
uv run mypy --strict src/ gamepack/

# Lint with Ruff
uv run ruff check .

# Run pre-commit hooks (includes Black, Ruff, mypy, and additional checks)
uv run pre-commit run --all-files
```

### Dependencies and Environment
```bash
# Install all dependencies (including dev)
uv sync

# Install dev dependencies (legacy fallback)
uv pip install -e ".[dev]"

# Project uses Python 3.14+ (as specified in pyproject.toml)
# Virtual environment is managed by uv in .venv/
```

## Code Style Guidelines

### Import Organization
- Standard library imports first, sorted alphabetically
- Third-party imports next, sorted alphabetically
- Local imports last, sorted alphabetically
- Use built-in generics (`list[]`, `dict[]`) over `typing` equivalents
- Example pattern follows PEP8:
```python
import itertools
import re
import time

from collections.abc import Sequence
from typing import Self

from gamepack.Item import Item
from gamepack.DiceParser import fullparenthesis
```

### Type Annotations
- Use modern typing syntax (Python 3.14+ features available)
- Class variables use type annotations with `:` syntax
- Union types: Use `X | None`, never `Union[X, None]`
- Generic types: Use `list[Item]`, `dict[str, str]`, never `List[Item]`, `Dict[str, str]`
- Import ABCs from `collections.abc` (e.g., `Sequence`, `Mapping`) not from `typing`

### Naming Conventions
- Classes: `PascalCase` (e.g., `FenCharacter`, `DescriptiveError`)
- Functions and methods: `snake_case` (e.g., `roll_v`, `dicecache_db`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `table_name`, `table_all`)
- Private methods: prefix with underscore (`_private_method`)
- Module variables: `snake_case` (e.g., `cache`, `logger`)

### Error Handling
- Use custom exception classes that inherit from `Exception`
- Example: `class DescriptiveError(Exception): pass`
- Raise specific exceptions with descriptive error messages
- Use `pytest.raises` in tests for specific error messages

### Documentation and Comments
- Use comprehensive docstrings (Google style) for all public APIs
- Use inline comments sparingly, only for complex logic

### Code Structure
- Class attributes defined at class level with type annotations
- Instance variables initialized in `__init__`
- Use `Self` for return type annotations where appropriate
- All function signatures have full type hints (parameters and return types)

### Testing Conventions
- Use pytest style (plain functions, fixtures, parametrize)
- Test classes: `TestClassName` (no base class needed)
- Test methods/functions: `test_specific_behavior`
- Use fixtures for setup/teardown over `setUp()`/`tearDown()`
- Use `pytest.raises` over `assertRaises`
- Test files are named `test_ModuleName.py` in the `tests/` directory

### Configuration Files
- **pyproject.toml**: Project metadata, dependencies, tool configuration (Black, Ruff, mypy)
- **.pre-commit-config.yaml**: Pre-commit hooks (Black, Ruff, mypy, various checks)

## Key Patterns in Codebase

### Data Classes and Items
- Classes sometimes have an  attribute for an associated markdown file
- Item classes use tuple constants for field name matching (e.g., `table_name = ("objekt", "object", "name")`)
- Cache patterns using class-level dictionaries for performance

### Dice System
- Complex dice rolling mechanics with various return functions
- Supports explosions, thresholds, and different dice behaviors
- Uses logging for debugging (`logger = logging.getLogger(__name__)`)

### Wiki and Markdown Integration
- Heavy integration with markdown processing (`MDObj`, `MDTable`)
- Character sheets and items have wiki representation capabilities
- Multi-language support (English/German field names)

## Development Notes

- Pre-commit hooks handle most formatting automatically
- The codebase mixes English and German in some field names - preserve this pattern
- SQLite database is used for dice result caching (`dicecache.sqlite`)
- Some files support multiple Python versions (cache shows 3.11, 3.13, 3.14)
- this project is intended to be used with uv only
- do not commit autonomously, just ready things for the commit and stage them

## Performance Considerations

- Use caching for expensive operations (see `item_cache` patterns)
- Database connections use singleton pattern (`dicecache_db()`)
- Import optimizations are in place for frequently accessed modules

When working on this codebase, always run pre-commit hooks and mypy before committing, and ensure your changes pass all existing tests.
Keep Coverage above 80%
