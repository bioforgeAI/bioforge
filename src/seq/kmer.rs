//! K-mers avec stockage compact.
//!
//! # Description
//! Un k-mer est une sous-séquence de longueur fixe, stockée de manière
//! compacte dans un registre `u128`. Pour DNA (2 bits/base), cela permet
//! de stocker jusqu'à 64 bases sans allocation heap, avec un hashing parfait
//! (la valeur encodée est une bijection).
//!
//! # Compromis par rapport à bio-seq
//! bio-seq utilise `Kmer<C, const K: usize>` (longueur connue à la compilation).
//! Ici, la longueur est dynamique mais bornée, afin de permettre une exposition
//! Python ergonomique. Le modèle `const K` pourra être introduit ultérieurement
//! dans le cœur Rust pour les hot-paths critiques (ex: k-mer counting avec k
//! fixé), de manière transparente pour l'utilisateur Python.
// Les casts dans kmer.rs sont mathématiquement sûrs :

// - u128 -> u8 dans `get()` : la valeur est masquée par (2^bits - 1) où bits ∈ [1, 8]
// - u128 -> u64 dans `__hash__()` : repli volontaire (XOR des moitiés) pour un hash Python
#![allow(clippy::cast_possible_truncation)]

use std::marker::PhantomData;

use pyo3::prelude::*;

use super::codec::{Codec, Dna, DnaBase};
use super::core::Seq;
use super::error::SeqError;

/// Nombre maximum de bits pour le stockage compact d'un k-mer.
///
/// # Description
/// Un `u128` permet de stocker jusqu'à 128 bits. Pour DNA (2 bits/base),
/// cela correspond à 64 bases ; pour IUPAC (4 bits/base), 32 bases ;
/// pour Amino (6 bits/base), 21 bases.
pub const KMER_STORAGE_BITS: usize = 128;

/// Un k-mer avec stockage compact.
///
/// # Description
/// Représente une sous-séquence de longueur fixe, encodée dans un `u128`.
/// La valeur encodée sert de hash parfait (sans collision) pour les k-mers
/// dont la longueur respecte la capacité de stockage.
///
/// # Invariants
/// - `1 <= len <= KMER_STORAGE_BITS / C::BITS_PER_SYMBOL`
/// - `data` contient uniquement les `len * C::BITS_PER_SYMBOL` bits significatifs
/// - La valeur encodée est une bijection entre k-mers de même longueur
#[derive(Clone, Copy)]
pub struct Kmer<C: Codec> {
    /// Valeur encodée du k-mer (bit-packing).
    data: u128,
    /// Longueur du k-mer (nombre de symboles).
    len: usize,
    _codec: PhantomData<C>,
}

impl<C: Codec> Kmer<C> {
    /// Crée un k-mer à partir d'un itérateur de symboles.
    ///
    /// # Arguments
    /// * `symbols` : itérateur de symboles à encoder.
    ///
    /// # Returns
    /// * `Ok(Self)` : le k-mer encodé.
    ///
    /// # Errors
    /// * `SeqError::InvalidKmerLength` : si l'itérateur est vide.
    /// * `SeqError::KmerTooLarge` : si la longueur dépasse la capacité de stockage.
    /// * `SeqError::InvalidSymbol` : si un symbole n'est pas reconnu par le codec.
    pub fn new(symbols: impl IntoIterator<Item = C::Symbol>) -> Result<Self, SeqError> {
        let symbols: Vec<_> = symbols.into_iter().collect();
        let len = symbols.len();

        if len == 0 {
            return Err(SeqError::InvalidKmerLength { got: 0 });
        }

        let max_len = KMER_STORAGE_BITS / C::BITS_PER_SYMBOL;
        if len > max_len {
            return Err(SeqError::KmerTooLarge {
                got: len,
                max: max_len,
                bits: C::BITS_PER_SYMBOL,
            });
        }

        let mut data: u128 = 0;
        for (i, symbol) in symbols.into_iter().enumerate() {
            let val = C::encode(symbol).ok_or(SeqError::InvalidSymbol {
                pos: i,
                symbol: symbol.to_string().chars().next().unwrap_or('?'),
            })?;
            // Le shift est sûr : i < len <= max_len, donc i * BITS < 128.
            data |= u128::from(val) << (i * C::BITS_PER_SYMBOL);
        }

        Ok(Self {
            data,
            len,
            _codec: PhantomData,
        })
    }

    /// Retourne la longueur du k-mer.
    ///
    /// # Returns
    /// * `usize` : nombre de symboles.
    #[must_use]
    pub fn len(&self) -> usize {
        self.len
    }

