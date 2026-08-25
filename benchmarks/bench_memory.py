"""Benchmarks d'allocation mémoire par opération.

Conforme à la charte BioForge v4.5 §7 (mesure de la mémoire).

Note : La mesure du peak RSS global exigée par le smoke test FASTQ (charte §7)
sera activée dans un processus isolé lorsque le parsing FASTQ sera implémenté.
Ici, on mesure l'allocation Python via tracemalloc (composante Rust incluse
indirectement via les objets retournés).

Lancement :
    pytest benchmarks/bench_memory.py -v -s
"""

from __future__ import annotations

import tracemalloc
from collections.abc import Callable

import pytest

from bioforge import DnaSequence
from reference.dna import DnaReference

Bio = pytest.importorskip("Bio", reason="Biopython requis pour les benchmarks")
from Bio.Seq import Seq


def measure_peak_bytes(factory: Callable[[], object]) -> int:
    """Mesure le pic d'allocation mémoire (bytes) pour une opération.

    Args:
        factory: Callable qui crée l'objet à mesurer.

    Returns:
        int: Pic d'allocation en bytes.

    Invariants:
        - Le résultat est déterministe pour une même entrée
        - Le résultat est >= 0
    """
    tracemalloc.start()
    try:
        _ = factory()
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return peak


def _report(label: str, seq_len: int, peak_bytes: int) -> None:
    """Affiche un rapport de mémoire normalisé par base."""
    bytes_per_base = peak_bytes / seq_len if seq_len > 0 else 0.0
    print(
        f"\n  [{label}] seq_len={seq_len:>8}  peak={peak_bytes:>12} B  "
        f"({bytes_per_base:.2f} B/base)"
    )


def test_memory_creation(seq_str_small: str) -> None:
    """Compare l'allocation mémoire à la création pour les 3 implémentations."""
    seq_len = len(seq_str_small)

    peak_bioforge = measure_peak_bytes(lambda: DnaSequence(seq_str_small))
    peak_biopython = measure_peak_bytes(lambda: Seq(seq_str_small))
    peak_reference = measure_peak_bytes(lambda: DnaReference(seq_str_small))

    _report("BioForge ", seq_len, peak_bioforge)
    _report("Biopython", seq_len, peak_biopython)
    _report("Reference", seq_len, peak_reference)

    # Invariant : BioForge (2-bit) doit allouer moins que la référence (1 octet/base).
    assert peak_bioforge < peak_reference, (
        f"BioForge ({peak_bioforge} B) devrait allouer moins que la "
        f"référence ({peak_reference} B)"
    )
