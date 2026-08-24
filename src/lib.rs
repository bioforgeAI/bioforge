use pyo3::prelude::*;
use pyo3::Bound;

mod seq;

#[pymodule]
fn bioforge(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // ✅ Utilise le raccourci défini dans seq/mod.rs
    m.add_class::<seq::PyDnaSequence>()?;
    Ok(())
}
