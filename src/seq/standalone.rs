//! Fonctions standalone pour la manipulation de séquences.
//!
//! # Description
//! Ces fonctions offrent un accès rapide sans instanciation explicite d'un
//! objet de séquence. Elles délèguent **entièrement** au moteur `Seq<Codec>`
//! existant (principe DRY : aucune duplication de logique de validation,
//! de bit-packing ou de gestion d'erreurs).
//!
//! # Conception
//! - `reverse_complement_strict` → délègue à `Seq<Dna>` (codec 2-bit, A/C/G/T uniquement)
//! - `reverse_complement_ambiguous` → délègue à `Seq<Iupac>` (codec 4-bit, 15 codes IUPAC)

use pyo3::prelude::*;

use super::codec::{Dna, DnaBase, Iupac};
use super::core::Seq;
use super::error::SeqError;

/// Retourne le complément inverse d'une séquence ADN stricte (A, C, G, T).
///
/// # Description
/// Version stricte qui rejette toute séquence contenant un caractère autre
/// que A, C, G, T (casse ignorée). Délègue à `Seq<Dna>::reverse_complement()`.
///
/// # Arguments
/// * `seq` : chaîne composée uniquement de A, C, G, T (insensible à la casse).
///
/// # Returns
/// * `PyResult<String>` : la séquence complément inverse en majuscules.
///
/// # Errors
/// * `ValueError` : si `seq` contient un caractère autre que A/C/G/T
///   (y compris N et les codes IUPAC ambigus).
///
/// # Invariants
/// - `len(output) == len(input)`
/// - `reverse_complement_strict(reverse_complement_strict(s)) == s.upper()`
/// - `"" → ""`
#[pyfunction]
#[pyo3(signature = (seq, /))]
pub fn reverse_complement_strict(seq: &str) -> PyResult<String> {
    // Conversion char → DnaBase avec validation (Dna::Symbol = DnaBase, pas char).
    let symbols: Result<Vec<_>, _> = seq
        .chars()
        .enumerate()
        .map(|(i, c)| DnaBase::from_char(c).ok_or(SeqError::InvalidSymbol { pos: i, symbol: c }))
        .collect();

    // Délégation totale au moteur Seq<Dna> (reverse complement).
    let dna_seq: Seq<Dna> = Seq::new(symbols?)?;
    let rc = dna_seq.reverse_complement()?;

    // Reconstruction en String via DnaBase::to_char().
    let mut s = String::with_capacity(rc.len());
    for i in 0..rc.len() {
        if let Some(symbol) = rc.get(i) {
            s.push(symbol.to_char());
        }
    }
    Ok(s)
}

/// Retourne le complément inverse d'une séquence ADN avec ambiguïtés IUPAC.
///
/// # Description
/// Version permissive qui accepte tous les codes IUPAC (A C G T N R Y S
/// W K M B D H V) et préserve l'information d'ambiguïté lors du complément.
/// Délègue à `Seq<Iupac>::reverse_complement()`.
///
/// Table de complément : A↔T C↔G N↔N R↔Y S↔S W↔W K↔M B↔V D↔H
///
/// # Arguments
/// * `seq` : chaîne composée de symboles IUPAC (insensible à la casse).
///
/// # Returns
/// * `PyResult<String>` : la séquence complément inverse en majuscules,
///   avec les codes d'ambiguïté préservés.
///
/// # Errors
/// * `ValueError` : si `seq` contient un caractère hors alphabet IUPAC.
///
/// # Invariants
/// - `len(output) == len(input)`
/// - `reverse_complement_ambiguous(reverse_complement_ambiguous(s)) == s.upper()`
/// - `"" → ""`
/// - Aucune perte d'information IUPAC.
#[pyfunction]
#[pyo3(signature = (seq, /))]
pub fn reverse_complement_ambiguous(seq: &str) -> PyResult<String> {
    // Iupac::Symbol = char, on passe directement les caractères.
    // La validation et la canonicalisation (majuscules) sont gérées
    // par Iupac::encode() à l'intérieur de Seq::new().
    let iupac_seq: Seq<Iupac> = Seq::new(seq.chars())?;
    let rc = iupac_seq.reverse_complement()?;

    // Reconstruction en String. Iupac::Symbol = char, push direct.
    let mut s = String::with_capacity(rc.len());
    for i in 0..rc.len() {
        if let Some(symbol) = rc.get(i) {
            s.push(symbol);
        }
    }
    Ok(s)
}
