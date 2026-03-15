# Coding Conventions

**Analysis Date:** 2026-03-15

## Language and Runtime

**Primary:** Python 3.10+
**Package Manager:** pip with `pyproject.toml` configuration
**Type Hints:** Modern Python type annotations used throughout (e.g., `list[str]`, `dict[str, float]`, `Optional[str]`)

## Naming Patterns

**Files:**
- Module names use snake_case: `treesearch.py`, `pathutil.py`, `ast_parser.py`
- Test files follow `test_<module>.py` pattern: `test_indexer.py`, `test_fts.py`
- Private/internal functions prefixed with underscore: `_extract_md_headings()`, `_file_hash()`

**Classes:**
- PascalCase: `TreeSearch`, `FTS5Index`, `Document`, `GrepFilter`, `PreFilter`
- Dataclasses for simple data containers: `TreeSearchConfig`, `Document`
- Protocol classes for interfaces: `PreFilter` with `@runtime_checkable`

**Functions:**
- snake_case: `build_index()`, `md_to_tree()`, `flatten_tree()`
- Async variants prefixed with `a`: `aindex()`, `asearch()`
- Private helpers prefixed with `_`: `_finalize_tree()`, `_detect_headings()`
- Sync wrappers explicitly named: `search_sync()`

**Variables:**
- snake_case for local variables and parameters
- Descriptive names preferred over abbreviations
- Class instance variables use leading underscore for "private": `_db_path`, `_conn`, `_weights`

**Constants:**
- UPPER_SNAKE_CASE at module level: `_RE_FRONT_MATTER`, `_DEFAULT_WEIGHTS`, `_FTS5_OPERATORS`
- Compiled regex patterns prefixed with `_RE_`: `_RE_CJK_CHAR`, `_RE_HAS_CJK`

## Code Style

**Formatting:**
- No explicit formatter configuration detected (no `.prettierrc`, `pyproject.toml [tool.black]`, etc.)
- 4-space indentation
- Max line length appears flexible (~100-120 characters observed)
- UTF-8 encoding declared at file top: `# -*- coding: utf-8 -*-`

**Docstrings:**
- Module-level docstrings with `@author` and `@description` tags
- Triple-quoted strings with Args/Returns sections
- Example code in docstrings uses `::` prefix with indented blocks

**Imports:**
```python
# Standard library first
import asyncio
import json
import logging
import os
import re

# Third-party
import pytest
from unittest.mock import patch

# Local imports last (relative for internal)
from .tree import Document, flatten_tree
from .config import get_config
```

## File Organization

**Module Structure:**
```python
# -*- coding: utf-8 -*-
"""
@author:Name(email)
@description: Brief description
"""
# Standard library imports
# Third-party imports
# Local imports

# Constants (UPPER_CASE)

# Classes
# Functions

# Private helpers (_prefix) grouped logically
```

**File Size:**
- Modules range from ~100 to ~1000 lines
- `treesearch/indexer.py` is the largest at ~913 lines
- `treesearch/utils.py` is smallest at ~30 lines

## Error Handling

**Patterns:**
- Explicit `ValueError` for invalid arguments:
  ```python
  if md_path and md_content:
      raise ValueError("Specify only one of md_path or md_content")
  ```

- `FileNotFoundError` for missing files:
  ```python
  if not os.path.isfile(src):
      raise FileNotFoundError(f"Database file not found: {src}")
  ```

- Graceful fallbacks with logging:
  ```python
  except (FileNotFoundError, OSError):
      return ""  # Empty string indicates file not available
  ```

- Warnings for missing optional dependencies:
  ```python
  import warnings
  warnings.warn(
      "SQLite FTS5 not available. Full-text search will use LIKE fallback",
      RuntimeWarning,
      stacklevel=2,
  )
  ```

**Exception Handling:**
- Catch specific exceptions, not bare `except:`
- Use context managers (`with` statements) for file/DB operations
- Log warnings for recoverable errors, re-raise for fatal ones

## Logging

**Framework:** Python `logging` module

**Pattern:**
```python
import logging
logger = logging.getLogger(__name__)

# Usage
logger.info("Building indexes for %d file(s)...", len(files))
logger.warning("Failed to index %s: %s", fp, e)
logger.debug("Skipping missing file: %s", abs_fp)
```

**Log Levels:**
- `INFO` for significant operations (indexing, search results)
- `WARNING` for recoverable issues (missing optional deps, query errors)
- `DEBUG` for detailed diagnostics

## Comments

**When to Comment:**
- Section dividers using comment blocks:
  ```python
  # ---------------------------------------------------------------------------
  # FTS5 Index Engine
  # ---------------------------------------------------------------------------
  ```

- Inline comments for non-obvious logic:
  ```python
  # ~4 chars per token for English, ~2 for CJK; use 3 as balanced estimate
  ```

- TODO comments not observed in codebase (clean state)

**Docstrings:**
- All public functions have docstrings
- Args/Returns sections with type hints in description
- Example usage included for complex APIs

## Function Design

**Size:** Functions range from 5 to 80 lines; complex functions refactored into helpers

**Parameters:**
- Use keyword-only arguments with `*` separator (not observed, but kwargs pattern used)
- Optional parameters with `None` defaults
- Configuration via dataclass (`TreeSearchConfig`) rather than many parameters

**Return Values:**
- Consistent return types (dict with predictable keys)
- Tuple returns for related values: `tuple[list[dict], list[str]]`
- `Optional[T]` for may-return-None functions

**Pattern - Async/Sync Pairs:**
```python
async def asearch(self, query: str, **kwargs) -> dict:
    """Async implementation."""
    ...

def search(self, query: str, **kwargs) -> dict:
    """Sync wrapper."""
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            raise RuntimeError("Event loop is already running. Please use `await asearch()` instead.")
    except RuntimeError as e:
        if "Event loop is already running" in str(e):
            raise
        pass
    return asyncio.run(self.asearch(query, **kwargs))
```

## Module Design

**Exports:**
- Explicit `__all__` in `treesearch/__init__.py`
- Re-export public API from main module:
  ```python
  from treesearch.treesearch import TreeSearch
  from treesearch.indexer import build_index, md_to_tree, text_to_tree
  ```

**Internal Organization:**
- Private helpers with `_` prefix for module-internal use
- Related functions grouped in sections with comment dividers
- Lazy imports for optional dependencies:
  ```python
  def _ensure_jieba():
      """Lazy-load jieba to avoid import cost when unused."""
      global _JIEBA_LOADED, _jieba
      if not _JIEBA_LOADED:
          try:
              import jieba
              _jieba = jieba
          except ImportError:
              _jieba = None
          _JIEBA_LOADED = True
      return _jieba
  ```

## Configuration

**Pattern:**
- `dataclass` for configuration: `TreeSearchConfig`
- Global singleton with `get_config()`, `set_config()`, `reset_config()`
- Environment variable overrides via `from_env()` class method
- Priority: `set_config()` > env vars > defaults

---

*Convention analysis: 2026-03-15*
