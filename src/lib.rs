//! diffpilot_core — Rust extension module for diffpilot (PyO3).
//!
//! Exposes performance-critical diff parsing to the Python MCP layer.

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

/// Parse a unified diff string and return a summary (counts only).
///
/// Returns a dict with keys:
/// - ``files_changed``: number of files affected
/// - ``additions``: total lines added
/// - ``deletions``: total lines removed
/// - ``hunks``: total number of diff hunks
#[pyfunction]
pub fn parse_diff<'py>(py: Python<'py>, diff_text: &str) -> PyResult<Bound<'py, PyDict>> {
    let mut files_changed: u64 = 0;
    let mut additions: u64 = 0;
    let mut deletions: u64 = 0;
    let mut hunks: u64 = 0;
    let mut in_header = false;

    for line in diff_text.lines() {
        if line.starts_with("diff ") {
            files_changed += 1;
            in_header = true;
        } else if line.starts_with("--- ") && !in_header {
            // Plain unified diff (e.g. difflib output) — no leading "diff" line.
            // Start a new file record when we are not already inside a header block.
            files_changed += 1;
            in_header = true;
        } else if line.starts_with("@@ ") {
            hunks += 1;
            in_header = false;
        } else if !in_header {
            if line.starts_with('+') && !line.starts_with("+++") {
                additions += 1;
            } else if line.starts_with('-') && !line.starts_with("---") {
                deletions += 1;
            }
        }
    }

    let result = PyDict::new(py);
    result.set_item("files_changed", files_changed)?;
    result.set_item("additions", additions)?;
    result.set_item("deletions", deletions)?;
    result.set_item("hunks", hunks)?;
    Ok(result)
}

/// Parse a unified diff string into a detailed per-file structure.
///
/// Returns a list of file dicts, each with:
/// - ``path``: affected file path
/// - ``additions``: lines added in this file
/// - ``deletions``: lines removed in this file
/// - ``hunks``: list of hunk dicts (``header``, ``old_start``, ``old_count``,
///   ``new_start``, ``new_count``, ``lines``)
///
/// Each line entry in a hunk has ``type`` (added/removed/context) and ``content``.
#[pyfunction]
pub fn parse_diff_detailed<'py>(py: Python<'py>, diff_text: &str) -> PyResult<Bound<'py, PyList>> {
    let files = PyList::empty(py);
    let mut cur_file: Option<Bound<'py, PyDict>> = None;
    let mut cur_hunk: Option<Bound<'py, PyDict>> = None;
    let mut in_header = false;

    for line in diff_text.lines() {
        if line.starts_with("diff ") {
            flush_hunk(py, &mut cur_file, &mut cur_hunk)?;
            flush_file(py, &files, &mut cur_file)?;
            cur_file = Some(make_file(py)?);
            in_header = true;
        } else if let Some(suffix) = line.strip_prefix("+++ ") {
            // Strip optional timestamp appended after a tab (e.g. from difflib).
            let path_part = suffix.split('\t').next().unwrap_or(suffix);
            if let Some(ref f) = cur_file {
                if let Some(path) = path_part.strip_prefix("b/") {
                    f.set_item("path", path)?;
                } else if path_part != "/dev/null" {
                    f.set_item("path", path_part)?;
                }
                // /dev/null → deleted file; keep path set from "--- a/..."
            }
        } else if let Some(suffix) = line.strip_prefix("--- ") {
            // Strip optional timestamp appended after a tab (e.g. from difflib).
            let path_part = suffix.split('\t').next().unwrap_or(suffix);
            // Create an implicit file record for plain unified diffs that have no
            // leading "diff " line (e.g. the output of difflib.unified_diff).
            // We do this whenever we are not already inside a header block.
            if !in_header {
                flush_hunk(py, &mut cur_file, &mut cur_hunk)?;
                flush_file(py, &files, &mut cur_file)?;
                cur_file = Some(make_file(py)?);
                in_header = true;
            }
            // Fill path from "---" only if not yet set (handles deleted files).
            if let Some(ref f) = cur_file {
                let existing: String = f.get_item("path")?.unwrap().extract()?;
                if existing.is_empty() {
                    if let Some(path) = path_part.strip_prefix("a/") {
                        f.set_item("path", path)?;
                    } else if path_part != "/dev/null" {
                        f.set_item("path", path_part)?;
                    }
                }
            }
        } else if line.starts_with("@@ ") {
            flush_hunk(py, &mut cur_file, &mut cur_hunk)?;
            in_header = false;
            cur_hunk = Some(make_hunk(py, line)?);
        } else if !in_header {
            if let (Some(ref hunk), Some(ref file)) = (&cur_hunk, &cur_file) {
                let hunk_lines: Bound<'py, PyList> =
                    hunk.get_item("lines")?.unwrap().cast_into()?;
                let entry = PyDict::new(py);
                if let Some(content) = line.strip_prefix('+') {
                    if !line.starts_with("+++") {
                        entry.set_item("type", "added")?;
                        entry.set_item("content", content)?;
                        let prev: u64 = file.get_item("additions")?.unwrap().extract()?;
                        file.set_item("additions", prev + 1)?;
                        hunk_lines.append(entry)?;
                    }
                } else if let Some(content) = line.strip_prefix('-') {
                    if !line.starts_with("---") {
                        entry.set_item("type", "removed")?;
                        entry.set_item("content", content)?;
                        let prev: u64 = file.get_item("deletions")?.unwrap().extract()?;
                        file.set_item("deletions", prev + 1)?;
                        hunk_lines.append(entry)?;
                    }
                } else if let Some(content) = line.strip_prefix(' ') {
                    entry.set_item("type", "context")?;
                    entry.set_item("content", content)?;
                    hunk_lines.append(entry)?;
                }
            }
        }
    }

    flush_hunk(py, &mut cur_file, &mut cur_hunk)?;
    flush_file(py, &files, &mut cur_file)?;
    Ok(files)
}

