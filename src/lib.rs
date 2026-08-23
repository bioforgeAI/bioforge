use pyo3::prelude::*;

pub mod seq;

#[pymodule]
fn bioforge(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Exposition du module seq et de ses classes
    m.add_class::<seq::PyDnaSequence>()?;
    Ok(())
}
