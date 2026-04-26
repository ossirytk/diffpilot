# AGENTS.md — Project Rules for AI Assistants (Python + Rust/PyO3)

diffpilot is a structured diff tool MCP server. The Python layer handles the MCP protocol via FastMCP, while a Rust extension module (built with maturin/PyO3) provides high-performance diff parsing. The Rust core is optional at development time — the server falls back gracefully if the extension is not yet built.

---

## Tech Stack

- **Python layer:** Python 3.12+, FastMCP, maturin build backend
- **Rust core:** PyO3 0.23, cdylib extension (`diffpilot._core`)
- **Build / env:** uv + maturin
- **Linter / formatter:** ruff (Python), cargo clippy + cargo fmt (Rust)
- **Tests:** pytest + pytest-cov

---

## Development Commands

```sh
# Install Python dependencies
uv sync

# Build Rust extension (debug, editable)
uv run maturin develop

# Build Rust extension (release)
uv run maturin develop --release

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

# Rust format
cargo fmt
```

---

## Project Structure

```
diffpilot/
├── python/
│   └── diffpilot/
│       ├── __init__.py      # Package marker
│       ├── __main__.py      # python -m diffpilot entry point
│       └── server.py        # FastMCP server + tool definitions
├── src/
│   └── lib.rs               # PyO3 extension — parse_diff and related functions
├── Cargo.toml               # Rust package metadata (cdylib)
├── pyproject.toml           # Python project metadata (maturin backend)
├── .python-version          # Pinned Python version (3.12)
├── AGENTS.md                # This file
└── README.md                # User-facing documentation
```

---

## Key Conventions

- Python source lives under `python/` (not `src/`), as required by `[tool.maturin] python-source = "python"`.
- The Rust extension module is `diffpilot._core`; import it with a graceful `try/except ImportError`.
- ruff is the sole Python formatter/linter; cargo fmt + clippy for Rust.
- `pyproject.toml` is the single source of truth for ruff and maturin settings.
- Run `uv run ruff check --fix . && uv run ruff format .` and `cargo clippy -- -D warnings` before every commit.
