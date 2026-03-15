# Testing Patterns

**Analysis Date:** 2026-03-15

## Test Framework

**Runner:**
- pytest (version >= 7.0)
- pytest-asyncio (version >= 0.21)
- pytest-cov for coverage
- Config: `pyproject.toml` under `[tool.pytest.ini_options]`

**Configuration:**
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**Run Commands:**
```bash
pytest tests/                          # Run all tests
pytest tests/ -v                       # Verbose output
pytest tests/ --tb=short               # Short traceback
pytest tests/ --cov=treesearch         # With coverage
pytest tests/ --cov=treesearch --cov-report=term-missing  # Coverage with line numbers
```

**CI Integration:**
```bash
# From .github/workflows/ubuntu.yml
python -m pytest tests/ -v --tb=short --cov=treesearch --cov-report=term-missing
```

## Test File Organization

**Location:**
- Separate `tests/` directory at project root
- Not co-located with source files

**Naming:**
- Pattern: `test_<module_name>.py`
- Examples: `test_indexer.py`, `test_fts.py`, `test_search.py`, `test_tree.py`

**Structure:**
```
tests/
├── conftest.py           # Shared fixtures
├── test_cli.py           # CLI tests
├── test_config.py        # Configuration tests
├── test_fts.py           # FTS5 index tests
├── test_indexer.py       # Indexing tests
├── test_pathutil.py      # Path utility tests
├── test_ripgrep.py       # Ripgrep integration tests
├── test_search.py        # Search pipeline tests
├── test_tokenizer.py     # Tokenization tests
├── test_tree.py          # Tree structure tests
└── test_utils.py         # Utility function tests
```

## Test Structure

**Suite Organization:**
```python
class TestExtractMdHeadings:
    """Tests for _extract_md_headings function."""

    def test_basic_headings(self, sample_md_file):
        """Test extraction of basic markdown headings."""
        with open(sample_md_file, "r") as f:
            content = f.read()
        headings, lines = _extract_md_headings(content)
        titles = [h["title"] for h in headings]
        assert "Overview" in titles
        assert "Architecture" in titles

    def test_ignores_code_blocks(self):
        """Headings inside code blocks should be ignored."""
        content = "# Real Heading\n\n```\n# Not a heading\n```\n"
        headings, lines = _extract_md_headings(content)
        assert "Not a heading" not in [h["title"] for h in headings]
```

**Class-Based Organization:**
- Tests grouped by function/class under test
- Class names: `Test<FunctionName>` or `Test<ClassName>`
- One class per logical grouping

**Async Tests:**
```python
class TestMdToTree:
    @pytest.mark.asyncio
    async def test_basic_structure(self, sample_md_file):
        result = await md_to_tree(md_path=sample_md_file)
        assert "doc_name" in result
        assert "structure" in result
