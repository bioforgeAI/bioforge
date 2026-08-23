---
name: "BioForge Engineering Charter"
description: "Use when designing, implementing, reviewing, testing, or documenting BioForge Python, Rust, PyO3, bioinformatics, packaging, or CI changes. Enforces the BioForge v4.2 production charter, API-first design, strict typing, deterministic native execution, scientific validation, and memory safety."
applyTo: "**"
---

# BioForge Engineering Rules

The normative source is [charte_bioforge_v4.2.md](../../charte_bioforge_v4.2.md). Treat these rules as hard requirements. Do not silently weaken, bypass, or reinterpret them.

## Required workflow

- Before implementing any new API or behavior, propose the semantic interface and wait for explicit human validation.
- Python proposals must be typed stubs with Google-style docstrings containing `Args`, `Returns`, `Raises`, `Example`, and an `Invariants` section.
- Rust proposals must use `#[pyfunction]`, `#[pyo3(signature)]`, and `PyResult` where applicable.
- State one concise hypothesis, the smallest coherent edit, and one focused validation check before changing code.
- After every edit, run the narrowest relevant executable check before broadening the work.
- Never hide failing tests, diagnostics, benchmarks, or unresolved assumptions.

## Python

- Target Python 3.12+ and use modern native typing syntax.
- Code must pass `pyright` in strict mode, `ruff check`, and `ruff format`.
- Use `pydantic` only for configuration and external boundaries; never for hot-path records.
- Define each data type once. Use Rust `#[pyclass]` or `@dataclass(frozen=True, slots=True)` for hot-path data, and Pydantic models for low-volume boundary data.
- Keep one module focused on one concept and each function focused on one logical responsibility.
- Permit `# type: ignore[...]` only for an untyped external dependency or confirmed defect, with an explanatory comment.

## Rust and PyO3

- Use Edition 2021 with MSRV 1.70.0, explicitly declared in `Cargo.toml`.
- Never use `.unwrap()` or `.expect()` in production code under `src/`; propagate errors with `?`.
- Define domain errors in `thiserror` enums and map every variant explicitly and exhaustively to `PyErr`.
- Release the GIL around long or parallel native work with `py.allow_threads(...)`.
- Rayon closures must contain only native `Send + Sync` Rust data; never use PyO3 objects or acquire the GIL inside them.
- Parallel results must be deterministic whenever order is significant.
- Do not retain borrowed references to Python `PyBuffer` data beyond the call; borrow temporarily or take ownership with `to_vec()` or `Arc<[u8]>`.
- Document every public item with `///` sections for Description, Arguments, Returns, and Errors.
- Require `cargo fmt` and `cargo clippy -- -D warnings` with pedantic lints; justify localized `#[allow(...)]` attributes.

## Data, formats, and boundaries

- Polars may be used internally in Rust but must never cross the Python boundary; convert to native records first.
- For the MVP, sequence encoding is exactly two bases per byte using the specified 3-bit extraction (`i / 2`, `4 * (i % 2)`, mask `0b111`). Document `2 bases/octet` in each relevant module.
- Encapsulate Rust memory views behind safe Python classes such as `Sequence3Bit`; do not expose raw memory access.
- Keep `encoding` explicit for FASTQ (`phred33`, `phred64`, `solexa`, or `auto`); with `strict=True`, ambiguous auto-detection must raise `ValueError`.
- Keep strict and ambiguous reverse-complement operations as separate functions.
- Production `src/` must not contain concrete `NotImplementedError`. Abstract interfaces and tests are the only exceptions; any allowed use requires the mandated TODO, GitHub label, and CI detection.

## Scientific correctness and validation

- Every non-trivial algorithm needs an identifiable bibliography source and a naive, correct implementation under `reference/`.
- Never import `reference/` from `src/` or `bioforge/`; enforce this in CI.
- Preserve determinism: identical inputs and parameters produce identical results independent of parallelism unless documented otherwise.
- Ensure public APIs have tests for invariants and edge cases. Prefer property-based tests with Hypothesis.
- Complex algorithms require `pytest-regressions` and multi-level benchmarks against both Biopython and the reference implementation.
- Pin benchmark Biopython to `1.84.0`; the standard smoke test uses 1000 FASTQ reads and fails above 2x Biopython time or 1.5x its peak RSS.
- Require ASan and LSan in standard CI; use Miri only when unsafe Rust exists.

## Dependencies and reproducibility

- Use the declared core dependencies (`pyarrow`, `numpy`, `pydantic`, `pyo3`, `thiserror`, `serde`, `flate2`) and add optional dependencies only when justified.
- Use a lockfile manager such as `uv` or Poetry, with reasonable version ranges in `pyproject.toml`.
- Never use Biopython at BioForge runtime; it is permitted only as a validation oracle, reference implementation, or benchmark dependency.