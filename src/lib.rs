use pyo3::prelude::*;
use pyo3::Bound;

mod core;

#[pymodule]
fn bioforge(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<core::sequence::Sequence3Bit>()?;
    Ok(())
}
