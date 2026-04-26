"""Structured diff tool MCP server — Python layer with Rust diff parsing core."""
from __future__ import annotations

from fastmcp import FastMCP

try:
    from diffpilot._core import parse_diff
except ImportError:
    parse_diff = None  # type: ignore[assignment]  # Rust extension not yet built

mcp: FastMCP = FastMCP(
    name="diffpilot",
    instructions=(
        "diffpilot produces structured diffs between files, git refs, or the staging area. "
        "Use `diff_files` to compare two files and get a structured result. "
        "Use `diff_refs` to diff between two git commits, branches, or tags. "
        "Use `diff_staged` to inspect currently staged changes in a repository. "
        "Use `summarize_diff` to get a high-level natural language summary of a diff."
    ),
)


@mcp.tool()
def diff_files(path_a: str, path_b: str, context_lines: int = 3) -> dict[str, object]:
    """Compare two files and return a structured diff.

    Args:
        path_a: Path to the first (old) file.
        path_b: Path to the second (new) file.
        context_lines: Number of context lines to include around each hunk.

    Returns:
        A dict with keys ``hunks``, ``additions``, ``deletions``, and ``raw_diff``.
    """
    raise NotImplementedError


@mcp.tool()
def diff_refs(
    ref_a: str,
    ref_b: str,
    path: str = ".",
    file_filter: str = "",
) -> dict[str, object]:
    """Diff between two git commits, branches, or tags.

    Args:
        ref_a: The base git ref (older side of the diff).
        ref_b: The target git ref (newer side of the diff).
        path: Path to the repository root.
        file_filter: Optional glob pattern to restrict which files are diffed.

    Returns:
        A dict with keys ``files``, ``total_additions``, ``total_deletions``, and ``hunks``.
    """
    raise NotImplementedError


@mcp.tool()
def diff_staged(path: str = ".", context_lines: int = 3) -> dict[str, object]:
    """Return structured diff of currently staged changes.

    Args:
        path: Path to the repository root.
        context_lines: Number of context lines to include around each hunk.

    Returns:
        A dict with keys ``files``, ``total_additions``, ``total_deletions``, and ``hunks``.
    """
    raise NotImplementedError


@mcp.tool()
def summarize_diff(diff_text: str) -> dict[str, object]:
    """Summarize a unified diff as structured metadata.

    Args:
        diff_text: Raw unified diff text to parse.

    Returns:
        A dict with keys ``files_changed``, ``additions``, ``deletions``, and ``hunks``.
    """
    if parse_diff is not None:
        return parse_diff(diff_text)  # type: ignore[no-any-return]
    raise NotImplementedError


def run() -> None:
    """Run the MCP server."""
    mcp.run()
