# Architecture

**Analysis Date:** 2026-03-15

## Pattern Overview

**Overall:** Layered async-first library with SQLite FTS5 as the storage/search backbone

**Key Characteristics:**
- Tree-structured document indexing with hierarchical node representation
- SQLite FTS5 full-text search (no vector embeddings, no external DB)
- Async-first design with sync wrappers for convenience
- Plugin-style parser registry for extensible file type support
- PreFilter protocol for composable scoring strategies

## Layers

**API Layer (User-facing):**
- Purpose: Single entry point for users - `TreeSearch` class
- Location: `treesearch/treesearch.py`
- Contains: `TreeSearch` class with `index()`, `search()`, `save_index()`, `load_index()` methods
- Depends on: indexer, search, fts, tree modules
- Used by: CLI, user code

**CLI Layer:**
- Purpose: Command-line interface for `treesearch` command
- Location: `treesearch/cli.py`, `treesearch/__main__.py`
- Contains: `main()` entry point, subcommand parsers for `index`, `search`
- Depends on: TreeSearch API layer
- Used by: End users via `treesearch` command

**Search Layer:**
- Purpose: Multi-document search with routing and scoring
- Location: `treesearch/search.py`
- Contains: `search()` async function, `GrepFilter`, `PreFilter` protocol, `_CombinedScorer`
- Depends on: tree, fts, config modules
- Used by: TreeSearch API layer

**Indexer Layer:**
- Purpose: Build tree structures from various file types
- Location: `treesearch/indexer.py`
- Contains: `build_index()`, `md_to_tree()`, `text_to_tree()`, `code_to_tree()`, `json_to_tree()`, `csv_to_tree()`
- Depends on: tree, pathutil, parsers modules
- Used by: TreeSearch API layer

**Storage Layer (FTS5):**
- Purpose: SQLite FTS5 full-text search and document persistence
- Location: `treesearch/fts.py`
- Contains: `FTS5Index` class with BM25 scoring, document storage, index metadata
- Depends on: tree, tokenizer, utils modules
- Used by: indexer, search modules

**Parser Layer:**
- Purpose: File type detection and parsing to tree structures
- Location: `treesearch/parsers/` directory
- Contains: `ParserRegistry`, `registry.py`, `ast_parser.py`, `treesitter_parser.py`, `pdf_parser.py`, `docx_parser.py`, `html_parser.py`
- Depends on: External parsers (jieba, tree-sitter-languages, pageindex, python-docx, beautifulsoup4)
- Used by: indexer module

**Core Data Layer:**
- Purpose: Data models and tree operations
- Location: `treesearch/tree.py`
- Contains: `Document` dataclass, tree traversal functions (`flatten_tree`, `build_tree_maps`, `get_leaf_nodes`), persistence helpers
- Depends on: fts module (for persistence)
- Used by: All layers

**Utility Layer:**
- Purpose: Shared helpers and configuration
- Location: `treesearch/config.py`, `treesearch/tokenizer.py`, `treesearch/utils.py`, `treesearch/pathutil.py`, `treesearch/ripgrep.py`
- Contains: `TreeSearchConfig`, `tokenize()`, `count_tokens()`, `resolve_paths()`, `rg_search()`
- Depends on: External libs (jieba, nltk, pathspec)
- Used by: All layers

## Data Flow

**Indexing Flow:**

1. User calls `TreeSearch.index("docs/*.md", "src/")` or `build_index()`
2. `pathutil.resolve_paths()` expands globs/directories into file list
3. `indexer.build_index()` iterates files with concurrency control
4. `ParserRegistry` dispatches to appropriate parser (`md_to_tree`, `code_to_tree`, etc.)
5. Parser builds hierarchical tree structure with node_ids, summaries
6. `FTS5Index.index_document()` persists tree + indexes nodes in FTS5
7. Returns list of `Document` objects

**Search Flow:**

