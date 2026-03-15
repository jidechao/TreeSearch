# Codebase Concerns

**Analysis Date:** 2026-03-15

## Tech Debt

**Large File Complexity:**
- Issue: `treesearch/fts.py` (1022 lines) and `treesearch/indexer.py` (912 lines) exceed the 800-line guideline. Both modules mix multiple responsibilities.
- Files: `treesearch/fts.py`, `treesearch/indexer.py`
- Impact: Harder to understand, test, and maintain. Changes may introduce regressions.
- Fix approach: Split `fts.py` into `fts_index.py` (core FTS5Index class) and `fts_search.py` (search utilities, tokenization). Split `indexer.py` into `indexer_md.py`, `indexer_text.py`, `indexer_code.py`, and `indexer_batch.py`.

**Async/Sync Duplication:**
- Issue: Both `treesearch/treesearch.py` and `treesearch/search.py` have nearly identical async/sync wrapper patterns with event loop detection.
- Files: `treesearch/treesearch.py` (lines 140-149, 221-228), `treesearch/search.py` (lines 408-410)
- Impact: Code duplication, potential for inconsistent behavior.
- Fix approach: Create a shared `async_utils.py` with `run_async()` helper that handles event loop detection.

**Global State via Singletons:**
- Issue: Multiple global singletons (`_global_fts`, `_default_config`) make testing harder and can cause state leakage between tests.
- Files: `treesearch/fts.py` (lines 988-1022), `treesearch/config.py` (lines 78-101)
- Impact: Tests may interfere with each other; concurrent usage is fragile.
- Fix approach: Use dependency injection where possible. At minimum, ensure all tests reset global state.

**Deprecated Model Parameter:**
- Issue: `treesitter_code_to_tree()` in `treesearch/parsers/treesitter_parser.py` still accepts an unused `model` parameter and passes it to `_update_token_counts` and `_thin_tree` which also no longer use it.
- Files: `treesearch/parsers/treesitter_parser.py` (lines 343, 402, 404)
- Impact: Dead code, confusing API.
- Fix approach: Remove `model` parameter from function signatures.

## Known Bugs

**Regex Error Handling:**
- Symptoms: Invalid regex patterns in GrepFilter are logged as warnings but return empty results without clear error feedback to caller.
- Files: `treesearch/search.py` (lines 129-132)
- Trigger: User passes malformed regex pattern to GrepFilter with `use_regex=True`.
- Workaround: None. User gets empty results with only a log warning.

**SQLite FTS5 Unavailability:**
- Symptoms: When FTS5 is unavailable, system falls back to LIKE-based search with reduced ranking quality. Warning is only logged once.
- Files: `treesearch/fts.py` (lines 50-70)
- Trigger: Python SQLite build without FTS5 extension.
- Workaround: Install `pysqlite3-binary` via the `[fts5]` extra.

**Event Loop Detection Race:**
- Symptoms: The sync wrapper pattern catches `RuntimeError` with `pass` which could mask unrelated errors.
- Files: `treesearch/treesearch.py` (lines 144-147, 225-228)
- Trigger: Calling sync `index()` or `search()` from an already-running event loop.
- Workaround: Use the async `aindex()` or `asearch()` methods in async contexts.

## Security Considerations

**File System Traversal:**
- Risk: The `resolve_paths()` function walks directories with a configurable `max_files` cap (default 10,000) but no depth limit. Symbolic link following is disabled by default.
- Files: `treesearch/pathutil.py` (lines 96-140)
- Current mitigation: `max_files` cap, `follow_symlinks=False` default, gitignore support.
- Recommendations: Consider adding a max depth parameter for deeply nested directory trees.

**Subprocess Execution:**
- Risk: The ripgrep integration uses `subprocess.run()` with user-provided patterns and file paths.
- Files: `treesearch/ripgrep.py` (lines 80-92)
- Current mitigation: Timeout (10s default), argument-based invocation (not shell), exception handling.
- Recommendations: None critical. Current implementation is safe.

**Database File Permissions:**
- Risk: SQLite database files are created with default umask permissions. No explicit permission control.
- Files: `treesearch/fts.py` (lines 206-212)
- Current mitigation: None.
- Recommendations: If storing sensitive document content, consider setting restrictive file permissions (0600) on database files.

## Performance Bottlenecks

**In-Memory Tree Operations:**
- Problem: Tree flattening and node map rebuilding happens on every `Document.__post_init__` and various search operations.
- Files: `treesearch/tree.py` (lines 34-40), `treesearch/fts.py` (lines 357-358)
- Cause: Recursive tree traversal is O(n) and called multiple times.
- Improvement path: Cache flattened nodes and tree maps with invalidation on structure mutation.

**Token Count Computation:**
- Problem: `_update_token_counts()` in indexer iterates backwards through nodes and makes O(n^2) token counting calls in worst case.
- Files: `treesearch/indexer.py` (lines 179-189)
- Cause: Each node aggregates text from all descendants.
- Improvement path: Use memoization or single-pass token counting.

