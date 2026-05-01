---
name: diffpilot
description: Structured diff tools returning per-file JSON hunks. Use this skill when the user wants to inspect staged changes, compare two git refs/branches, or compare two files, and needs machine-readable output (not raw text). Invoke for prompts like "what's staged?", "show changes between main and this branch", "compare these two files", or "how many lines changed?".
---

## Overview

diffpilot provides structured, machine-readable diffs optimized for AI assistants. All tools return per-file JSON with hunk-level line detail (additions, deletions, context lines). The Python MCP layer handles all tools; an optional Rust extension accelerates `summarize_diff` for large diffs.

## Available Tools

| Tool | When to use |
|------|-------------|
| `diffpilot-diff_files` | Compare two arbitrary files; returns per-hunk line-level diff with additions, deletions, and raw unified diff. Required: `file_a`, `file_b`. |
| `diffpilot-diff_refs` | Structured diff between two git commits, branches, or tags. Required: `path`, `ref_a`, `ref_b`. |
| `diffpilot-diff_staged` | Structured hunks for currently staged changes in a repository. Required: `path`. |
| `diffpilot-summarize_diff` | Parse a raw unified diff string into summary counts (files, additions, deletions, hunks). Required: `diff`. Uses Rust core when available. |

## Guidance

- **Staged review**: use `diff_staged` before committing to confirm what will be included.
- **Branch comparison**: use `diff_refs` with `ref_a="main"` and `ref_b="HEAD"` (or any refs).
- **Unstaged changes**: diffpilot does **not** cover unstaged working-tree diffs — use gitpilot's `git_diff` (with `staged=False`) for that.
- **Git workflow ops** (commit, push, branch): use gitpilot, not diffpilot.
- **Summarizing**: pipe raw diff text from any source into `summarize_diff` to get counts without parsing.