1. User calls `TreeSearch.search(query)` or `search()`
2. If no documents, lazy-loads or builds index from pending paths
3. `search()` performs document routing via `FTS5Index.search_with_aggregation()`
4. Top-K documents selected based on aggregated FTS5 scores
5. PreFilter scorers (GrepFilter + FTS5Index) score nodes within each document
6. Ancestor score propagation adds context to parent nodes
7. Results merged by strategy (interleave/per_doc/global_score)
8. Returns `{"documents": [...], "query": str, "flat_nodes": [...]}`

**State Management:**
- All state stored in SQLite `.db` file (tree structures, FTS5 indexes, file hashes)
- `TreeSearch.documents` holds in-memory `Document` list
- `FTS5Index` uses WAL mode for concurrent read/write
- Incremental indexing via mtime/size fingerprints in `index_meta` table

## Key Abstractions

**Document:**
- Purpose: Represents a single indexed document with its tree structure
- Examples: `treesearch/tree.py` - `Document` dataclass
- Pattern: Dataclass with `doc_id`, `doc_name`, `structure` (tree), `metadata`, `source_type`
- Methods: `get_node_by_id()` for O(1) node lookup via cached map

**Tree Node:**
- Purpose: Single node in document tree hierarchy
- Examples: Dict with `node_id`, `title`, `text`, `summary`, `nodes` (children), `line_start`, `line_end`
- Pattern: Recursive dict structure with `nodes` list for children

**PreFilter Protocol:**
- Purpose: Interface for node pre-scoring strategies
- Examples: `treesearch/search.py` - `PreFilter` protocol, `GrepFilter` class
- Pattern: Protocol with `score_nodes(query, doc_id) -> dict[str, float]`
- Implementations: `FTS5Index`, `GrepFilter`, `_CombinedScorer`

**ParserRegistry:**
- Purpose: Maps file extensions to async parser functions
- Examples: `treesearch/parsers/registry.py` - `ParserRegistry` class
- Pattern: Static registry with `register()`, `get()`, `supported_extensions()`
- Built-in parsers registered at module load time

## Entry Points

**CLI Entry:**
- Location: `treesearch/cli.py:main()`
- Triggers: `treesearch` command or `python -m treesearch`
- Responsibilities: Arg parsing, subcommand dispatch, output formatting

**Library Entry (Primary):**
- Location: `treesearch/treesearch.py:TreeSearch`
- Triggers: `from treesearch import TreeSearch`
- Responsibilities: Unified API for indexing, searching, persistence

**Library Entry (Low-level):**
- Location: `treesearch/__init__.py`
- Triggers: `from treesearch import build_index, search, FTS5Index, Document`
- Responsibilities: Exports all public APIs

**Module Entry:**
- Location: `treesearch/__main__.py`
- Triggers: `python -m treesearch`
- Responsibilities: Delegates to `cli.main()`

## Error Handling

**Strategy:** Graceful degradation with fallbacks

**Patterns:**
- FTS5 unavailable -> fall back to LIKE-based search in `fts.py`
- Tree-sitter unavailable -> fall back to regex-based code parsing
- Optional dependencies (jieba, pathspec, PDF parsers) -> gracefully skip if not installed
- File read errors -> log warning and skip file during batch indexing
- `rg` unavailable -> fall back to native Python matching in `GrepFilter`

## Cross-Cutting Concerns

**Logging:** Python `logging` module with `logger = logging.getLogger(__name__)` per module

**Validation:**
- File path validation in `pathutil.py`
- Query tokenization in `tokenizer.py`
- Extension-to-parser mapping in `ParserRegistry`

**Configuration:**
- Global `TreeSearchConfig` dataclass in `config.py`
- Config priority: `set_config()` > env vars > defaults
- Environment variables: `TREESEARCH_CJK_TOKENIZER`

**Concurrency:**
- Async/await throughout with `asyncio.Semaphore` for rate limiting
- Sync wrappers use `asyncio.run()` for compatibility
- SQLite WAL mode for concurrent read/write safety

**Internationalization:**
- CJK tokenization with jieba/bigram/char modes
- English tokenization with NLTK stemming (optional)

---

*Architecture analysis: 2026-03-15*
