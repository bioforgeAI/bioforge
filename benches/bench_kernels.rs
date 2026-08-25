//! Benchmarks des kernels Rust purs de `BioForge`.
//!
//! # Description
//! Conforme à la charte `BioForge` v4.5 §7 (benchmarks multi-niveaux).
//! Ces benchmarks mesurent les kernels Rust SANS la couche `PyO3`, afin de
//! séparer les coûts FFI des coûts algorithmiques (recommandation `ChatGPT`).
//!
//! # Couverture des cas `len % 4`
//! Les tailles incluent explicitement toutes les classes de reste modulo 4
//! ({0, 1, 2, 3}), comme exigé par Claude pour valider le futur RC bit-natif.

use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion};

use bioforge::seq::codec::{Dna, DnaBase};
use bioforge::seq::core::Seq;

/// Tailles de benchmark couvrant toutes les classes `len % 4`.
///
/// # Invariants
/// - `1000 % 4 == 0`, `1001 % 4 == 1`, `1002 % 4 == 2`, `1003 % 4 == 3`
/// - `10000` et `100000` pour les volumes réalistes.
const SIZES: &[usize] = &[1000, 1001, 1002, 1003, 10_000, 100_000];

/// Génère une séquence ADN déterministe pseudo-aléatoire.
///
/// # Arguments
/// * `len` : longueur de la séquence à générer.
///
/// # Returns
/// * `String` : séquence composée uniquement de A/C/G/T.
///
/// # Invariants
/// - Même `len` produit toujours la même séquence (déterminisme, charte §6).
/// - La séquence ne contient que A/C/G/T.
fn generate_dna_string(len: usize) -> String {
    let mut state: u64 = 0x1234_5678_9ABC_DEF0;
    (0..len)
        .map(|_| {
            // LCG déterministe (constantes de Knuth).
            state = state
                .wrapping_mul(6_364_136_223_846_793_005)
                .wrapping_add(1_442_695_040_888_963_407);
            match (state >> 62) as usize {
                0 => 'A',
                1 => 'C',
                2 => 'G',
                _ => 'T',
            }
        })
        .collect()
}

/// Convertit une séquence String en Vec<DnaBase> (setup hors benchmark).
///
/// # Arguments
/// * `s` : la séquence à convertir.
///
/// # Returns
/// * `Vec<DnaBase>` : les symboles convertis.
fn to_dna_bases(s: &str) -> Vec<DnaBase> {
    s.chars()
        .map(|c| DnaBase::from_char(c).expect("generated DNA is always valid"))
        .collect()
}

/// Benchmark : encodage (chars → bit-packing).
///
/// # Description
/// Mesure `Seq::<Dna>::new()` sur des symboles déjà convertis en `DnaBase`.
/// Isole le coût du bit-packing pur, sans la conversion char→DnaBase.
fn bench_encode(c: &mut Criterion) {
    let mut group = c.benchmark_group("kernel_encode_dna");
    for &len in SIZES {
        let symbols = to_dna_bases(&generate_dna_string(len));
        group.bench_with_input(BenchmarkId::from_parameter(len), &symbols, |b, symbols| {
            b.iter(|| {
                Seq::<Dna>::new(black_box(symbols.iter().copied())).expect("valid DNA symbols")
            });
        });
    }
    group.finish();
}

/// Benchmark : décodage complet (bit-packing → String).
///
/// # Description
/// Mesure la reconstruction de la String complète depuis la représentation
/// compacte. C'est l'opération équivalente à `str()` côté Python.
fn bench_decode_full(c: &mut Criterion) {
    let mut group = c.benchmark_group("kernel_decode_full_dna");
    for &len in SIZES {
        let symbols = to_dna_bases(&generate_dna_string(len));
        let seq = Seq::<Dna>::new(symbols).expect("valid DNA symbols");
        group.bench_with_input(BenchmarkId::from_parameter(len), &seq, |b, seq| {
            b.iter(|| {
                let mut s = String::with_capacity(seq.len());
                for i in 0..seq.len() {
                    if let Some(sym) = seq.get(i) {
                        s.push(sym.to_char());
                    }
                }
                black_box(s)
            });
        });
    }
    group.finish();
}

/// Benchmark : accès individuel (get).
///
/// # Description
/// Mesure le coût de `seq.get(i)` répété sur toute la séquence.
/// Ce kernel est actuellement utilisé dans les boucles internes (à optimiser).
fn bench_get_individual(c: &mut Criterion) {
    let mut group = c.benchmark_group("kernel_get_individual_dna");
    for &len in SIZES {
        let symbols = to_dna_bases(&generate_dna_string(len));
        let seq = Seq::<Dna>::new(symbols).expect("valid DNA symbols");
        group.bench_with_input(BenchmarkId::from_parameter(len), &seq, |b, seq| {
            b.iter(|| {
                let mut count = 0usize;
                for i in 0..seq.len() {
                    if seq.get(i).is_some() {
                        count += 1;
                    }
                }
                black_box(count)
            });
        });
    }
    group.finish();
}

/// Benchmark : reverse complement.
///
/// # Description
/// Mesure `Seq::<Dna>::reverse_complement()`. C'est le kernel prioritaire
/// à optimiser (RC bit-natif, preuve algébrique fournie par Claude).
fn bench_reverse_complement(c: &mut Criterion) {
    let mut group = c.benchmark_group("kernel_reverse_complement_dna");
    for &len in SIZES {
        let symbols = to_dna_bases(&generate_dna_string(len));
        let seq = Seq::<Dna>::new(symbols).expect("valid DNA symbols");
        group.bench_with_input(BenchmarkId::from_parameter(len), &seq, |b, seq| {
            b.iter(|| seq.reverse_complement().expect("valid DNA"));
        });
    }
    group.finish();
}

criterion_group!(
    benches,
    bench_encode,
    bench_decode_full,
    bench_get_individual,
    bench_reverse_complement
);
criterion_main!(benches);
