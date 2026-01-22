# Dice Parser Implementation Notes

The dice parser has been refactored from a `RegexRouter`-based implementation to a `PLY` (Python Lex-Yacc) based implementation.

## Features

- **Compatibility**: Supports all existing dice expression formats, including:
    - Basic dice: `3d6`
    - Literal dice: `[1,2,3]`
    - Selectors: `1,2@5d10` (keeps the 1st and 2nd results)
    - Threshold functions: `10d10e6` (Success on 6+), `10d10f6` (Success on 6+, 1 subtracts)
    - Result functions: `3d6g` (sum), `3d6h` (max), `3d6l` (min), `3d6~` (none), `3d6=` (id)
    - Rerolls: `5d10r2` (reroll 2 lowest), `5d10r-2` (reroll 2 highest)
    - Sorting: `5d10s`
    - Explosions: `10d10!` (explode on max), `10d10!!` (explode on max and max-1)
    - Referencing previous rolls: `-d6`, `--d6`, etc.
    - Negative dice: `-3d6`

## Implementation Details

The implementation is split into four files:
1. `gamepack/DiceLexer.py`: Contains the `DiceLexer` class using `ply.lex`.
2. `gamepack/DiceExpressionParser.py`: Contains the `DiceExpressionParser` class using `ply.yacc`.
3. `gamepack/DiceParser.py`: Integrated the new parser into the `DiceParser.extract_diceparams` method.
4. `gamepack/RegexRouter.py`: Now contains the `DiceRegexRouter` utility class, which preserves the legacy regex-based parsing logic.

## Changes and Constraints

- **Strictness**: The parser is more structured than the previous regex-based one. It follows the general pattern: `[Selectors@]Dice[dSides][Options]`.
- **Conflict Handling**: Similar to the original `RegexRouter`, it detects "Interpretation Conflicts" if multiple result functions are specified (e.g., `10@3d6g` is invalid because both `10@` and `g` specify how to return the result).
- **Error Messages**: Invalid expressions will raise a `DiceCodeError` with a helpful usage hint.

## Usage specifics

The supported grammar is roughly:
```
[<Selectors>@]<Amount>[d<Sides>][<Options>]
```
Where:
- `Amount` can be a number (e.g. `3`), a negative number (e.g. `-3`), a literal list (e.g. `[1,2,3]`), or a reference to a previous roll (e.g. `-`).
- `Options` can include `r<N>`, `s`, `e<N>`, `f<N>`, `g`, `h`, `l`, `~`, `=`, and `!+` in any order.
