# diffpilot

Structured diff tool MCP server — Python MCP layer with Rust diff parsing core.

diffpilot provides structured, machine-readable diffs between files, git refs, and the staging area, optimized for AI assistants. The Python layer handles the MCP protocol and implements all tools; an optional Rust extension module (built with maturin/PyO3) accelerates large-diff parsing for `summarize_diff`.

---

## Tools

| Tool | Description |
|------|-------------|
| `diff_files` | Compare two files; returns per-hunk line-level diff with additions, deletions, and raw unified diff |
| `diff_refs` | Diff between two git commits, branches, or tags; returns per-file structured hunks |
| `diff_staged` | Inspect currently staged changes; returns per-file structured hunks |
| `summarize_diff` | Parse a raw unified diff string into summary counts (files, additions, deletions, hunks). Uses the Rust core when available |

All tools return structured dicts — no raw text that needs post-processing.

---

## Installation

> Coming soon.

---

## Development

```sh
# Install Python dependencies
uv sync

# Build Rust extension (editable, optional — server works without it)
uv run maturin develop

# Run the server
uv run diffpilot

# Python lint + format (pre-commit)
uv run ruff check --fix . && uv run ruff format .

# Run tests
uv run pytest

# Rust build
cargo build

# Rust lint
cargo clippy -- -D warnings

# Rust format
cargo fmt
```