    /// Retourne le symbole à la position `i`.
    ///
    /// # Arguments
    /// * `i` : index du symbole (0-based).
    ///
    /// # Returns
    /// * `Some(C::Symbol)` : le symbole décodé.
    /// * `None` : si `i` est hors des limites.
    ///
    /// # Safety (cast)
    /// Le cast `u128 -> u8` est sûr : la valeur extraite est masquée par
    /// `(1 << BITS_PER_SYMBOL) - 1`, où `BITS_PER_SYMBOL ∈ [1, 8]`, donc
    /// la valeur résultante est toujours < 256.
    #[must_use]
    pub fn get(&self, i: usize) -> Option<C::Symbol> {
        if i >= self.len {
            return None;
        }
        let bits = C::BITS_PER_SYMBOL;
        let mask = (1_u128 << bits) - 1;
        let val = (self.data >> (i * bits)) & mask;
        // Le cast est sûr : val < 2^bits <= 2^8 = 256.
        C::decode(val as u8)
    }

    /// Retourne la valeur encodée du k-mer.
    ///
    /// # Description
    /// Cette valeur est un hash parfait : deux k-mers distincts de même
    /// longueur ont toujours des valeurs distinctes.
    ///
    /// # Returns
    /// * `u128` : la valeur encodée.
    #[must_use]
    pub fn encoded_value(&self) -> u128 {
        self.data
    }

    /// Retourne le reverse complement du k-mer.
    ///
    /// # Returns
    /// * `Ok(Self)` : le k-mer complément inverse.
    ///
    /// # Errors
    /// * `SeqError::NoComplementForCodec` : si le codec ne supporte pas le complément.
    /// * `SeqError::InvalidSymbol` : si un symbole interne est corrompu.
    pub fn reverse_complement(&self) -> Result<Self, SeqError> {
        let mut symbols = Vec::with_capacity(self.len);
        for i in (0..self.len).rev() {
            let symbol = self.get(i).ok_or(SeqError::InvalidSymbol {
                pos: i,
                symbol: '?',
            })?;
            let comp = C::complement(symbol).ok_or(SeqError::NoComplementForCodec {
                codec: std::any::type_name::<C>(),
            })?;
            symbols.push(comp);
        }
        Self::new(symbols)
    }

    /// Retourne le k-mer canonique (minimum entre self et `reverse_complement`).
    ///
    /// # Description
    /// La comparaison se fait sur la valeur encodée. Cela permet de traiter
    /// un k-mer et son reverse complement comme une entité unique.
    ///
    /// # Returns
    /// * `Ok(Self)` : le k-mer canonique.
    ///
    /// # Errors
    /// * `SeqError::NoComplementForCodec` : si le codec ne supporte pas le complément.
    pub fn canonical(&self) -> Result<Self, SeqError> {
        let rc = self.reverse_complement()?;
        if self.data <= rc.data {
            Ok(*self)
        } else {
            Ok(rc)
        }
    }
}

/// K-mer d'ADN exposé à Python.
///
/// # Description
/// Wrapper `PyO3` autour de `Kmer<Dna>`. Encodage 2 bits/base dans un `u128`,
/// permettant un hashing parfait pour k <= 64.
///
/// # Invariants
/// - `1 <= len(self) <= 64`
/// - `str(self)` ne contient que A/C/G/T en majuscules
/// - `hash(self)` est la valeur encodée (hash parfait)
#[pyclass(module = "bioforge.seq", name = "DnaKmer")]
pub struct PyDnaKmer {
    inner: Kmer<Dna>,
}

#[pymethods]
impl PyDnaKmer {
    /// Crée un `DnaKmer` à partir d'une chaîne de caractères.
    ///
    /// # Arguments
    /// * `seq` : chaîne composée de A, C, G, T (insensible à la casse),
    ///   de longueur 1 à 64.
    ///
    /// # Returns
    /// * `PyResult<Self>` : le k-mer encodé.
    ///
    /// # Errors
    /// * `ValueError` : si `seq` est vide, trop longue, ou contient un
    ///   caractère invalide.
    #[new]
    #[pyo3(signature = (seq, /))]
    pub fn new(seq: &str) -> PyResult<Self> {
        // Conversion char → DnaBase avec validation (Dna::Symbol = DnaBase).
        let symbols: Result<Vec<_>, _> = seq
            .chars()
            .enumerate()
            .map(|(i, c)| {
                DnaBase::from_char(c).ok_or(SeqError::InvalidSymbol { pos: i, symbol: c })
            })
            .collect();

        Ok(Self {
            inner: Kmer::new(symbols?)?,
        })
    }

