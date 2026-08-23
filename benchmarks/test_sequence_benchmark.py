# benchmarks/test_sequence_benchmark.py
import pytest

from bioforge import Sequence3Bit
from reference.sequence import ReferenceSequence

# Tailles testées : petite, moyenne, grande
SEQ_SIZES = [100, 10_000, 1_000_000]


def _generate_seq(size: int) -> str:
    return "ATGC" * (size // 4)


@pytest.mark.parametrize("size", SEQ_SIZES)
def test_creation_benchmark(benchmark, size: int):
    seq_str = _generate_seq(size)

    # BioForge
    benchmark(Sequence3Bit, seq_str)


@pytest.mark.parametrize("size", SEQ_SIZES)
def test_access_random_benchmark(benchmark, size: int):
    seq_str = _generate_seq(size)
    rust_seq = Sequence3Bit(seq_str)
    ref_seq = ReferenceSequence(seq_str)

    # On fixe l'index au milieu pour éviter les biais de prédiction de branche extrêmes
    mid_idx = size // 2

    # BioForge
    benchmark(lambda: rust_seq[mid_idx])

    # Référence Python (pour comparer l'overhead de l'API Rust vs Python pur)
    # Note: pytest-benchmark ne compare pas automatiquement, on peut les mettre dans des groupes
    # ou simplement les exécuter pour analyse manuelle des temps relatifs.
    benchmark.pedantic(lambda: ref_seq[mid_idx], iterations=10, rounds=5)


@pytest.mark.parametrize("size", SEQ_SIZES)
def test_decode_benchmark(benchmark, size: int):
    seq_str = _generate_seq(size)
    rust_seq = Sequence3Bit(seq_str)

    benchmark(rust_seq.to_string)