fn make_file(py: Python<'_>) -> PyResult<Bound<'_, PyDict>> {
    let file = PyDict::new(py);
    file.set_item("path", "")?;
    file.set_item("additions", 0u64)?;
    file.set_item("deletions", 0u64)?;
    file.set_item("hunks", PyList::empty(py))?;
    Ok(file)
}

fn make_hunk<'py>(py: Python<'py>, header: &str) -> PyResult<Bound<'py, PyDict>> {
    let hunk = PyDict::new(py);
    hunk.set_item("header", header)?;
    hunk.set_item("lines", PyList::empty(py))?;

    // Parse "@@ -old_start[,old_count] +new_start[,new_count] @@"
    let (mut old_start, mut old_count, mut new_start, mut new_count) = (0u64, 1u64, 0u64, 1u64);
    if let Some(rest) = header.strip_prefix("@@ -") {
        let parts: Vec<&str> = rest.splitn(3, ' ').collect();
        if !parts.is_empty() {
            let old: Vec<&str> = parts[0].splitn(2, ',').collect();
            old_start = old[0].parse().unwrap_or(0);
            if old.len() > 1 {
                old_count = old[1].parse().unwrap_or(1);
            }
        }
        if parts.len() > 1 {
            let new: Vec<&str> = parts[1].trim_start_matches('+').splitn(2, ',').collect();
            new_start = new[0].parse().unwrap_or(0);
            if new.len() > 1 {
                new_count = new[1].parse().unwrap_or(1);
            }
        }
    }
    hunk.set_item("old_start", old_start)?;
    hunk.set_item("old_count", old_count)?;
    hunk.set_item("new_start", new_start)?;
    hunk.set_item("new_count", new_count)?;
    Ok(hunk)
}

fn flush_hunk<'py>(
    _py: Python<'py>,
    cur_file: &mut Option<Bound<'py, PyDict>>,
    cur_hunk: &mut Option<Bound<'py, PyDict>>,
) -> PyResult<()> {
    if let (Some(file), Some(hunk)) = (cur_file.as_ref(), cur_hunk.take()) {
        let hunks: Bound<'py, PyList> = file.get_item("hunks")?.unwrap().cast_into()?;
        hunks.append(hunk)?;
    }
    Ok(())
}

fn flush_file<'py>(
    _py: Python<'py>,
    files: &Bound<'py, PyList>,
    cur_file: &mut Option<Bound<'py, PyDict>>,
) -> PyResult<()> {
    if let Some(file) = cur_file.take() {
        files.append(file)?;
    }
    Ok(())
}

/// The diffpilot._core extension module.
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse_diff, m)?)?;
    m.add_function(wrap_pyfunction!(parse_diff_detailed, m)?)?;
    Ok(())
}
