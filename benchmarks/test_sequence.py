"""Benchmarks pour DnaSequence.

Conforme à la charte BioForge v4.4 §7 : comparaison de performance.
"""

from typing import Any

from bioforge import DnaSequence


class TestDnaSequenceBenchmark:
    """Benchmarks de DnaSequence via pytest-benchmark."""

    def test_new_benchmark(self, benchmark: Any) -> None:
        """Benchmark de la création d'une séquence."""
        seq_str = "ATGC" * 10_000  # 40k bases
        benchmark(DnaSequence, seq_str)

    def test_getitem_benchmark(self, benchmark: Any) -> None:
        """Benchmark de l'accès par index."""
        seq = DnaSequence("ATGC" * 10_000)
        benchmark(lambda: [seq[i] for i in range(1_000)])

    def test_reverse_complement_benchmark(self, benchmark: Any) -> None:
        """Benchmark du complément inverse."""
        seq = DnaSequence("ATGC" * 10_000)
        benchmark(seq.reverse_complement)
