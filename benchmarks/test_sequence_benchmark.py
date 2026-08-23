# benchmarks/test_sequence_benchmark.py
from typing import Any

import pytest

from bioforge import Sequence3Bit
from reference.sequence import ReferenceSequence

# Tailles testées : petite, moyenne, grande
SEQ_SIZES = [100, 10_000, 1_000_000]


def _generate_seq(size: int) -> str:
    return "ATGC" * (size // 4)


@pytest.mark.parametrize("size", SEQ_SIZES)
def test_creation_benchmark(benchmark: Any, size: int) -> None:
    """Benchmark de la création d'une séquence encodée (BioForge)."""
    seq_str = _generate_seq(size)
    benchmark(Sequence3Bit, seq_str)


@pytest.mark.parametrize("size", SEQ_SIZES)
def test_access_benchmark_bioforge(benchmark: Any, size: int) -> None:
    """Benchmark de l'accès O(1) à une base (BioForge)."""
    seq_str = _generate_seq(size)
    rust_seq = Sequence3Bit(seq_str)
    mid_idx = size // 2
    benchmark(lambda: rust_seq[mid_idx])


@pytest.mark.parametrize("size", SEQ_SIZES)
def test_access_benchmark_reference(benchmark: Any, size: int) -> None:
    """Benchmark de l'accès O(1) à une base (Référence Python) pour comparaison."""
    seq_str = _generate_seq(size)
    ref_seq = ReferenceSequence(seq_str)
    mid_idx = size // 2
    benchmark(lambda: ref_seq[mid_idx])


@pytest.mark.parametrize("size", SEQ_SIZES)
def test_decode_benchmark(benchmark: Any, size: int) -> None:
    """Benchmark du décodage complet de la séquence (BioForge)."""
    seq_str = _generate_seq(size)
    rust_seq = Sequence3Bit(seq_str)
    benchmark(rust_seq.to_string)
