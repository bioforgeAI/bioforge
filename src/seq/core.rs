use super::codec::Codec;
use super::error::SeqError;
use std::marker::PhantomData;

pub struct Seq<C: Codec> {
    data: Vec<u8>,
    len: usize,
    _codec: PhantomData<C>,
}

/// ⚠️ ATTENTION : `SeqSlice` est UNIQUEMENT pour un usage interne en Rust.
/// NE PAS exposer à Python via PyO3 (problèmes de lifetime).
#[allow(dead_code)] // Structure prête pour les opérations zero-copy internes fu
pub struct SeqSlice<'a, C: Codec> {
    data: &'a [u8],
    bit_offset: usize,
    len: usize,
    _codec: PhantomData<C>,
}

/// K-mer de longueur fixe connue à la compilation.
/// Utilise `u128` pour supporter des k-mers jusqu'à 64 bases (en 2-bit) ou 32 bases (en 4-bit).
#[allow(dead_code)] // Structure prête pour l'implémentation des algorithmes de k-mers
pub struct Kmer<C: Codec, const K: usize> {
    data: u128,
    _codec: PhantomData<C>,
}

impl<C: Codec> Seq<C> {
    pub fn new(symbols: impl IntoIterator<Item = C::Symbol>) -> Result<Self, SeqError> {
        let symbols: Vec<_> = symbols.into_iter().collect();
        let len = symbols.len();
        let bits_per_symbol = C::BITS_PER_SYMBOL;

        // Sécurité : garantit que le bit-packing fonctionne avec des opérations u8/u16
        assert!(
            bits_per_symbol <= 8,
            "BITS_PER_SYMBOL must be <= 8 for u8 packing"
        );

        let capacity = (len * bits_per_symbol + 7) / 8;
        let mut data = vec![0; capacity];

        for (i, symbol) in symbols.into_iter().enumerate() {
            let val = C::encode(symbol).ok_or(SeqError::InvalidSymbol {
                pos: i,
                symbol: symbol.to_string().chars().next().unwrap_or('?'),
            })?;

            let bit_pos = i * bits_per_symbol;
            let octet_idx = bit_pos / 8;
            let bit_offset = bit_pos % 8;

            let val_u16 = val as u16;
            data[octet_idx] |= (val_u16 << bit_offset) as u8;

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

    pub fn get(&self, i: usize) -> Option<C::Symbol> {
        if i >= self.len {
            return None;
        }
        let bits_per_symbol = C::BITS_PER_SYMBOL;
        let bit_pos = i * bits_per_symbol;
        let octet_idx = bit_pos / 8;
        let bit_offset = bit_pos % 8;
        let mask = (1 << bits_per_symbol) - 1;

        let mut val = (self.data[octet_idx] >> bit_offset) as u16;
        if bit_offset + bits_per_symbol > 8 {
            val |= (self.data[octet_idx + 1] as u16) << (8 - bit_offset);
        }

        C::decode((val & (mask as u16)) as u8)
    }

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

    pub fn to_bytes(&self) -> Vec<u8> {
        self.data.clone()
    }
    pub fn len(&self) -> usize {
        self.len
    }
    pub fn is_empty(&self) -> bool {
        self.len == 0
    }
}
