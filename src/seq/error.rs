use pyo3::{
    exceptions::{PyIndexError, PyOverflowError, PyValueError},
    PyErr,
};
use thiserror::Error;

/// Erreurs liées à la manipulation des séquences biologiques.
///
/// # Description
/// Cette enum centralise toutes les erreurs du module `seq`. Chaque variante
/// est mappée de manière exhaustive vers une exception Python via
/// `From<SeqError> for PyErr`, conformément à la charte v4.4 §3.
///
/// # Variantes
/// - `InvalidSymbol` : symbole non reconnu par le codec à une position donnée.
/// - `InvalidKmerLength` : longueur de k-mer invalide (doit être > 0).
/// - `SliceOutOfBounds` : index hors des limites de la séquence.
/// - `KmerTooLarge` : k-mer dépassant la capacité du stockage interne (`u128`).
/// - `NoComplementForCodec` : le codec ne supporte pas le complément (ex. protéines).
/// - `UnsupportedBitsPerSymbol` : le codec déclare un nombre de bits/symbole non supporté.
/// - `SequenceTooLong` : la séquence dépasse la capacité de représentation interne.
#[derive(Error, Debug)]
pub enum SeqError {
    #[error("Invalid symbol '{symbol}' at position {pos} for this codec")]
    InvalidSymbol { pos: usize, symbol: char },

    #[error("K-mer length {got} is invalid (must be > 0)")]
    InvalidKmerLength { got: usize },

    #[error("Slice index {index} out of bounds for sequence of length {len}")]
    SliceOutOfBounds { index: isize, len: usize },

    #[error("K-mer length {got} exceeds storage capacity (max {max} for {bits}-bit symbols)")]
    KmerTooLarge { got: usize, max: usize, bits: usize },

    #[error("Complement operation is not supported for codec {codec}")]
    NoComplementForCodec { codec: &'static str },

    #[error("Unsupported bits per symbol: {bits} (must be between 1 and 8)")]
    UnsupportedBitsPerSymbol { bits: usize },

    #[error("Sequence too large to encode: {len} symbols overflow the internal representation")]
    SequenceTooLong { len: usize },
}

/// Mapping exhaustif des erreurs Rust vers les exceptions Python.
///
/// # Description
/// Convertit chaque variante de `SeqError` vers l'exception Python la plus
/// sémantique. Le `match` est exhaustif : `clippy` échouera si une variante
/// est oubliée.
///
/// # Arguments
/// * `err` : l'erreur Rust à convertir.
///
/// # Returns
/// * `PyErr` : l'exception Python correspondante.
impl From<SeqError> for PyErr {
    fn from(err: SeqError) -> Self {
        match err {
            SeqError::InvalidSymbol { pos, symbol } => {
                PyValueError::new_err(format!("Invalid symbol '{symbol}' at position {pos}"))
            }
            SeqError::InvalidKmerLength { got } => {
                PyValueError::new_err(format!("Invalid K-mer length: {got}"))
            }
            SeqError::SliceOutOfBounds { index, len } => {
                PyIndexError::new_err(format!("Index {index} out of bounds for length {len}"))
            }
            SeqError::KmerTooLarge { got, max, bits } => PyValueError::new_err(format!(
                "K-mer length {got} exceeds capacity (max {max} for {bits}-bit symbols)"
            )),
            SeqError::NoComplementForCodec { codec } => PyValueError::new_err(format!(
                "Complement operation not supported for codec {codec}"
            )),
            SeqError::UnsupportedBitsPerSymbol { bits } => PyValueError::new_err(format!(
                "Unsupported bits per symbol: {bits} (must be between 1 and 8)"
            )),
            SeqError::SequenceTooLong { len } => {
                PyOverflowError::new_err(format!("Sequence too large to encode: {len} symbols"))
            }
        }
    }
}
