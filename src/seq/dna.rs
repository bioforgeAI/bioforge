use super::codec::{Dna, DnaBase};
use super::core::Seq;
use super::error::SeqError;
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PySlice};

#[pyclass(module = "bioforge.seq", name = "DnaSequence")]
pub struct PyDnaSequence {
    inner: Seq<Dna>,
}

#[pymethods]
impl PyDnaSequence {
    #[new]
    #[pyo3(signature = (seq, /))]
    pub fn new(seq: &str) -> PyResult<Self> {
        let symbols: Result<Vec<_>, _> = seq
            .chars()
            .enumerate()
            .map(|(i, c)| {
                DnaBase::from_char(c).ok_or(SeqError::InvalidSymbol { pos: i, symbol: c })
            })
            .collect();

        Ok(Self {
            inner: Seq::new(symbols?)?,
        })
    }

    pub fn __len__(&self) -> usize {
        self.inner.len()
    }

    /// Retourne la séquence sous forme de chaîne de caractères ASCII.
    pub fn __str__(&self) -> String {
        let mut bytes = Vec::with_capacity(self.inner.len());
        for i in 0..self.inner.len() {
            if let Some(symbol) = self.inner.get(i) {
                bytes.push(symbol.to_ascii_u8());
            }
        }
        // Safe car nous ne poussons que des octets ASCII valides (A, C, G, T)
        unsafe { String::from_utf8_unchecked(bytes) }
    }

    /// Récupère un symbole ou une slice de la séquence.
    ///
    /// # Errors
    /// * `PyIndexError`: Si l'index est hors limites.
    /// * `PyTypeError`: Si l'index n'est pas un int ou une slice.
    pub fn __getitem__(&self, py: Python, index: &Bound<'_, PyAny>) -> PyResult<PyObject> {
        if let Ok(idx) = index.extract::<isize>() {
            let len = self.inner.len() as isize;
            let mut actual_idx = idx;
            if actual_idx < 0 {
                actual_idx += len;
            }
            if actual_idx < 0 || actual_idx >= len {
                return Err(SeqError::SliceOutOfBounds {
                    index: idx,
                    len: self.inner.len(),
                }
                .into());
            }

            // ✅ Correction : ok_or au lieu de ok_or_else
            let symbol = self
                .inner
                .get(actual_idx as usize)
                .ok_or(SeqError::InvalidSymbol {
                    pos: actual_idx as usize,
                    symbol: '?',
                })?;
            Ok(symbol.to_string().into_py(py))
        } else if let Ok(slice) = index.downcast::<PySlice>() {
            let indices = slice
                .indices(self.inner.len() as i64)
                .map_err(|_| pyo3::exceptions::PyTypeError::new_err("Invalid slice indices"))?;

            if indices.step != 1 {
                return Err(pyo3::exceptions::PyTypeError::new_err(
                    "Slice step must be 1",
                ));
            }

            let start = indices.start as usize;
            let stop = indices.stop as usize;

            let mut symbols = Vec::with_capacity(stop.saturating_sub(start));
            for i in start..stop {
                // ✅ Correction : ok_or au lieu de ok_or_else
                let sym = self.inner.get(i).ok_or(SeqError::InvalidSymbol {
                    pos: i,
                    symbol: '?',
                })?;
                symbols.push(sym);
            }

            let new_seq = PyDnaSequence {
                inner: Seq::new(symbols)?,
            };
            Ok(new_seq.into_py(py))
        } else {
            Err(pyo3::exceptions::PyTypeError::new_err(
                "Index must be int or slice",
            ))
        }
    }

    /// Retourne le complément inverse de la séquence.
    pub fn reverse_complement(&self) -> PyResult<Self> {
        Ok(PyDnaSequence {
            inner: self.inner.reverse_complement()?,
        })
    }

    /// Retourne une copie du buffer interne encodé sous forme d'objet `bytes` Python.
    #[getter]
    pub fn to_bytes(&self, py: Python) -> PyObject {
        // PyBytes::new_bound crée un objet bytes Python à partir du Vec<u8>
        PyBytes::new_bound(py, &self.inner.to_bytes()).into()
    }
}
