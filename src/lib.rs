use pyo3::prelude::*;
use pyo3::Bound;

mod seq;

/// Module principal de `BioForge` exposé à Python.
///
/// # Description
/// Point d'entrée `PyO3`. Le cœur de calcul (`seq::`) est indépendant de `PyO3` ;
/// ce module n'enregistre que les wrappers de frontière Python.
#[pymodule]
fn bioforge(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<seq::PyDnaSequence>()?;
    m.add_class::<seq::PyIupacSequence>()?;
    Ok(())
}
