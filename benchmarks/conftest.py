"""Fixtures partagées pour les benchmarks.

Conforme à la charte BioForge v4.5 §6 : les séquences sont générées de
manière déterministe (même seed = même séquence) pour la reproductibilité.
"""

from __future__ import annotations

import random

import pytest

# Tailles de séquences à benchmarker (charte §7 : multi-niveaux).
SIZES = [1_000, 10_000, 100_000, 1_000_000]

# Cache pour éviter de régénérer les grandes séquences à chaque test.
_SEQ_CACHE: dict[int, str] = {}


def generate_dna(length: int, seed: int = 42) -> str:
    """Génère une séquence ADN pseudo-aléatoire déterministe.

    Args:
        length: Nombre de bases à générer.
        seed: Graine aléatoire pour la reproductibilité.

    Returns:
        str: Séquence composée uniquement de A/C/G/T.

    Invariants:
        - len(result) == length
        - all(c in "ACGT" for c in result)
        - generate_dna(n, s) == generate_dna(n, s) (déterminisme)
    """
    if length not in _SEQ_CACHE:
        rng = random.Random(seed)
        _SEQ_CACHE[length] = "".join(rng.choices("ACGT", k=length))
    return _SEQ_CACHE[length]


@pytest.fixture(params=SIZES, ids=lambda s: f"{s // 1000}k")
def seq_str(request: pytest.FixtureRequest) -> str:
    """Séquence ADN déterministe, paramétrée par taille (1k → 1M)."""
    return generate_dna(request.param)


@pytest.fixture(params=SIZES[:3], ids=lambda s: f"{s // 1000}k")
def seq_str_small(request: pytest.FixtureRequest) -> str:
    """Séquence ADN pour benchmarks rapides (1k → 100k, exclut 1M)."""
    return generate_dna(request.param)
