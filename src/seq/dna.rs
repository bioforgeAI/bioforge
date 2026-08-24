// Les conversions d'index Python (isize) vers Rust (usize) et les calculs de
// bornes impliquent des casts signés délibérés, vérifiés avant usage.
#![allow(clippy::cast_possible_truncation)]
#![allow(clippy::cast_sign_loss)]
#![allow(clippy::cast_possible_wrap)]

use pyo3::prelude::*;
use pyo3::types::PySlice;

use super::codec::{Dna, DnaBase};
use super::core::Seq;
use super::error::SeqError;
use super::kmer::PyDnaKmerIterator;

/// Wrapper `PyO3` pour `Seq<Dna>`, exposé à Python sous le nom `DnaSequence`.
#[pyclass(module = "bioforge.seq", name = "DnaSequence")]
pub struct PyDnaSequence {
    inner: Seq<Dna>,
}

#[pymethods]
impl PyDnaSequence {
    /// Crée une `DnaSequence` à partir d'une chaîne de caractères.
    ///
    /// # Arguments
    /// * `seq` : chaîne composée de A, C, G, T (insensible à la casse).
    ///
    /// # Returns
    /// * `PyResult<Self>` : la séquence encodée.
    ///
    /// # Errors
    /// * `ValueError` : si la chaîne contient un symbole non reconnu.
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

    /// Retourne la longueur de la séquence.
    pub fn __len__(&self) -> usize {
        self.inner.len()
    }

    /// Retourne la séquence sous forme de chaîne de caractères ASCII.
    pub fn __str__(&self) -> String {
        let mut s = String::with_capacity(self.inner.len());
        for i in 0..self.inner.len() {
            if let Some(symbol) = self.inner.get(i) {
                s.push(symbol.to_char());
            }
        }
        s
    }

    /// Récupère un symbole ou une slice de la séquence.
    ///
    /// # Errors
    /// * `PyIndexError` : si l'index est hors limites.
    /// * `PyTypeError` : si l'index n'est pas un int ou une slice.
    pub fn __getitem__(&self, py: Python, index: &Bound<'_, PyAny>) -> PyResult<PyObject> {
        if let Ok(idx) = index.extract::<isize>() {
            // Cast usize -> isize sûr : les séquences bioinformatiques ne dépassent
            // jamais isize::MAX (limite mémoire réaliste).
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

            // Cast isize -> usize sûr : on vient de vérifier actual_idx >= 0.
            let symbol = self
                .inner
                .get(actual_idx as usize)
                .ok_or(SeqError::InvalidSymbol {
                    pos: actual_idx as usize,
                    symbol: '?',
                })?;
            Ok(symbol.to_string().into_py(py))
        } else if let Ok(slice) = index.downcast::<PySlice>() {
            // Cast usize -> i64 sûr : PySlice.indices attend un i64 pour la longueur.
            let indices = slice
                .indices(self.inner.len() as i64)
                .map_err(|_| pyo3::exceptions::PyTypeError::new_err("Invalid slice indices"))?;

            if indices.step != 1 {
                return Err(pyo3::exceptions::PyTypeError::new_err(
                    "Slice step must be 1",
                ));
            }

            // Casts isize -> usize sûrs : PySlice.indices garantit start/stop >= 0
            // quand la séquence a une longueur positive.
            let start = indices.start as usize;
            let stop = indices.stop as usize;

            let mut symbols = Vec::with_capacity(stop.saturating_sub(start));
            for i in start..stop {
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

    /// Itère sur tous les k-mers de longueur k, de gauche à droite.
    ///
    /// # Arguments
    /// * `k` : longueur des k-mers (1 <= k <= len(self)).
    ///
    /// # Returns
    /// * `PyResult<PyDnaKmerIterator>` : itérateur paresseux sur les k-mers.
    ///
    /// # Errors
    /// * `ValueError` : si k == 0 ou k > len(self).
    #[pyo3(signature = (k, /))]
    pub fn kmers(&self, k: usize) -> PyResult<PyDnaKmerIterator> {
        if k == 0 || k > self.inner.len() {
            return Err(SeqError::InvalidKmerLength { got: k }.into());
        }
        Ok(PyDnaKmerIterator::new(self.inner.clone(), k))
    }
}
