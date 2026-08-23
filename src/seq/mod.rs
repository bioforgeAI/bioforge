pub mod codec;
pub mod core;
pub mod dna;
pub mod error;

// Exposition des types Python au niveau du module `seq`
pub use dna::PyDnaSequence;
