"""Structured diff tool MCP server — Python layer with Rust diff parsing core."""

from __future__ import annotations

import difflib
import re
import subprocess
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

try:
    from diffpilot._core import parse_diff as _rust_parse_diff
except ImportError:
    _rust_parse_diff = None  # type: ignore[assignment]  # Rust extension not yet built

mcp: FastMCP = FastMCP(
    name="diffpilot",
    instructions=(
        "diffpilot produces structured, machine-readable diffs optimized for AI assistants. "
        "The diff_* tools (diff_files, diff_refs, diff_staged) return per-file JSON with "
        "hunk-level line detail (additions, deletions, context). "
        "Use `diff_files` to compare two arbitrary files and get structured hunks. "
        "Use `diff_refs` to get a structured diff between two git commits, branches, or tags. "
        "Use `diff_staged` to get structured hunks for currently staged changes in a repository. "
        "Use `summarize_diff` to get aggregate counts only (files changed, additions, deletions, "
        "hunks) from a raw diff string — it does not return per-file hunk detail. "
        "Note: diffpilot does not cover unstaged working-tree diffs — use gitpilot's `git_diff` "
        "(with staged=False) for that. For git workflow operations such as commit, push, or branch "
        "management, use gitpilot."
    ),
)


# ── Helpers ───────────────────────────────────────────────────────────────────

_DEFAULT_SUBPROCESS_TIMEOUT_SECONDS = 30


def _resolve(path: str) -> str:
    return str(Path(path).expanduser().resolve())


def _run(args: list[str], cwd: str, timeout: float = _DEFAULT_SUBPROCESS_TIMEOUT_SECONDS) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 124, "", f"Command timed out after {timeout} seconds: {' '.join(args)}"
    return result.returncode, result.stdout, result.stderr


def _err(msg: str) -> dict[str, Any]:
    return {"error": msg}


_HUNK_HEADER = re.compile(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)")


def _parse_unified_diff(diff_text: str) -> list[dict[str, Any]]:
    """Parse unified diff text into per-file structured records."""
    files: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_hunk: dict[str, Any] | None = None

    def _flush_hunk() -> None:
        if current is not None and current_hunk is not None:
            current["hunks"].append(current_hunk)

    def _flush_file() -> None:
        _flush_hunk()
        if current is not None:
            files.append(current)

    for line in diff_text.splitlines():
        if line.startswith("diff "):
            _flush_file()
            current = {"path": "", "additions": 0, "deletions": 0, "hunks": []}
            current_hunk = None
        elif line.startswith("--- "):
            # Start a new implicit file when there's no leading "diff" line (e.g. difflib output).
            if current is None:
                current = {"path": "", "additions": 0, "deletions": 0, "hunks": []}
                current_hunk = None
            suffix = line[4:].split("\t")[0]  # strip optional timestamp
            if not current["path"]:
                if suffix.startswith("a/"):
                    current["path"] = suffix[2:]
                elif suffix != "/dev/null":
                    current["path"] = suffix
        elif line.startswith("+++ ") and current is not None:
            suffix = line[4:].split("\t")[0]
            if suffix.startswith("b/"):
                current["path"] = suffix[2:]
            elif suffix != "/dev/null":
                current["path"] = suffix
        elif line.startswith("@@ ") and current is not None:
            _flush_hunk()
            m = _HUNK_HEADER.match(line)
            if m:
                current_hunk = {
                    "header": line,
                    "old_start": int(m.group(1)),
                    "old_count": int(m.group(2)) if m.group(2) is not None else 1,
                    "new_start": int(m.group(3)),
                    "new_count": int(m.group(4)) if m.group(4) is not None else 1,
                    "lines": [],
                }
        elif current_hunk is not None and current is not None:
            if line.startswith("+") and not line.startswith("+++"):
                current_hunk["lines"].append({"type": "added", "content": line[1:]})
                current["additions"] += 1
            elif line.startswith("-") and not line.startswith("---"):
                current_hunk["lines"].append({"type": "removed", "content": line[1:]})
                current["deletions"] += 1
            elif line.startswith(" "):
                current_hunk["lines"].append({"type": "context", "content": line[1:]})

    _flush_file()
    return files


