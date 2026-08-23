use pyo3::{
    exceptions::{PyIndexError, PyValueError},
    PyErr,
};
use thiserror::Error;

/// Erreurs liées à la manipulation des séquences biologiques.
///
/// # Variantes
/// - `InvalidSymbol`: Symbole invalide pour le codec utilisé à une position donnée.
/// - `InvalidKmerLength`: Longueur de k-mer demandée invalide (doit être > 0).
/// - `SliceOutOfBounds`: Index de slice hors des limites de la séquence.
/// - `KmerTooLarge`: Le k-mer est trop grand pour tenir dans le stockage interne (u128).
/// - `NoComplementForCodec`: Le codec ne supporte pas l'opération de complément (ex: protéines).
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
}

/// Mapping exhaustif des erreurs Rust vers les exceptions Python.
///
/// # Variantes
/// - `InvalidSymbol` → `PyValueError`
/// - `SliceOutOfBounds` → `PyIndexError`
/// - `InvalidKmerLength`, `KmerTooLarge`, `NoComplementForCodec` → `PyValueError`
impl From<SeqError> for PyErr {
    fn from(err: SeqError) -> Self {
        match err {
            SeqError::InvalidSymbol { pos, symbol } => {
                PyValueError::new_err(format!("Invalid symbol '{}' at position {}", symbol, pos))
            }
            SeqError::InvalidKmerLength { got } => {
                PyValueError::new_err(format!("Invalid K-mer length: {}", got))
            }
            SeqError::SliceOutOfBounds { index, len } => {
                PyIndexError::new_err(format!("Index {} out of bounds for length {}", index, len))
            }
            SeqError::KmerTooLarge { got, max, bits } => PyValueError::new_err(format!(
                "K-mer length {} exceeds capacity (max {} for {}-bit symbols)",
                got, max, bits
            )),
            SeqError::NoComplementForCodec { codec } => PyValueError::new_err(format!(
                "Complement operation not supported for codec {}",
                codec
            )),
        }
    }
}
