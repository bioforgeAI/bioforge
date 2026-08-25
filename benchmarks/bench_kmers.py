"""Benchmarks d'itération de k-mers : BioForge vs boucle manuelle Biopython.

Conforme à la charte BioForge v4.5 §7.

Convention de nommage : test_{operation}__{implementation}
pour garantir des résultats interprétables.

Lancement :
    pytest benchmarks/bench_kmers.py -v
"""

from __future__ import annotations

from typing import Any

import pytest

from bioforge import DnaSequence

# pytest-benchmark est une dépendance externe sans stubs de typage.
# Conformément à la charte BioForge v4.5 §2, on annote le fixture avec Any.
BenchmarkFixture = Any

Bio = pytest.importorskip("Bio", reason="Biopython requis pour les benchmarks")
from Bio.Seq import Seq

# Taille de k-mer typique pour l'assemblage / indexation.
K = 31


def test_kmer_iteration__bioforge_lazy(
    benchmark: BenchmarkFixture, seq_str_small: str
) -> None:
    """Itération paresseuse BioForge (O(1) mémoire)."""
    seq = DnaSequence(seq_str_small)
    # Consommer l'itérateur pour mesurer le temps total.
    benchmark(lambda: sum(1 for _ in seq.kmers(K)))


def test_kmer_iteration__biopython_manual(
    benchmark: BenchmarkFixture, seq_str_small: str
) -> None:
    """Boucle manuelle de slicing Biopython (approche standard)."""
    seq = Seq(seq_str_small)

    def iterate() -> int:
        count = 0
        for i in range(len(seq) - K + 1):
            _ = seq[i : i + K]
            count += 1
        return count

    benchmark(iterate)