```

## Fixtures and Factories

**Shared Fixtures (`conftest.py`):**
```python
@pytest.fixture
def sample_md_file():
    """Create a temp Markdown file for testing."""
    content = """\
# Overview
This document describes the system.

## Architecture
The system uses microservices architecture.
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def sample_tree_structure():
    """A pre-built tree structure for testing search/retrieval."""
    return [
        {
            "title": "Architecture",
            "summary": "System architecture overview.",
            "node_id": "0",
            "nodes": [...]
        }
    ]
```

**Autouse Fixtures:**
```python
_ENV_PREFIXES = ("TREESEARCH_", "OPENAI_")

@pytest.fixture(autouse=True)
def _isolate_env_and_config():
    """Remove .env-injected vars before each test, restore after."""
    from treesearch.config import reset_config
    from treesearch.fts import reset_fts_index

    saved = {}
    for k in list(os.environ):
        if k.startswith(_ENV_PREFIXES):
            saved[k] = os.environ.pop(k)
    reset_config()
    reset_fts_index()
    yield
    # Restore
    os.environ.update(saved)
    reset_config()
    reset_fts_index()
```

**Module-Local Fixtures:**
```python
# In test_fts.py
@pytest.fixture
def sample_document():
    """Create a sample Document for testing."""
    structure = [
        {"title": "Introduction", "node_id": "0", ...}
    ]
    return Document(
        doc_id="test_doc",
        doc_name="Test Document",
        structure=structure,
    )


@pytest.fixture
def fts_index():
    """Create an in-memory FTS5 index."""
    idx = FTS5Index(db_path=None)
    yield idx
    idx.close()
```

## Mocking

**Framework:** `unittest.mock`

**Patterns:**
```python
from unittest.mock import patch

# Patching environment variables
def test_cjk_tokenizer_from_env(self):
    env = {"TREESEARCH_CJK_TOKENIZER": "bigram"}
    with patch.dict(os.environ, env, clear=False):
        c = TreeSearchConfig.from_env()
    assert c.cjk_tokenizer == "bigram"


# Patching functions
def test_native_fallback_no_rg(self, sample_tree_structure):
    doc = Document(...)
    grep = GrepFilter([doc])
    with patch("treesearch.ripgrep.rg_available", return_value=False):
        scores = grep.score_nodes("FastAPI", doc.doc_id)
    assert len(scores) > 0
```

**What to Mock:**
- External dependencies (ripgrep availability)
- Environment variables
- File system operations (when testing logic, not I/O)

**What NOT to Mock:**
- Internal business logic
- Data structure operations
- SQLite/FTS5 operations (use in-memory databases instead)

## Test Patterns

**Result Assertion:**
```python
def test_basic_search(self, fts_index, sample_document):
    fts_index.index_document(sample_document)
    results = fts_index.search("machine learning")
    assert len(results) > 0
    assert any(r["node_id"] == "0" for r in results)
```

**State Verification:**
```python
def test_index_incremental(self, fts_index, sample_document):
    """Second indexing with same content should be skipped."""
    count1 = fts_index.index_document(sample_document)
    assert count1 == 5
    count2 = fts_index.index_document(sample_document)
    assert count2 == 0  # skipped due to hash match
```

**Exception Testing:**
```python
def test_both_path_and_content_raises(self, sample_md_file):
    with pytest.raises(ValueError, match="only one"):
        await md_to_tree(md_path=sample_md_file, md_content="# Test")


def test_missing_db_exits(self):
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(SystemExit):
            _load_documents_from_dir(tmpdir)
```

**Round-Trip Testing:**
```python
def test_round_trip(self, sample_tree_structure):
    """Save and load should preserve data."""
    index = {"doc_name": "test", "structure": sample_tree_structure}
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        save_index(index, db_path, doc_id="test")
        doc = load_index(db_path, doc_id="test")
        assert doc.doc_name == "test"
        assert len(doc.structure) == 2
```

**Parameterized Tests:**
Not observed in current codebase but pytest supports:
```python
@pytest.mark.parametrize("input,expected", [
    ("simple", ["simple"]),
    ("two words", ["two", "words"]),
])
def test_tokenize(input, expected):
    assert tokenize(input) == expected
```

## Coverage

**Requirements:** No explicit coverage threshold enforced in configuration

**View Coverage:**
```bash
pytest tests/ --cov=treesearch --cov-report=html
open htmlcov/index.html
```

**CI Coverage:**
```yaml
# .github/workflows/ubuntu.yml
- name: Run tests
  run: |
    python -m pytest tests/ -v --tb=short --cov=treesearch --cov-report=term-missing
```

## Test Types

**Unit Tests:**
- Individual functions: `_extract_md_headings()`, `_detect_headings()`, `_build_tree()`
- Class methods: `Document.get_node_by_id()`, `FTS5Index.search()`
- Utility functions: `count_tokens()`, `tokenize()`
- Pure functions with no external dependencies

**Integration Tests:**
- `test_fts.py`: SQLite FTS5 indexing and search
- `test_search.py`: Full search pipeline with FTS5 + GrepFilter
- `test_indexer.py`: File parsing and tree building
- Tests that involve multiple modules working together

**End-to-End Tests:**
- `test_cli.py`: Command-line interface parsing and execution
- `test_treesearch.py` (implicit): Full TreeSearch class usage

**Async Tests:**
```python
@pytest.mark.asyncio
async def test_fts5_search_returns_results(self, sample_tree_structure):
    doc = Document(doc_id="test", doc_name="Test Doc", structure=sample_tree_structure)
    result = await search(query="backend Python FastAPI", documents=[doc])
    assert isinstance(result, dict)
```

## Common Patterns

**Temporary Files/Directories:**
```python
def test_persistent_index(self, tmp_path):
    """pytest's tmp_path fixture for temporary directories."""
    db_path = str(tmp_path / "test_index.db")
    idx = FTS5Index(db_path=db_path)
    idx.index_document(sample_document)
    idx.close()
```

**Fixture Cleanup:**
```python
@pytest.fixture
def fts_index():
    idx = FTS5Index(db_path=None)
    yield idx
    idx.close()  # Cleanup after test
```

**Isolation:**
- Reset global singletons between tests
- Use in-memory databases for unit tests
- Clear environment variables

## Adding New Tests

**For a new module `treesearch/newmodule.py`:**
1. Create `tests/test_newmodule.py`
2. Import functions/classes to test
3. Add fixtures to `tests/conftest.py` if reusable
4. Use class-based organization: `class TestNewFunction:`
5. For async functions, use `@pytest.mark.asyncio`

**Test file template:**
```python
# -*- coding: utf-8 -*-
"""
Tests for treesearch.newmodule module.
"""
import pytest
from treesearch.newmodule import NewClass, new_function


class TestNewClass:
    def test_initialization(self):
        obj = NewClass()
        assert obj is not None

    def test_method(self):
        obj = NewClass()
        result = obj.method()
        assert result == expected


class TestNewFunction:
    def test_basic_case(self):
        result = new_function("input")
        assert result == "expected"

    def test_edge_case(self):
        with pytest.raises(ValueError):
            new_function("")
```

---

*Testing analysis: 2026-03-15*
