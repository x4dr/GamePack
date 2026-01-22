# MDPack Behavioral Documentation

This document describes the observed behaviors and edge cases of the `gamepack.MDPack` module.

## MDList & MDChecklist

### Implementation Details
- **Unified Logic**: `MDList` handles both regular and checklist items. `MDChecklist` is maintained as a legacy compatibility subclass.
- **Nesting**: Supported via `level` attribute. Indentation is normalized to 2 spaces per level in `to_md()`.
- **Bullet Detection**: Supports `-`, `*`, `+`, and numbered lists (e.g., `1.`).
- **YAML Safety**: The list pattern requires a space after the bullet (e.g., `- Item` not `-Item`) to avoid misinterpreting YAML frontmatter (`---`) as a list.

### Ambiguity & Questions
- **Indentation Levels**: Should we support custom indentation sizes (e.g., 4 spaces)? Currently hardcoded to 2 for canonicalization.
- **Mixed Bullets**: Should a single list support multiple bullet types? `to_md()` currently preserves the bullet captured during parsing for each item.

## MDTable

### Parsing Improvements
- **Robustness**: The parser now consistently handles outer pipes and missing leading empty cells. It automatically pads or truncates rows to match the header count.
- **Ambiguity rejection**: Rows that don't match the table structure are treated as separate lines if they don't contain pipes.

### Data Access
- **Row Dictionary**: `table.row(key)` returns a full dictionary `{header: value}` for the first row matching the key in its first column.
- **Rows Dictionary**: `table.rows_dict` returns a mapping of `row_id -> row_data_dict`.

### Normalization (Serialization)
- **Pretty Format**: `to_md()` ensures pipes line up and columns have consistent padding. Separator rows are adjusted to match the longest content width.

## MDObj

### Tree Structure & Extraction
- **General Lists**: `MDObj` now extracts ALL lists into `self.lists`. `self.checklists` is a legacy property that filters `self.lists`.
- **Order Preservation**: `to_md()` now combines tables and lists and reinserts them into the plaintext based on their original line numbers, preserving the relative order of all document elements.

### Serialization
- **Canonical Format**: `to_md()` implements a clean "optimal" format:
    - Headers have one blank line before them (unless at start of doc).
    - Headers have one newline after them.
    - Document elements (tables, lists, text) are separated by consistent newlines.
- **Question**: Should we preserve "excessive" blank lines from the original document? Currently, `to_md()` canonicalizes them away to maintain an optimal look.

## Observed Ambiguities

1. **Mixed Lists**: If a list has some items with checkboxes and some without, it is treated as a single `MDList`. 
2. **`__getitem__` Collision**: If a header name matches a table key, the child node (header) always wins.
3. **Table Row ID**: We assume the first column is a unique identifier when using `table.row(key)` or `table.get(key)`. If IDs are duplicated, only the first match is returned.
