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

All tools return structured dicts; some responses may also include raw unified diff text when useful.

---

## Installation

**Requires:** Python 3.12+, [uv](https://docs.astral.sh/uv/)

> **Optional Rust extension:** The `summarize_diff` tool uses a Rust core for faster large-diff parsing. The server works without it, but `summarize_diff` will be slower.

### Option A — Install as a uv tool (recommended)

```sh
uv tool install git+https://github.com/ossirytk/diffpilot
```

The Rust extension is compiled automatically during install (requires a [Rust toolchain](https://rustup.rs/)).

Verify:

```sh
diffpilot --help
```

To update later:

```sh
uv tool upgrade diffpilot
```

### Option B — Clone and run from source

```sh
git clone https://github.com/ossirytk/diffpilot
cd diffpilot
uv sync
```

To build the optional Rust extension:

```sh
uv run maturin develop
```

---

## Configuration

### GitHub Copilot CLI

Add to `~/.copilot/mcp-config.json`:

**Option A (installed tool):**

```json
{
  "mcpServers": {
    "diffpilot": {
      "type": "stdio",
      "command": "diffpilot"
    }
  }
}
```

**Option B (local clone):**

```json
{
  "mcpServers": {
    "diffpilot": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "/path/to/diffpilot", "diffpilot"]
    }
  }
}
```

### VS Code Copilot

Add to your user-level MCP config file:
- **Linux:** `~/.config/Code/User/mcp.json`
- **macOS:** `~/Library/Application Support/Code/User/mcp.json`
- **Windows:** `%APPDATA%\Code\User\mcp.json`

**Option A:**

```json
{
  "servers": {
    "diffpilot": {
      "type": "stdio",
      "command": "diffpilot"
    }
  }
}
```

**Option B:**

```json
{
  "servers": {
    "diffpilot": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "/path/to/diffpilot", "diffpilot"]
    }
  }
}
```

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
