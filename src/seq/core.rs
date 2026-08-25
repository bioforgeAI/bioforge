// Le bit-packing exige des casts de troncature délibérés (les symboles sont
// volontairement réduits à leur largeur en bits). Ces lints sont donc levés
// localement avec justification, conformément à la charte v4.4 §3.
#![allow(clippy::cast_possible_truncation)]
#![allow(clippy::cast_sign_loss)]
#![allow(clippy::cast_possible_wrap)]

use std::marker::PhantomData;

use super::codec::Codec;
use super::error::SeqError;

/// Séquence biologique possédée, encodée en bit-packing.
///
/// # Description
/// Structure générique sur un `Codec`. Le stockage (`Vec<u8>`) est un détail
/// d'implémentation : l'API publique n'expose que des symboles biologiques,
/// conformément à la charte v4.4 §4.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Seq<C: Codec> {
    data: Vec<u8>,
    len: usize,
    _codec: PhantomData<C>,
}

/// ⚠️ ATTENTION : `SeqSlice` est UNIQUEMENT pour un usage interne en Rust.
/// NE PAS exposer à Python via `PyO3` (problèmes de lifetime).
///
/// # Description
/// Vue zero-copy sur une sous-séquence. Utilisée par les algorithmes internes
/// pour éviter les copies mémoire (charte v4.4 §4).
#[allow(dead_code)] // Structure prête pour les opérations zero-copy internes futures
pub struct SeqSlice<'a, C: Codec> {
    data: &'a [u8],
    bit_offset: usize,
    len: usize,
    _codec: PhantomData<C>,
}

/// K-mer de longueur fixe connue à la compilation.
///
/// # Description
/// Représentation compacte d'un k-mer dans un `u128`, inspirée de `bio-seq`.
/// Supporte jusqu'à 64 symboles en 2-bit ou 32 symboles en 4-bit.
#[allow(dead_code)] // Structure prête pour l'implémentation des algorithmes de k-mers
pub struct Kmer<C: Codec, const K: usize> {
    data: u128,
    _codec: PhantomData<C>,
}

impl<C: Codec> Seq<C> {
    /// Crée une nouvelle séquence à partir d'un itérateur de symboles.
    ///
    /// # Arguments
    /// * `symbols` : itérateur de symboles à encoder.
    ///
    /// # Returns
    /// * `Ok(Self)` : la séquence encodée.
    ///
    /// # Errors
    /// * `SeqError::UnsupportedBitsPerSymbol` : si le codec déclare un nombre
    ///   de bits/symbole hors de la plage supportée (1..=8).
    /// * `SeqError::SequenceTooLong` : si la taille totale en bits déborde `usize`.
    /// * `SeqError::InvalidSymbol` : si un symbole n'est pas reconnu par le codec.
    pub fn new(symbols: impl IntoIterator<Item = C::Symbol>) -> Result<Self, SeqError> {
        let bits_per_symbol = C::BITS_PER_SYMBOL;
        // Invariant du codec : le bit-packing est implémenté pour 1..=8 bits/symbole.
        // Retourne une erreur au lieu de paniquer (charte v4.4 §3).
        if bits_per_symbol == 0 || bits_per_symbol > 8 {
            return Err(SeqError::UnsupportedBitsPerSymbol {
                bits: bits_per_symbol,
            });
        }

        let symbols: Vec<_> = symbols.into_iter().collect();
        let len = symbols.len();

        // Protection contre le débordement arithmétique (charte v4.4, audit Copilot).
        let total_bits = len
            .checked_mul(bits_per_symbol)
            .ok_or(SeqError::SequenceTooLong { len })?;
        // Équivalent de div_ceil(8), sans dépendre de Rust 1.73 (MSRV = 1.70).
        let capacity = total_bits / 8 + usize::from(total_bits % 8 != 0);

        let mut data = vec![0_u8; capacity];
        for (i, symbol) in symbols.into_iter().enumerate() {
            let val = C::encode(symbol).ok_or_else(|| SeqError::InvalidSymbol {
                pos: i,
                symbol: symbol.to_string().chars().next().unwrap_or('?'),
            })?;

            let bit_pos = i * bits_per_symbol;
            let octet_idx = bit_pos / 8;
            let bit_offset = bit_pos % 8;

            // Cast u8 -> u16 infallible : From est préféré à `as`.
            let val_u16 = u16::from(val);
            // Troncature u16 -> u8 DÉLIBÉRÉE : seule la partie basse (bits_per_symbol bits)
            // est conservée, le reste est nul par construction (val < 2^bits_per_symbol <= 256).
            data[octet_idx] |= (val_u16 << bit_offset) as u8;
            // Gestion du chevauchement d'octets (codecs 4-bit et 6-bit).
            if bit_offset + bits_per_symbol > 8 {
                data[octet_idx + 1] |= (val_u16 >> (8 - bit_offset)) as u8;
            }
        }

        Ok(Self {
            data,
            len,
            _codec: PhantomData,
        })
    }

