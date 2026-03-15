# Codebase Structure

**Analysis Date:** 2026-03-15

## Directory Layout

```
TreeSearch/
├── treesearch/              # Main package source code
│   ├── __init__.py          # Public API exports
│   ├── __main__.py          # python -m treesearch entry
│   ├── cli.py               # Command-line interface
│   ├── treesearch.py        # TreeSearch unified engine class
│   ├── tree.py              # Document model and tree utilities
│   ├── indexer.py           # File-to-tree conversion (md, text, code, json, csv)
│   ├── search.py            # Multi-document search pipeline
│   ├── fts.py               # SQLite FTS5 full-text search engine
│   ├── config.py            # Global configuration (TreeSearchConfig)
│   ├── tokenizer.py         # CJK/English tokenization
│   ├── utils.py             # Shared utilities (count_tokens)
│   ├── pathutil.py          # Path resolution, glob, directory walk
│   ├── ripgrep.py           # Optional ripgrep integration
│   └── parsers/             # Extensible parser registry
│       ├── __init__.py      # Parser exports
│       ├── registry.py      # ParserRegistry, SOURCE_TYPE_MAP
│       ├── ast_parser.py    # Python AST-based code parser
│       ├── treesitter_parser.py  # Tree-sitter multi-language parser
│       ├── pdf_parser.py    # PDF parser (pageindex)
│       ├── docx_parser.py   # DOCX parser (python-docx)
│       └── html_parser.py   # HTML parser (beautifulsoup4)
├── tests/                   # Test suite
├── examples/                # Usage examples and demos
│   ├── benchmark/           # Benchmarking utilities
│   ├── data/                # Sample data files
│   └── indexes/             # Generated index files
├── docs/                    # Documentation
├── .github/                 # GitHub workflows, issue templates
├── pyproject.toml           # Package metadata and dependencies
├── requirements.txt         # Development requirements
├── README.md                # English documentation
└── README_ZH.md             # Chinese documentation
```

## Directory Purposes

**treesearch/:**
- Purpose: Main package containing all source code
- Contains: Core modules, CLI, parsers subdirectory
- Key files: `treesearch.py`, `search.py`, `fts.py`, `indexer.py`, `tree.py`

**treesearch/parsers/:**
- Purpose: File type parsing registry and implementations
- Contains: Parser functions for each file type
- Key files: `registry.py` (dispatcher), `ast_parser.py` (Python), `treesitter_parser.py` (multi-language)

**tests/:**
- Purpose: Test suite with pytest
- Contains: Unit tests for each module, conftest.py fixtures
- Key files: `test_search.py`, `test_fts.py`, `test_indexer.py`, `test_tree.py`

**examples/:**
- Purpose: Usage demonstrations and RAG demo
- Contains: Basic demos, CLI workflow, RAG retrieval demo
- Key files: `05_rag_retrieval_demo.py`, `02_index_and_search.py`

**docs/:**
- Purpose: Project documentation
- Contains: Logo, additional documentation files

## Key File Locations

**Entry Points:**
- `treesearch/__init__.py`: Package exports - `TreeSearch`, `build_index`, `search`, `Document`, `FTS5Index`
- `treesearch/__main__.py`: Module execution entry (`python -m treesearch`)
- `treesearch/cli.py`: CLI implementation with `main()` function
- `treesearch/treesearch.py`: Primary `TreeSearch` class

**Configuration:**
- `pyproject.toml`: Package metadata, dependencies, optional extras, entry points
- `treesearch/config.py`: `TreeSearchConfig` dataclass, global config singleton

**Core Logic:**
- `treesearch/search.py`: Multi-document search pipeline, `PreFilter` protocol, `GrepFilter`
- `treesearch/fts.py`: `FTS5Index` class with BM25 scoring, document persistence
- `treesearch/indexer.py`: File parsing to tree structures, `build_index()` batch processor
- `treesearch/tree.py`: `Document` dataclass, tree traversal utilities

**Parsers:**
- `treesearch/parsers/registry.py`: `ParserRegistry`, extension mapping, pre-filter routing
- `treesearch/parsers/ast_parser.py`: Python AST-based structure extraction
- `treesearch/parsers/treesitter_parser.py`: Tree-sitter multi-language support

**Utilities:**
- `treesearch/tokenizer.py`: CJK/English tokenization with jieba, bigram modes
- `treesearch/pathutil.py`: Glob/directory resolution, .gitignore support
- `treesearch/ripgrep.py`: Optional ripgrep subprocess integration
- `treesearch/utils.py`: `count_tokens()` helper

