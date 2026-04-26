# diffpilot

Structured diff tool MCP server — Python MCP layer with Rust diff parsing core.

> **Status:** 🚧 Work in progress

diffpilot provides structured, machine-readable diffs between files, git refs, and the staging area. The Python layer handles the MCP protocol; a Rust extension module (built with maturin/PyO3) delivers high-performance diff parsing. The server degrades gracefully if the Rust extension has not yet been compiled.

---

## Tools

| Tool | Description |
|------|-------------|
| `diff_files` | Compare two files and return a structured diff with hunk metadata |
| `diff_refs` | Diff between two git commits, branches, or tags |
| `diff_staged` | Inspect currently staged changes in a repository |
| `summarize_diff` | Parse a unified diff string into structured metadata (additions, deletions, hunks) |

---

## Installation

> Coming soon.

---

## Development

```sh
# Install Python dependencies
uv sync

# Build Rust extension (editable)
uv run maturin develop

# Run the server
uv run diffpilot

# Python lint
uv run ruff check .

# Python format
uv run ruff format .

# Run tests
uv run pytest

# Rust build
cargo build

# Rust lint
cargo clippy -- -D warnings
```
