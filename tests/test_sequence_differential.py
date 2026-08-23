# tests/test_sequence_differential.py
"""
Tests différentiels : prouve que l'implémentation Rust se comporte exactement
comme la référence naïve pour toute entrée valide générée par Hypothesis.
"""

import pytest
from hypothesis import given, settings
from hypothesis.strategies import sampled_from, text

from bioforge import Sequence3Bit
from reference.sequence import ReferenceSequence

# Alphabet valide pour la génération Hypothesis (incluant les bases dégradées en N)
DNA_ALPHABET = "ACGTNRYWSKMBDHVacgtnryswskmbdhv"


@given(seq=text(alphabet=sampled_from(DNA_ALPHABET), min_size=0, max_size=1000))
@settings(max_examples=500)
def test_rust_matches_reference_length_and_string(seq: str):
    """Vérifie que la longueur et la représentation string sont identiques."""
    ref = ReferenceSequence(seq)
    rust = Sequence3Bit(seq)

    assert len(rust) == len(ref), f"Length mismatch for seq: {seq[:50]}..."
    assert str(rust) == ref.to_string(), f"String mismatch for seq: {seq[:50]}..."


@given(seq=text(alphabet=sampled_from(DNA_ALPHABET), min_size=1, max_size=500))
@settings(max_examples=500)
def test_rust_matches_reference_getitem(seq: str):
    """Vérifie l'accès par index (positif et négatif) sur toute la séquence."""
    ref = ReferenceSequence(seq)
    rust = Sequence3Bit(seq)

    # Test premier et dernier élément
    assert rust[0] == ref[0]
    assert rust[-1] == ref[-1]

    # Test aléatoire de quelques indices
    import random

    for _ in range(5):
        idx = random.randint(0, len(ref) - 1)
        assert rust[idx] == ref[idx]
        assert rust[-(idx + 1)] == ref[-(idx + 1)]


def test_rust_matches_reference_errors():
    """Vérifie que les erreurs sont levées de manière cohérente."""
    # Caractère invalide
    with pytest.raises(ValueError):
        ReferenceSequence("ATGX")
    with pytest.raises(ValueError):
        Sequence3Bit("ATGX")

    # Index hors limites
    ref = ReferenceSequence("A")
    rust = Sequence3Bit("A")

    with pytest.raises(IndexError):
        _ = ref[1]
    with pytest.raises(IndexError):
        _ = rust[1]
