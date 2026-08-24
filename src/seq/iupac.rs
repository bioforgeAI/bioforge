// Les conversions d'index Python (isize) vers Rust (usize) et les calculs de
// bornes impliquent des casts signés délibérés, vérifiés avant usage.
#![allow(clippy::cast_possible_truncation)]
#![allow(clippy::cast_sign_loss)]
#![allow(clippy::cast_possible_wrap)]

//! Wrapper `PyO3` pour `Seq<Iupac>`, exposé à Python sous le nom `IupacSequence`.
//!
//! # Description
//! Ce module expose la séquence IUPAC (4-bit) à Python. Le cœur de calcul
//! (`Seq<Iupac>`) est indépendant de `PyO3` ; ce fichier n'est qu'une couche
//! d'adaptation FFI.

use pyo3::prelude::*;
use pyo3::types::PySlice;

use super::codec::Iupac;
use super::core::Seq;
use super::error::SeqError;

/// Séquence d'ADN avec ambiguïtés IUPAC, exposée à Python.
///
/// # Description
/// Encodage 4-bit par symbole. Préserve la totalité de l'information IUPAC
/// (15 codes d'ambiguïté). Aucune dégradation en N.
///
/// # Invariants
/// - `len(self) == len(input)`
/// - `str(self)` ne contient que des symboles de l'alphabet IUPAC en majuscules
/// - `reverse_complement` est une involution
#[pyclass(module = "bioforge.seq", name = "IupacSequence")]
pub struct PyIupacSequence {
    inner: Seq<Iupac>,
}

#[pymethods]
impl PyIupacSequence {
    /// Crée une `IupacSequence` à partir d'une chaîne de caractères.
    ///
    /// # Arguments
    /// * `seq` : chaîne composée de symboles IUPAC (A C G T N R Y S W K M B D H V),
    ///   insensible à la casse.
    ///
    /// # Returns
    /// * `PyResult<Self>` : la séquence encodée.
    ///
    /// # Errors
    /// * `ValueError` : si la chaîne contient un symbole hors alphabet IUPAC.
    #[new]
    #[pyo3(signature = (seq, /))]
    pub fn new(seq: &str) -> PyResult<Self> {
        // Iupac::Symbol = char, on passe directement les caractères.
        // La validation et la canonicalisation (majuscules) sont gérées
        // par Iupac::encode() à l'intérieur de Seq::new().
        let symbols = seq.chars();
        Ok(Self {
            inner: Seq::new(symbols)?,
        })
    }

    /// Retourne la longueur de la séquence.
    ///
    /// # Returns
    /// * `usize` : nombre de symboles.
    pub fn __len__(&self) -> usize {
        self.inner.len()
    }

    /// Retourne la séquence sous forme de chaîne de caractères ASCII.
    ///
    /// # Returns
    /// * `String` : la séquence décodée en majuscules.
    pub fn __str__(&self) -> String {
        let mut s = String::with_capacity(self.inner.len());
        for i in 0..self.inner.len() {
            if let Some(symbol) = self.inner.get(i) {
                // Iupac::Symbol = char, push direct sans conversion.
                s.push(symbol);
            }
        }
        s
    }

    /// Récupère un symbole ou une slice de la séquence.
    ///
    /// # Arguments
    /// * `index` : index entier (positif ou négatif) ou slice Python.
    ///
    /// # Returns
    /// * `PyObject` : symbole unique (`str`) ou sous-séquence (`IupacSequence`).
    ///
    /// # Errors
    /// * `IndexError` : si l'index est hors limites.
    /// * `TypeError` : si l'index n'est ni un int ni une slice.
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
            // Iupac::Symbol = char, conversion directe en String Python.
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

            let new_seq = PyIupacSequence {
                inner: Seq::new(symbols)?,
            };
            Ok(new_seq.into_py(py))
        } else {
            Err(pyo3::exceptions::PyTypeError::new_err(
                "Index must be int or slice",
            ))
        }
    }

    /// Retourne le complément inverse avec la table IUPAC complète.
    ///
    /// # Description
    /// Table de complément : A↔T C↔G N↔N R↔Y S↔S W↔W K↔M B↔V D↔H.
    /// Cette opération est une involution.
    ///
    /// # Returns
    /// * `PyResult<Self>` : la séquence complément inverse.
    ///
    /// # Errors
    /// * `ValueError` : si le codec ne supporte pas le complément (ne devrait
    ///   pas arriver pour IUPAC).
    pub fn reverse_complement(&self) -> PyResult<Self> {
        Ok(PyIupacSequence {
            inner: self.inner.reverse_complement()?,
        })
    }
}
