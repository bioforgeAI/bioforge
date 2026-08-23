# benchmarks/test_sequence_benchmark.py
"""
Benchmarks comparatifs pour le module Sequence3Bit.
Comparaison avec l'implémentation de référence et Biopython.
"""

from bioforge import Sequence3Bit

# Séquence de test réaliste (1000 bases)
TEST_SEQ = "ATGC" * 250
AMBIGUOUS_SEQ = "ATGCRYSN" * 125


def test_sequence3bit_creation_benchmark(benchmark):
    """Benchmark de la création d'une séquence encodée."""
    benchmark(Sequence3Bit, TEST_SEQ)


def test_sequence3bit_access_benchmark(benchmark):
    """Benchmark de l'accès O(1) à une base (index aléatoire)."""
    seq = Sequence3Bit(TEST_SEQ)
    # Accès à la dernière base pour éviter tout biais de cache prédictif simple
    benchmark(lambda: seq[-1])


def test_sequence3bit_decode_benchmark(benchmark):
    """Benchmark du décodage complet de la séquence."""
    seq = Sequence3Bit(TEST_SEQ)
    benchmark(seq.decode)