**Testing:**
- `tests/conftest.py`: Pytest fixtures
- `tests/test_search.py`: Search pipeline tests
- `tests/test_fts.py`: FTS5 index tests
- `tests/test_indexer.py`: Indexer tests

## Naming Conventions

**Files:**
- Module files: snake_case (e.g., `treesearch.py`, `pathutil.py`)
- Test files: `test_<module>.py` (e.g., `test_search.py`, `test_fts.py`)
- Parser files: `<type>_parser.py` (e.g., `ast_parser.py`, `pdf_parser.py`)

**Directories:**
- Package directories: lowercase (e.g., `treesearch/`, `parsers/`)
- Test/examples: plural nouns (e.g., `tests/`, `examples/`, `docs/`)

**Classes:**
- PascalCase (e.g., `TreeSearch`, `Document`, `FTS5Index`, `ParserRegistry`, `GrepFilter`)

**Functions:**
- snake_case (e.g., `build_index`, `md_to_tree`, `search_sync`, `flatten_tree`)
- Async functions: prefixed with `a` (e.g., `aindex`, `asearch`) or just base name
- Private functions: prefixed with underscore (e.g., `_file_hash`, `_build_tree`)

**Variables:**
- snake_case for local variables
- SCREAMING_SNAKE_CASE for constants (e.g., `DEFAULT_IGNORE_DIRS`, `MAX_DIR_FILES`)

**Dataclass fields:**
- snake_case with optional `if_` prefix for boolean flags (e.g., `if_add_node_summary`)

## Where to Add New Code

**New Feature (search/index related):**
- Primary code: `treesearch/treesearch.py` (add methods to `TreeSearch` class)
- Tests: `tests/test_treesearch.py` (or appropriate test file)

**New File Type Parser:**
- Implementation: `treesearch/parsers/<type>_parser.py`
- Registration: Add to `treesearch/parsers/registry.py` in `_register_builtin_parsers()`
- Source type mapping: Add to `SOURCE_TYPE_MAP` in `registry.py`
- Pre-filter routing: Add to `PREFILTER_ROUTING` in `registry.py`

**New PreFilter Scorer:**
- Implementation: `treesearch/search.py` (implement `PreFilter` protocol)
- Integration: Add to `PREFILTER_ROUTING` or use directly in `search()`

**New Configuration Option:**
- Add field to `TreeSearchConfig` in `treesearch/config.py`
- Wire defaults in `build_index()` or `search()`

**New CLI Subcommand:**
- Implementation: `treesearch/cli.py` (add parser and `_run_<cmd>()` function)
- Registration: Add to `_SUBCOMMANDS` set

**Utilities:**
- Shared helpers: `treesearch/utils.py`
- Path-related: `treesearch/pathutil.py`
- Tokenization: `treesearch/tokenizer.py`

## Special Directories

**examples/indexes/:**
- Purpose: Generated SQLite database files from examples
- Generated: Yes (by running example scripts)
- Committed: No (in .gitignore)

**examples/data/:**
- Purpose: Sample input files for examples
- Generated: No
- Committed: Yes

**.venv/:**
- Purpose: Python virtual environment
- Generated: Yes (by user)
- Committed: No

**pytreesearch.egg-info/:**
- Purpose: Package metadata generated by setuptools
- Generated: Yes (by pip install)
- Committed: No

**.github/workflows/:**
- Purpose: GitHub Actions CI/CD workflows
- Generated: No
- Committed: Yes

## Module Dependency Graph

```
treesearch/
├── __init__.py ──────────> treesearch.py, search.py, fts.py, tree.py, config.py, indexer.py
├── treesearch.py ────────> tree.py, search.py, config.py, pathutil.py, indexer.py, fts.py
├── search.py ────────────> tree.py, config.py, fts.py, parsers/registry.py, ripgrep.py
├── indexer.py ───────────> tree.py, pathutil.py, parsers/, config.py, fts.py
├── fts.py ───────────────> tree.py, utils.py, tokenizer.py
├── tree.py ──────────────> fts.py (for persistence functions)
├── parsers/registry.py ──> indexer.py (deferred import for parsers)
├── pathutil.py ──────────> parsers/registry.py (for extension list)
└── tokenizer.py ─────────> config.py, utils.py
```

---

*Structure analysis: 2026-03-15*
