# Technology Stack

**Analysis Date:** 2026-03-15

## Languages

**Primary:**
- Python 3.10+ - Main implementation language, supports 3.10-3.13

**Secondary:**
- None detected

## Runtime

**Environment:**
- Python 3.10+ (tested on 3.12 in CI)

**Package Manager:**
- pip - Standard Python package manager
- Lockfile: `requirements.txt` (present)

## Frameworks

**Core:**
- setuptools 68.0+ - Build backend and packaging
- wheel - Wheel distribution format support

**Testing:**
- pytest 7.0+ - Test framework with async support
- pytest-asyncio 0.21+ - Async test support
- pytest-cov - Coverage reporting

**Build/Dev:**
- Standard Python packaging via `pyproject.toml`

## Key Dependencies

**Critical:**
- SQLite3 (stdlib) - FTS5 full-text search engine, persistent inverted index
- asyncio (stdlib) - Async-first design for all core functions
- json (stdlib) - Document structure serialization
- re (stdlib) - Regex-based heading detection and text parsing

**Optional Enhancements:**
- jieba 0.42+ - Chinese text segmentation for CJK tokenization
- pysqlite3-binary 0.5+ - FTS5 fallback for systems without SQLite FTS5
- tree-sitter-languages 1.10+ - Multi-language code parsing (optional, 50+ languages)
- pageindex 0.1+ - PDF structure extraction
- python-docx 0.8+ - DOCX document parsing
- beautifulsoup4 4.12+ - HTML parsing
- pathspec 0.11+ - .gitignore pattern matching

**Development/External APIs:**
- openai 1.0+ - For RAG generation (SiliconFlow OpenAI-compatible API)
- nltk.stem.PorterStemmer - English stemming (lazy-loaded, optional)

**Benchmark/Analysis:**
- numpy 1.26+ - Benchmark metrics calculation
- python-dotenv 1.0+ - Environment variable loading

## Configuration

**Environment:**
- `TREESEARCH_CJK_TOKENIZER` - CJK tokenization mode ("auto" | "jieba" | "bigram" | "char")
- `SILICONFLOW_API_KEY` - API key for RAG generation
- `SILICONFLOW_MODEL` - Model name for RAG generation
- Configuration via `TreeSearchConfig` dataclass with `set_config()` / `get_config()`

**Build:**
- `pyproject.toml` - Project metadata, dependencies, and build configuration
- `requirements.txt` - Full dependency list for one-command install

**CLI Entry Point:**
- `treesearch` command via `[project.scripts]` in `pyproject.toml`
- Entry function: `treesearch.cli:main`

## Platform Requirements

**Development:**
- Python 3.10+ runtime
- pip package manager
- Git for version control
- Optional: ripgrep (`rg`) for accelerated GrepFilter matching

**Production:**
- Python 3.10+ runtime
- SQLite3 with FTS5 extension (or install pysqlite3-binary)
- No external services required for core search functionality
- Optional: OpenAI-compatible API endpoint for RAG generation

## Architecture Highlights

**No External Dependencies for Core:**
- No vector database required (no Pinecone, Milvus, Chroma)
- No embedding model required
- Pure SQLite FTS5 for indexing and search
- Zero-cost keyword matching (no LLM calls at search time)

**Document Format Support:**
- Markdown (.md, .markdown) - Heading-based tree structure
- Plain text (.txt, .log, .rst) - Rule-based heading detection
- Code files (.py, .java, .ts, .js, .go, .cpp, etc.) - AST + regex parsing
- JSON (.json) - Hierarchical key-value trees
- CSV (.csv) - Row-based leaf nodes
- HTML (.html, .htm) - BeautifulSoup parsing (optional)
- XML (.xml) - Tag-based structure
- PDF (.pdf) - pageindex extraction (optional)
- DOCX (.docx) - python-docx extraction (optional)

---

*Stack analysis: 2026-03-15*