    /// Retourne la longueur du k-mer.
    pub fn __len__(&self) -> usize {
        self.inner.len()
    }

    /// Retourne le k-mer sous forme de chaîne.
    pub fn __str__(&self) -> String {
        let mut s = String::with_capacity(self.inner.len());
        for i in 0..self.inner.len() {
            if let Some(symbol) = self.inner.get(i) {
                s.push(symbol.to_char());
            }
        }
        s
    }

    /// Retourne le hash du k-mer (valeur encodée, hash parfait).
    ///
    /// # Description
    /// Pour k <= 32, la valeur encodée tient dans un u64 et est retournée
    /// directement (hash parfait, zéro collision). Pour k > 32, les deux
    /// moitiés du u128 sont repliées par XOR (repli déterministe).
    ///
    /// # Safety (cast)
    /// Les casts `u128 -> u64` sont intentionnels : ils implémentent le
    /// repli déterministe par XOR des deux moitiés du u128, nécessaire pour
    /// produire un hash Python (int signé 64 bits).
    pub fn __hash__(&self) -> u64 {
        let value = self.inner.encoded_value();
        (value as u64) ^ ((value >> 64) as u64)
    }

    /// Compare deux k-mers pour l'égalité.
    ///
    /// # Arguments
    /// * `other` : le k-mer à comparer.
    ///
    /// # Returns
    /// * `bool` : true si même longueur et même valeur encodée.
    pub fn __eq__(&self, other: &Self) -> bool {
        self.inner.len() == other.inner.len()
            && self.inner.encoded_value() == other.inner.encoded_value()
    }

    /// Retourne le reverse complement du k-mer.
    pub fn reverse_complement(&self) -> PyResult<Self> {
        Ok(Self {
            inner: self.inner.reverse_complement()?,
        })
    }

    /// Retourne le k-mer canonique (min entre self et `reverse_complement`).
    pub fn canonical(&self) -> PyResult<Self> {
        Ok(Self {
            inner: self.inner.canonical()?,
        })
    }
}

/// Itérateur paresseux sur les k-mers d'une séquence d'ADN.
///
/// # Description
/// Itérateur de mémoire constante O(1) : il possède une copie compacte des
/// données packées de la séquence source (2 bits/base) et avance via un index.
/// Aucune liste de k-mers n'est matérialisée.
///
/// # Choix d'implémentation
/// Les données packées sont copiées (et non une référence Python) pour éviter
/// les allers-retours `PyO3`` à chaque k-mer et garantir la sûreté des durées de
/// vie. Pour une séquence DNA de 1M de bases, la copie est ~250 KB (2-bit),
/// un surcoût négligeable au regard de l'efficacité d'itération.
#[pyclass(module = "bioforge.seq", name = "DnaKmerIterator")]
pub struct PyDnaKmerIterator {
    seq: Seq<Dna>,
    index: usize,
    k: usize,
}

impl PyDnaKmerIterator {
    /// Crée un nouvel itérateur de k-mers.
    ///
    /// # Arguments
    /// * `seq` : séquence source (copie compacte des données packées).
    /// * `k` : longueur des k-mers à produire.
    ///
    /// # Returns
    /// * `Self` : l'itérateur initialisé à l'index 0.
    pub(crate) fn new(seq: Seq<Dna>, k: usize) -> Self {
        Self { seq, index: 0, k }
    }
}

#[pymethods]
impl PyDnaKmerIterator {
    /// Retourne l'itérateur lui-même (protocole d'itération Python).
    pub fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    /// Retourne le prochain k-mer, ou lève `StopIteration`.
    ///
    /// # Returns
    /// * `Ok(Some(PyDnaKmer))` : le prochain k-mer.
    /// * `Ok(None)` : fin de l'itération (traduit en `StopIteration`).
    ///
    /// # Errors
    /// * `ValueError` : si un symbole interne est corrompu (ne devrait pas arriver).
    pub fn __next__(&mut self) -> PyResult<Option<PyDnaKmer>> {
        if self.index + self.k > self.seq.len() {
            return Ok(None);
        }

        let mut symbols = Vec::with_capacity(self.k);
        for j in 0..self.k {
            let sym = self
                .seq
                .get(self.index + j)
                .ok_or(SeqError::InvalidSymbol {
                    pos: self.index + j,
                    symbol: '?',
                })?;
            symbols.push(sym);
        }

        let kmer = Kmer::<Dna>::new(symbols)?;
        self.index += 1;
        Ok(Some(PyDnaKmer { inner: kmer }))
    }
}
