//! diffpilot_core — Rust extension module for diffpilot (PyO3).
//!
//! Exposes performance-critical diff parsing to the Python MCP layer.

use pyo3::prelude::*;
use pyo3::types::PyDict;

/// Parse a unified diff string and return structured metadata.
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

    for line in diff_text.lines() {
        if line.starts_with("--- ") {
            files_changed += 1;
        } else if line.starts_with("@@ ") {
            hunks += 1;
        } else if line.starts_with('+') && !line.starts_with("+++") {
            additions += 1;
        } else if line.starts_with('-') && !line.starts_with("---") {
            deletions += 1;
        }
    }

    let result = PyDict::new(py);
    result.set_item("files_changed", files_changed)?;
    result.set_item("additions", additions)?;
    result.set_item("deletions", deletions)?;
    result.set_item("hunks", hunks)?;
    Ok(result)
}

/// The diffpilot._core extension module.
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse_diff, m)?)?;
    Ok(())
}