def _summarize_files(files: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "files_changed": len(files),
        "additions": sum(f["additions"] for f in files),
        "deletions": sum(f["deletions"] for f in files),
        "hunks": sum(len(f["hunks"]) for f in files),
    }


# ── diff_files ────────────────────────────────────────────────────────────────


@mcp.tool
def diff_files(path_a: str, path_b: str, context_lines: int = 3) -> dict[str, object]:
    """Compare two files and return a structured diff.

    Args:
        path_a: Path to the first (old/left) file.
        path_b: Path to the second (new/right) file.
        context_lines: Number of context lines to include around each hunk.
    """
    pa = Path(path_a).expanduser().resolve()
    pb = Path(path_b).expanduser().resolve()

    try:
        lines_a = pa.read_text(errors="replace").splitlines(keepends=True)
        lines_b = pb.read_text(errors="replace").splitlines(keepends=True)
    except OSError as exc:
        return _err(str(exc))

    raw_diff = "".join(
        difflib.unified_diff(
            lines_a,
            lines_b,
            fromfile=str(pa),
            tofile=str(pb),
            n=context_lines,
        )
    )

    files = _parse_unified_diff(raw_diff)
    all_hunks = [h for f in files for h in f["hunks"]]
    total_additions = sum(f["additions"] for f in files)
    total_deletions = sum(f["deletions"] for f in files)

    return {
        "hunks": all_hunks,
        "additions": total_additions,
        "deletions": total_deletions,
        "raw_diff": raw_diff,
    }


# ── diff_refs ─────────────────────────────────────────────────────────────────


@mcp.tool
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
        file_filter: Optional path or glob to restrict which files are diffed.
    """
    cwd = _resolve(path)
    args = ["git", "diff", ref_a, ref_b]
    if file_filter:
        args += ["--", file_filter]

    rc, stdout, stderr = _run(args, cwd)
    if rc != 0:
        return _err(stderr.strip() or "git diff failed")

    files = _parse_unified_diff(stdout)
    total_additions = sum(f["additions"] for f in files)
    total_deletions = sum(f["deletions"] for f in files)

    return {
        "files": files,
        "total_additions": total_additions,
        "total_deletions": total_deletions,
    }


# ── diff_staged ───────────────────────────────────────────────────────────────


@mcp.tool
def diff_staged(path: str = ".", context_lines: int = 3) -> dict[str, object]:
    """Return structured diff of currently staged changes.

    Args:
        path: Path to the repository root.
        context_lines: Number of context lines to include around each hunk.
    """
    cwd = _resolve(path)
    rc, stdout, stderr = _run(["git", "diff", "--staged", f"--unified={context_lines}"], cwd)
    if rc != 0:
        return _err(stderr.strip() or "git diff --staged failed")

    files = _parse_unified_diff(stdout)
    total_additions = sum(f["additions"] for f in files)
    total_deletions = sum(f["deletions"] for f in files)

    return {
        "files": files,
        "total_additions": total_additions,
        "total_deletions": total_deletions,
    }


# ── summarize_diff ────────────────────────────────────────────────────────────


@mcp.tool
def summarize_diff(diff_text: str) -> dict[str, object]:
    """Summarize a unified diff string as structured metadata (counts only).

    Uses the Rust core when available for maximum performance on large diffs.

    Args:
        diff_text: Raw unified diff text to parse.
    """
    if _rust_parse_diff is not None:
        return _rust_parse_diff(diff_text)  # type: ignore[no-any-return]
    return _summarize_files(_parse_unified_diff(diff_text))


def run() -> None:
    """Run the MCP server."""
    mcp.run()
