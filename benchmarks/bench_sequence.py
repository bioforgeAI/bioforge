"""Benchmarks comparatifs de séquences : BioForge vs Biopython vs Référence.

Conforme à la charte BioForge v4.5 §7 :
- Comparaison obligatoire avec Biopython ET une référence algorithmique minimale
- Mesure du temps et du throughput via pytest-benchmark

Convention de nommage : test_{operation}__{implementation}
pour garantir des résultats interprétables (pas de doublons).

Lancement :
    pytest benchmarks/bench_sequence.py -v
"""

from __future__ import annotations

from typing import Any

import pytest

from bioforge import DnaSequence
from reference.dna import DnaReference

# pytest-benchmark est une dépendance externe sans stubs de typage.
# Conformément à la charte BioForge v4.5 §2, on annote le fixture avec Any.
BenchmarkFixture = Any

# Import conditionnel : les benchmarks sont skippés si Biopython est absent.
Bio = pytest.importorskip("Bio", reason="Biopython requis pour les benchmarks")
from Bio.Seq import Seq

# ============================================================
# Création de séquence
# ============================================================


def test_creation__bioforge(benchmark: BenchmarkFixture, seq_str: str) -> None:
    """Création BioForge (validation + bit-packing upfront)."""
    benchmark(DnaSequence, seq_str)


def test_creation__biopython(benchmark: BenchmarkFixture, seq_str: str) -> None:
    """Création Biopython (stocke la chaîne, pas de validation upfront)."""
    benchmark(Seq, seq_str)


def test_creation__reference(benchmark: BenchmarkFixture, seq_str: str) -> None:
    """Création référence naïve (list de caractères)."""
    benchmark(DnaReference, seq_str)


# ============================================================
# Reverse complement
# ============================================================


def test_reverse_complement__bioforge(
    benchmark: BenchmarkFixture, seq_str_small: str
) -> None:
    """Reverse complement BioForge."""
    seq = DnaSequence(seq_str_small)
    benchmark(seq.reverse_complement)


def test_reverse_complement__biopython(
    benchmark: BenchmarkFixture, seq_str_small: str
) -> None:
    """Reverse complement Biopython."""
    seq = Seq(seq_str_small)
    benchmark(seq.reverse_complement)


def test_reverse_complement__reference(
    benchmark: BenchmarkFixture, seq_str_small: str
) -> None:
    """Reverse complement référence naïve."""
    seq = DnaReference(seq_str_small)
    benchmark(seq.reverse_complement)


# ============================================================
# Conversion en chaîne (décodage complet)
# ============================================================


def test_str_conversion__bioforge(
    benchmark: BenchmarkFixture, seq_str_small: str
) -> None:
    """Conversion str() BioForge (décodage du bit-packing)."""
    seq = DnaSequence(seq_str_small)
    benchmark(str, seq)


def test_str_conversion__biopython(
    benchmark: BenchmarkFixture, seq_str_small: str
) -> None:
    """Conversion str() Biopython."""
    seq = Seq(seq_str_small)
    benchmark(str, seq)


def test_str_conversion__reference(
    benchmark: BenchmarkFixture, seq_str_small: str
) -> None:
    """Conversion to_string() référence naïve."""
    seq = DnaReference(seq_str_small)
    benchmark(seq.to_string)


# ============================================================
# Slicing (fenêtre de 1000 bases au milieu)
# ============================================================


def _slice_middle(seq: Any) -> None:
    """Extrait une fenêtre de 1000 bases au milieu de la séquence.

    Note : `seq` peut être DnaSequence ou Seq (Biopython) ; les deux
    supportent __len__ et __getitem__. Any est utilisé car le type varie.
    """
    mid = len(seq) // 2
    _ = seq[mid : mid + 1000]


def test_slicing__bioforge(benchmark: BenchmarkFixture, seq_str_small: str) -> None:
    """Slicing BioForge (retourne une copie)."""
    seq = DnaSequence(seq_str_small)
    benchmark(_slice_middle, seq)


def test_slicing__biopython(benchmark: BenchmarkFixture, seq_str_small: str) -> None:
    """Slicing Biopython."""
    seq = Seq(seq_str_small)
    benchmark(_slice_middle, seq)
