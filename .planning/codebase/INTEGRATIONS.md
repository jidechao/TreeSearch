# External Integrations

**Analysis Date:** 2026-03-15

## APIs & External Services

**LLM Generation (Optional):**
- SiliconFlow / OpenAI-compatible APIs - RAG generation stage
  - SDK/Client: `openai>=1.0`
  - Auth: `SILICONFLOW_API_KEY` or `OPENAI_API_KEY` environment variable
  - Base URL: Configurable (default: `https://api.siliconflow.cn/v1`)
  - Example model: `Pro/zai-org/GLM-5`
  - Usage: `examples/05_rag_retrieval_demo.py` demonstrates RAG retrieval + generation

**Note:** LLM is NOT required for core TreeSearch functionality. It's only used for optional RAG answer generation.

## Data Storage

**Databases:**
- SQLite3 - Built-in Python stdlib
  - Connection: File-based `.db` files (e.g., `indexes/index.db`)
  - Client: Direct `sqlite3` module
  - FTS5 virtual tables for full-text search
  - WAL mode for concurrent read/write
  - Persistent storage of tree structures and indexes

**File Storage:**
- Local filesystem only
  - Document sources: Various file formats (.md, .py, .txt, .pdf, etc.)
  - Index databases: SQLite `.db` files
  - JSON index files: Legacy format (being replaced by SQLite)

**Caching:**
- None (no Redis/Memcached)
- SQLite WAL mode provides efficient incremental updates

## Authentication & Identity

**Auth Provider:**
- None (local library)
  - No authentication required for core functionality
  - Optional API key for external LLM services

## Monitoring & Observability

**Error Tracking:**
- None detected

**Logs:**
- Python `logging` module
  - Logger name: `treesearch.*`
  - Levels: INFO, WARNING, DEBUG
  - Used throughout codebase for indexing progress and search operations

## CI/CD & Deployment

**Hosting:**
- PyPI - Package distribution as `pytreesearch`
  - PyPI URL: https://pypi.org/project/pytreesearch/

**CI Pipeline:**
- GitHub Actions
  - Workflow: `.github/workflows/ubuntu.yml`
  - Triggers: push to main/master, pull requests, manual dispatch
  - Python version: 3.12
  - Steps: Install from PyPI, install dependencies, run pytest with coverage

**Repository:**
- GitHub: https://github.com/shibing624/TreeSearch

## Environment Configuration

**Required env vars:**
- None required for core functionality

**Optional env vars:**
- `TREESEARCH_CJK_TOKENIZER` - CJK tokenization mode ("auto" | "jieba" | "bigram" | "char")
- `SILICONFLOW_API_KEY` - API key for RAG generation with SiliconFlow
- `SILICONFLOW_MODEL` - Model name for RAG generation
- `OPENAI_API_KEY` - Alternative API key (fallback for SILICONFLOW_API_KEY)

**Secrets location:**
- Environment variables only
- No secrets management service

**Configuration via code:**
```python
from treesearch import TreeSearchConfig, set_config

config = TreeSearchConfig(
    max_nodes_per_doc=5,
    top_k_docs=3,
    cjk_tokenizer="auto",
    # FTS5 column weights
    fts_title_weight=5.0,
    fts_body_weight=10.0,
)
set_config(config)
```

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## External Tool Integration

**ripgrep (Optional Acceleration):**
- Tool: `rg` command-line utility
- Purpose: Accelerated literal/regex matching in `GrepFilter`
- Detection: `shutil.which("rg")` at runtime
- Fallback: Pure Python regex scanning if `rg` unavailable
- Implementation: `treesearch/ripgrep.py`

**tree-sitter (Optional Parsing):**
- Package: `tree-sitter-languages>=1.10`
- Purpose: Multi-language code structure parsing (50+ languages)
- Supported extensions: `.py`, `.java`, `.ts`, `.js`, `.go`, `.rs`, `.rb`, etc.
- Implementation: `treesearch/parsers/treesitter_parser.py`
- Fallback: Regex-based parsing if tree-sitter unavailable

## Parser Dependencies (Optional)

| Format | Package | Extension | Notes |
|--------|---------|-----------|-------|
| PDF | `pageindex>=0.1` | `.pdf` | PDF structure extraction |
| DOCX | `python-docx>=0.8` | `.docx` | Word document parsing |
| HTML | `beautifulsoup4>=4.12` | `.html`, `.htm` | HTML tag structure |
| Chinese | `jieba>=0.42` | - | CJK word segmentation |
| Multi-lang code | `tree-sitter-languages>=1.10` | 50+ ext | AST-based parsing |
| gitignore | `pathspec>=0.11` | - | .gitignore pattern matching |

Install all optional parsers:
```bash
pip install pytreesearch[all]
```

---

*Integration audit: 2026-03-15*
