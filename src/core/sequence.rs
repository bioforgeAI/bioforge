use pyo3::prelude::*;
use pyo3::types::PyBytes;
use thiserror::Error;

/// Erreurs liées à la manipulation de séquences ADN.
///
/// # Variantes
/// - `InvalidCharacter`: Caractère invalide dans la séquence (ex: 'X' ou non-ASCII).
/// - `IndexOutOfBounds`: Index hors des limites de la séquence.
///
/// # Returns
/// Toujours converti en `PyErr` (via `From<SequenceError> for PyErr`).
#[derive(Error, Debug)]
pub enum SequenceError {
    #[error("Invalid character in sequence at index {index}: {character}")]
    InvalidCharacter { index: usize, character: char },
    #[error("Index out of bounds: {index} (length: {length})")]
    IndexOutOfBounds { index: isize, length: usize },
}

impl From<SequenceError> for PyErr {
    fn from(err: SequenceError) -> PyErr {
        use pyo3::exceptions::{PyIndexError, PyValueError};
        match err {
            SequenceError::InvalidCharacter { index, character } => PyValueError::new_err(format!(
                "Invalid character in sequence at index {}: {}",
                index, character
            )),
            SequenceError::IndexOutOfBounds { index, length } => PyIndexError::new_err(format!(
                "Index out of bounds: {} (length: {})",
                index, length
            )),
        }
    }
}

/// Table de correspondance générée à la compilation pour un encodage O(1) par caractère.
/// Associe chaque caractère ASCII (0-127) à sa valeur 3-bit (0xFF = invalide).
const ENCODE_MAP: [u8; 256] = build_encode_map();

const fn build_encode_map() -> [u8; 256] {
    let mut map = [0xFF; 256];
    let pairs = [
        (b'A', 0),
        (b'a', 0),
        (b'C', 1),
        (b'c', 1),
        (b'G', 2),
        (b'g', 2),
        (b'T', 3),
        (b't', 3),
        (b'N', 4),
        (b'n', 4),
        (b'R', 5),
        (b'r', 5),
        (b'Y', 6),
        (b'y', 6),
        (b'S', 7),
        (b's', 7),
        (b'W', 4),
        (b'w', 4),
        (b'K', 4),
        (b'k', 4),
        (b'M', 4),
        (b'm', 4),
        (b'B', 4),
        (b'b', 4),
        (b'D', 4),
        (b'd', 4),
        (b'H', 4),
        (b'h', 4),
        (b'V', 4),
        (b'v', 4),
    ];
    let mut i = 0;
    while i < pairs.len() {
        map[pairs[i].0 as usize] = pairs[i].1;
        i += 1;
    }
    map
}

/// Table de décodage inverse (0-7 → base).
const DECODE_MAP: [char; 8] = ['A', 'C', 'G', 'T', 'N', 'R', 'Y', 'S'];

/// Séquence d'ADN encodée en 3-bit (2 bases par octet).
///
/// # Description
/// Stocke une séquence ADN de manière compacte (3 bits par nucléotide) avec un accès O(1).
/// Utilise 2 bases par octet (6 bits utilisés) pour simplifier l'implémentation.
///
/// # Invariants
/// - `self.length` est toujours égal à la longueur originale de la séquence.
/// - Les bases sont toujours encodées en majuscules.
#[pyclass(module = "bioforge.core")]
pub struct Sequence3Bit {
    data: Vec<u8>,
    length: usize,
}

#[pymethods]
impl Sequence3Bit {
    /// Crée une nouvelle séquence à partir d'une chaîne ASCII.
    ///
    /// # Arguments
    /// * `seq`: Chaîne de caractères représentant l'ADN.
    ///   **Canonicalisation** : La séquence est mise en majuscules.
    ///   Les bases A, C, G, T, N, R, Y, S sont conservées.
    ///   Les autres bases IUPAC (W, K, M, B, D, H, V) sont dégradées en 'N' (valeur 4).
    ///   Tout autre caractère lève une `SequenceError::InvalidCharacter`.
    ///
    /// # Returns
    /// * `Sequence3Bit`: Objet séquence encodé.
    ///
    /// # Errors
    /// * `SequenceError::InvalidCharacter`: Si `seq` contient un caractère invalide ou non-ASCII.
    #[new]
    #[pyo3(signature = (seq, /))]
    pub fn new(seq: &str) -> Result<Self, SequenceError> {
        let length = seq.len();
        let capacity = (length + 1) / 2;
        let mut data = vec![0; capacity];

        for (i, c) in seq.chars().enumerate() {
            let b = c as u8;
            if b >= 128 {
                return Err(SequenceError::InvalidCharacter {
                    index: i,
                    character: c,
                });
            }
            let val = ENCODE_MAP[b as usize];
            if val == 0xFF {
                return Err(SequenceError::InvalidCharacter {
                    index: i,
                    character: c,
                });
            }
            let shift = if i % 2 == 0 { 3 } else { 0 }; // ✅ Décalage de 3 bits (0 ou 3)
            data[i / 2] |= val << shift;
        }

        Ok(Self { data, length })
    }

    /// Récupère la base à l'index donné (supporte les index négatifs).
    ///
    /// # Arguments
    /// * `index`: Index de la base (0 <= index < len ou -len <= index < 0).
    ///
    /// # Returns
    /// * `char`: La base à l'index donné (toujours en majuscule).
    ///
    /// # Errors
    /// * `SequenceError::IndexOutOfBounds`: Si l'index est hors limites.
    pub fn __getitem__(&self, index: isize) -> Result<char, SequenceError> {
        let mut idx = index;

        if idx < 0 {
            idx += self.length as isize;
        }

        if idx < 0 || idx >= self.length as isize {
            return Err(SequenceError::IndexOutOfBounds {
                index,
                length: self.length,
            });
        }

        let i = idx as usize;
        let shift = if i % 2 == 0 { 3 } else { 0 };
        let bits = (self.data[i / 2] >> shift) & 0b111;
        assert!(bits < 8, "Corruption mémoire détectée : bits = {}", bits);
        Ok(DECODE_MAP[bits as usize])
    }

    /// Retourne la longueur de la séquence.
    pub fn __len__(&self) -> usize {
        self.length
    }

    /// Décode la séquence entière en chaîne ASCII (majuscules).
    ///
    /// # Returns
    /// * `String`: La séquence décodée.
    #[pyo3(name = "to_string")]
    pub fn decode(&self) -> String {
        let mut s = String::with_capacity(self.length);
        for i in 0..self.length {
            let shift = if i % 2 == 0 { 3 } else { 0 };
            let bits = (self.data[i / 2] >> shift) & 0b111;
            assert!(bits < 8, "Corruption mémoire détectée : bits = {}", bits);
            s.push(DECODE_MAP[bits as usize]);
        }
        s
    }

    /// Retourne une copie du buffer interne encodé en 3-bit.
    ///
    /// # Returns
    /// * `Py<PyBytes>`: Buffer brut (garanti d'être un `bytes` en Python).
    #[pyo3(name = "to_bytes")]
    pub fn get_bytes(&self, py: Python) -> PyResult<Py<PyBytes>> {
        Ok(PyBytes::new_bound(py, &self.data).unbind())
    }

    /// Équivalent à `to_string()`, pour la compatibilité avec `str(seq)`.
    pub fn __str__(&self) -> String {
        self.decode()
    }
}
