from __future__ import annotations

from typing import TYPE_CHECKING

from diffpilot import server

if TYPE_CHECKING:
    from pathlib import Path


def test_summarize_diff_python_fallback() -> None:
    diff_text = (
        "diff --git a/demo.txt b/demo.txt\n"
        "--- a/demo.txt\n"
        "+++ b/demo.txt\n"
        "@@ -1,2 +1,2 @@\n"
        " unchanged\n"
        "-old line\n"
        "+new line\n"
    )
    summary = server.summarize_diff(diff_text)
    assert summary == {"files_changed": 1, "additions": 1, "deletions": 1, "hunks": 1}


def test_diff_files_returns_structured_hunks(tmp_path: Path) -> None:
    path_a = tmp_path / "a.txt"
    path_b = tmp_path / "b.txt"
    path_a.write_text("same\nold\n", encoding="utf-8")
    path_b.write_text("same\nnew\n", encoding="utf-8")

    result = server.diff_files(str(path_a), str(path_b), context_lines=1)

    assert "error" not in result
    assert result["additions"] == 1
    assert result["deletions"] == 1
    assert result["hunks"]
    assert "@@" in result["raw_diff"]


def test_diff_files_returns_error_on_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.txt"
    existing = tmp_path / "exists.txt"
    existing.write_text("hello\n", encoding="utf-8")

    result = server.diff_files(str(missing), str(existing))
    assert "error" in result


def test_diff_refs_success_and_error_paths(monkeypatch) -> None:
    diff_text = "diff --git a/file.txt b/file.txt\n--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-a\n+b\n"

    monkeypatch.setattr(server, "_run", lambda _args, _cwd: (0, diff_text, ""))
    success = server.diff_refs("main", "feature", path=".")
    assert "error" not in success
    assert success["total_additions"] == 1
    assert success["total_deletions"] == 1
    assert len(success["files"]) == 1

    monkeypatch.setattr(server, "_run", lambda _args, _cwd: (1, "", "boom"))
    failure = server.diff_refs("main", "feature", path=".")
    assert failure == {"error": "boom"}


def test_diff_staged_success_and_error_paths(monkeypatch) -> None:
    diff_text = "diff --git a/file.txt b/file.txt\n--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-before\n+after\n"

    monkeypatch.setattr(server, "_run", lambda _args, _cwd: (0, diff_text, ""))
    success = server.diff_staged(path=".", context_lines=7)
    assert "error" not in success
    assert success["total_additions"] == 1
    assert success["total_deletions"] == 1
    assert len(success["files"]) == 1

    monkeypatch.setattr(server, "_run", lambda _args, _cwd: (1, "", "staged failed"))
    failure = server.diff_staged(path=".")
    assert failure == {"error": "staged failed"}


def test_summarize_diff_python_and_rust_paths(monkeypatch) -> None:
    diff_text = "diff --git a/file.txt b/file.txt\n--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-x\n+y\n"

    monkeypatch.setattr(server, "_rust_parse_diff", None)
    python_summary = server.summarize_diff(diff_text)
    assert python_summary == {"files_changed": 1, "additions": 1, "deletions": 1, "hunks": 1}

    monkeypatch.setattr(server, "_rust_parse_diff", lambda raw: {"files_changed": 99, "raw_len": len(raw)})
    rust_summary = server.summarize_diff(diff_text)
    assert rust_summary == {"files_changed": 99, "raw_len": len(diff_text)}


def test_run_invokes_mcp_run(monkeypatch) -> None:
    called = {"ran": False}

    def fake_run() -> None:
        called["ran"] = True

    monkeypatch.setattr(server.mcp, "run", fake_run)
    server.run()
    assert called["ran"] is True