**FTS5 Query Phrase Boosting:**
- Problem: Phrase boosting runs a separate FTS5 query for multi-word queries, potentially doubling query latency.
- Files: `treesearch/fts.py` (lines 486-505)
- Cause: Two-phase matching to boost exact phrase matches.
- Improvement path: Consider making phrase boosting optional via config flag.

## Fragile Areas

**Parser Registry Dynamic Loading:**
- Files: `treesearch/parsers/registry.py` (lines 213-260)
- Why fragile: Uses `importlib.import_module` with try/except blocks that silently fail. Missing optional dependencies result in no parser, not an error.
- Safe modification: When adding new parsers, ensure the ImportError handling is explicit and test with missing dependencies.
- Test coverage: Limited - no tests for missing dependency scenarios.

**Async Event Loop Detection:**
- Files: `treesearch/treesearch.py` (lines 140-149, 221-228)
- Why fragile: Relies on `asyncio.get_running_loop()` raising `RuntimeError` when no loop exists, but the `pass` statement could hide issues.
- Safe modification: Log at debug level when falling through the exception handler.
- Test coverage: No explicit tests for the event loop detection logic.

**Incremental Indexing Hash Comparison:**
- Files: `treesearch/indexer.py` (lines 725-738, 815-835)
- Why fragile: Uses `mtime_ns + size` as file fingerprint instead of content hash. Fast but can miss changes if mtime is preserved (some editors do this) or false positives on metadata-only changes.
- Safe modification: Consider adding an optional content-hash mode for critical use cases.
- Test coverage: Covered but not for edge cases like mtime preservation.

## Scaling Limits

**Single SQLite Database:**
- Current capacity: Designed for single-machine use; SQLite handles 10k-100k documents reasonably.
- Limit: Write concurrency limited by SQLite WAL mode. Not suitable for high-write multi-user scenarios.
- Scaling path: For larger deployments, consider separating FTS5 index from document storage or using PostgreSQL with full-text search.

**In-Memory Document Loading:**
- Current capacity: All documents loaded into memory when calling `load_all_documents()`.
- Limit: Memory bound. Large document collections (thousands of docs with rich structures) may cause OOM.
- Scaling path: Add streaming/lazy document loading API for large collections.

**Concurrent Indexing:**
- Current capacity: `max_concurrency` defaults to 5, controlled by semaphore.
- Limit: High concurrency may saturate I/O or cause SQLite lock contention.
- Scaling path: For bulk indexing, consider batch operations with periodic commits.

## Dependencies at Risk

**jieba (Optional, Chinese Tokenization):**
- Risk: Imported lazily but if configured with `cjk_tokenizer="jieba"` and not installed, raises `ImportError`.
- Impact: Chinese search fails.
- Migration plan: Default `cjk_tokenizer="auto"` falls back to bigram. Document the requirement clearly.

**tree-sitter-languages (Optional, Code Parsing):**
- Risk: Version compatibility issues with tree-sitter core. Currently uses deprecated Language API (suppressed via warnings.catch_warnings).
- Impact: Code parsing falls back to regex-based extraction.
- Migration plan: Monitor tree-sitter ecosystem updates. The FutureWarning suppression should be removed when API stabilizes.

**pathspec (Optional, Gitignore Support):**
- Risk: Missing dependency silently disables gitignore support with only a debug log.
- Impact: Unexpected files may be indexed when walking directories.
- Migration plan: Document this clearly or add a warning-level log.

## Missing Critical Features

**No Document Versioning:**
- Problem: When a document is re-indexed, the old version is completely replaced. No history or version tracking.
- Blocks: Ability to track document changes over time or rollback to previous versions.

**No Access Control:**
- Problem: No built-in mechanism to restrict which documents a user can search.
- Blocks: Multi-tenant scenarios where document visibility varies by user.

**No Result Highlighting:**
- Problem: Search results return full text but no indication of which portions matched the query.
- Blocks: Better UX for users to understand why a result was returned.

## Test Coverage Gaps

**Treesearch Engine Integration:**
- What's not tested: `treesearch/treesearch.py` has no dedicated test file. The main `TreeSearch` class integration is not tested.
- Files: `treesearch/treesearch.py`
- Risk: Core API regressions may go undetected.
- Priority: High

**CLI Module:**
- What's not tested: `treesearch/cli.py` has no test coverage. Argument parsing and subcommand routing are untested.
- Files: `treesearch/cli.py`
- Risk: CLI breakages not caught by CI.
- Priority: Medium

**Error Handling Paths:**
- What's not tested: Exception handling in ripgrep, parser registry, and FTS5 fallback paths.
- Files: `treesearch/ripgrep.py`, `treesearch/parsers/registry.py`, `treesearch/fts.py`
- Risk: Edge case failures may crash or produce wrong results.
- Priority: Medium

**Config Module:**
- What's not tested: Environment variable parsing and config override priority.
- Files: `treesearch/config.py`
- Risk: Configuration bugs may affect all users silently.
- Priority: Low (simple dataclass with minimal logic)

**Path Resolution Edge Cases:**
- What's not tested: Symlink handling, max_files threshold behavior, gitignore pattern edge cases.
- Files: `treesearch/pathutil.py`
- Risk: Path traversal may behave unexpectedly in corner cases.
- Priority: Medium

---

*Concerns audit: 2026-03-15*
