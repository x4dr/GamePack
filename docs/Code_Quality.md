# Code Quality, Deduplication, and Coverage Plan

This document outlines the strategy for improving the internal code quality of the GamePack library.

## 1. Deduplication Opportunities

### Item Management
- **`gamepack/Item.py` vs `gamepack/PBTAItem.py`**: Both handle item-like structures with markdown representations. There is likely overlapping logic in how attributes are parsed from tables and how they are serialized back.
- **Goal**: Factor out a common base class or utility for Item-like objects if patterns repeat.

### Wiki Parsing
- **`gamepack/WikiPage.py` and `gamepack/WikiCharacterSheet.py`**: Both involve parsing complex wiki structures. With the recent improvements to `MDPack.py`, much of the custom parsing logic in these files might be simplified or replaced by `MDObj` and `MDTable` methods.
- **Goal**: Leverage the enhanced `MDPack` to reduce boilerplate in wiki-related classes.

### Dice Parsing
- **`gamepack/DiceParser.py` and `gamepack/DiceExpressionParser.py`**: While `DiceExpressionParser` is the new primary parser, `DiceParser` still contains some regex-based pre-processing and "define" resolution.
- **Goal**: Evaluate if more of the "define" logic can be moved into the grammar or a shared resolution pass.

## 2. Increasing Test Coverage

Based on recent coverage reports, the following modules require additional testing to reach the 80%+ target:

| Module | Current Coverage | Targets |
|--------|-----------------|---------|
| `gamepack/fengraph.py` | 31% | Graph generation and node traversal edge cases. |
| `gamepack/endworld/EWCharacter.py` | 37% | Endworld-specific character initialization and state changes. |
| `gamepack/PBTAItem.py` | 53% | Item attribute parsing and move integration. |
| `gamepack/WikiCharacterSheet.py` | 63% | Field extraction from varied markdown templates. |
| `gamepack/Item.py` | 68% | Base item logic and total_table calculations. |
| `gamepack/WikiPage.py` | 68% | Link extraction and section management. |

### Strategy
1. **Identify Missing Paths**: Use `pytest --cov-report=html` to identify specific lines not covered.
2. **Unit Tests for Core Logic**: Focus on `EWCharacter` and `PBTAItem` logic.
3. **Mocking External Resources**: Ensure `WikiPage` tests don't rely on live network calls (most seem to use local markdown already).

## 3. Increasing Code Quality

### Type Hinting and LSP Issues
- **`gamepack/Dice.py` and `gamepack/DiceParser.py`**: Fix remaining LSP errors related to `Optional` types and attribute assignments.
- **Standardization**: Ensure all new code uses modern typing (e.g., `|` instead of `Union`).

### Error Handling
- **Custom Exceptions**: Move more generic "Descriptive" errors to a centralized `exceptions.py` or keep them in `Dice.py` if they are truly dice-specific.
- **Input Validation**: Use the improved `MDTable` and `MDList` robustness to fail gracefully with helpful messages.

### Refactoring `MDPack` Usage
- **Transition**: Update existing character sheet parsers to use the new `MDList` and `MDTable.row_dict` features to make the code more readable and less prone to index-based errors.