    /// Retourne le symbole à la position `i`.
    ///
    /// # Arguments
    /// * `i` : index du symbole (0-based).
    ///
    /// # Returns
    /// * `Some(C::Symbol)` : le symbole décodé.
    /// * `None` : si `i` est hors des limites de la séquence.
    #[must_use]
    pub fn get(&self, i: usize) -> Option<C::Symbol> {
        if i >= self.len {
            return None;
        }
        let bits_per_symbol = C::BITS_PER_SYMBOL;
        let bit_pos = i * bits_per_symbol;
        let octet_idx = bit_pos / 8;
        let bit_offset = bit_pos % 8;
        // mask est construit pour tenir dans bits_per_symbol bits (<= 8), donc u8 suffit.
        let mask: u8 = (1_u8 << bits_per_symbol) - 1;

        // Cast u8 -> u16 infallible : From est préféré à `as`.
        let mut val = u16::from(self.data[octet_idx]) >> bit_offset;
        if bit_offset + bits_per_symbol > 8 {
            val |= u16::from(self.data[octet_idx + 1]) << (8 - bit_offset);
        }

        // Troncature u16 -> u8 DÉLIBÉRÉE : le masquage par `mask` (u8) garantit que
        // seules les bits_per_symbol bits basses sont conservées, valeur < 256.
        C::decode((val & u16::from(mask)) as u8)
    }

    /// Retourne le complément inverse de la séquence.
    ///
    /// # Returns
    /// * `Ok(Self)` : la séquence complément inverse.
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
            symbols.push(C::complement(symbol).ok_or(SeqError::NoComplementForCodec {
                codec: std::any::type_name::<C>(),
            })?);
        }
        Self::new(symbols)
    }

    /// Retourne la longueur de la séquence (nombre de symboles).
    ///
    /// # Returns
    /// * `usize` : nombre de symboles.
    #[must_use]
    pub fn len(&self) -> usize {
        self.len
    }

    /// Indique si la séquence est vide.
    ///
    /// # Returns
    /// * `bool` : `true` si la séquence ne contient aucun symbole.
    #[allow(dead_code)] // Méthode utilitaire standard, sera utilisée par les parseurs
    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.len == 0
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::seq::codec::{Dna, DnaBase};

    #[test]
    fn dna_roundtrip_preserves_symbols() -> Result<(), SeqError> {
        let input = [DnaBase::A, DnaBase::T, DnaBase::G, DnaBase::C];
        let seq = Seq::<Dna>::new(input)?;
        assert_eq!(seq.len(), 4);
        for (i, &expected) in input.iter().enumerate() {
            assert_eq!(seq.get(i), Some(expected));
        }
        assert_eq!(seq.get(4), None);
        Ok(())
    }

    #[test]
    fn reverse_complement_is_involution() -> Result<(), SeqError> {
        let input = [DnaBase::A, DnaBase::T, DnaBase::G, DnaBase::C];
        let seq = Seq::<Dna>::new(input)?;
        let rc = seq.reverse_complement()?;
        let rc2 = rc.reverse_complement()?;
        // Utilisation de PartialEq au lieu de to_bytes()
        assert_eq!(rc2, seq);
        Ok(())
    }

    #[test]
    fn odd_length_sequence_roundtrips() -> Result<(), SeqError> {
        let input = [DnaBase::A, DnaBase::C, DnaBase::G];
        let seq = Seq::<Dna>::new(input)?;
        assert_eq!(seq.len(), 3);
        for (i, &expected) in input.iter().enumerate() {
            assert_eq!(seq.get(i), Some(expected));
        }
        Ok(())
    }
}
