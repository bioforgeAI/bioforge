// Les conversions d'index Python (isize) vers Rust (usize) et les calculs de
// bornes impliquent des casts signés délibérés, vérifiés avant usage.
#![allow(clippy::cast_possible_truncation)]
#![allow(clippy::cast_sign_loss)]
#![allow(clippy::cast_possible_wrap)]

//! Wrapper `PyO3` pour `Seq<Amino>`, exposé à Python sous le nom `AminoSequence`.
//!
//! # Description
//! Ce module expose la séquence protéique (6-bit) à Python. Le cœur de calcul
//! (`Seq<Amino>`) est indépendant de `PyO3` ; ce fichier n'est qu'une couche
//! d'adaptation FFI.
//!
//! # Différence fondamentale avec DnaSequence/IupacSequence
//! `AminoSequence` **n'a pas de méthode `reverse_complement()`**, car les
//! protéines sont directionnelles (N-terminal → C-terminal) mais dépourvues
//! de brin complémentaire. Ne pas exposer cette méthode protège l'intégrité
//! du domaine.

use pyo3::prelude::*;
use pyo3::types::PySlice;

use super::codec::Amino;
use super::core::Seq;
use super::error::SeqError;

/// Séquence protéique exposée à Python.
///
/// # Description
/// Encodage 6-bit par acide aminé. Supporte 27 symboles (20 AA standards +
/// 3 codes ambigus + 3 codes spéciaux + stop codon).
///
/// # Invariants
/// - `len(self) == len(input)`
/// - `str(self)` ne contient que des symboles de l'alphabet protéique en majuscules
/// - **Pas de `reverse_complement()`** (protéines n'ont pas de brin complémentaire)
#[pyclass(module = "bioforge.seq", name = "AminoSequence")]
pub struct PyAminoSequence {
    inner: Seq<Amino>,
}

#[pymethods]
impl PyAminoSequence {
    /// Crée une `AminoSequence` à partir d'une chaîne de caractères.
    ///
    /// # Arguments
    /// * `seq` : chaîne composée de symboles protéiques
    ///   (A C D E F G H I K L M N P Q R S T V W Y B J Z O U X *),
    ///   insensible à la casse (sauf pour *).
    ///
    /// # Returns
    /// * `PyResult<Self>` : la séquence encodée.
    ///
    /// # Errors
    /// * `ValueError` : si la chaîne contient un symbole hors alphabet protéique.
    #[new]
    #[pyo3(signature = (seq, /))]
    pub fn new(seq: &str) -> PyResult<Self> {
        // Amino::Symbol = char, on passe directement les caractères.
        // La validation et la canonicalisation (majuscules) sont gérées
        // par Amino::encode() à l'intérieur de Seq::new().
        // Note : '*' est insensible à to_ascii_uppercase() (retourne '*').
        let symbols = seq.chars();
        Ok(Self {
            inner: Seq::new(symbols)?,
        })
    }

    /// Retourne la longueur de la séquence.
    ///
    /// # Returns
    /// * `usize` : nombre d'acides aminés.
    #[must_use]
    pub fn __len__(&self) -> usize {
        self.inner.len()
    }

    /// Retourne la séquence sous forme de chaîne de caractères.
    ///
    /// # Returns
    /// * `String` : la séquence décodée en majuscules.
    #[must_use]
    pub fn __str__(&self) -> String {
        let mut s = String::with_capacity(self.inner.len());
        for i in 0..self.inner.len() {
            if let Some(symbol) = self.inner.get(i) {
                // Amino::Symbol = char, push direct sans conversion.
                s.push(symbol);
            }
        }
        s
    }

    /// Récupère un acide aminé ou une slice de la séquence.
    ///
    /// # Arguments
    /// * `index` : index entier (positif ou négatif) ou slice Python.
    ///
    /// # Returns
    /// * `PyObject` : acide aminé unique (`str`) ou sous-séquence (`AminoSequence`).
    ///
    /// # Errors
    /// * `IndexError` : si l'index est hors limites.
    /// * `TypeError` : si l'index n'est ni un int ni une slice.
    pub fn __getitem__(&self, py: Python, index: &Bound<'_, PyAny>) -> PyResult<PyObject> {
        if let Ok(idx) = index.extract::<isize>() {
            // Cast usize -> isize sûr : les séquences protéiques ne dépassent
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
            // Amino::Symbol = char, conversion directe en String Python.
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

            let new_seq = PyAminoSequence {
                inner: Seq::new(symbols)?,
            };
            Ok(new_seq.into_py(py))
        } else {
            Err(pyo3::exceptions::PyTypeError::new_err(
                "Index must be int or slice",
            ))
        }
    }
}
