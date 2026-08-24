"""Tests différentiels : prouve que l'implémentation Rust (DnaSequence)
se comporte exactement comme la référence naïve (DnaReference) pour toute
entrée valide générée par Hypothesis.

Conforme à la charte BioForge v4.4 §7 : utilisation de hypothesis.
"""

import pytest
from hypothesis import given, settings
from hypothesis.strategies import sampled_from, text

from bioforge import DnaSequence
from reference.dna import DnaReference

# Alphabet strict A/C/G/T (majuscules et minuscules pour tester la canonicalization)
DNA_ALPHABET = "ACGTacgt"


@given(seq=text(alphabet=sampled_from(DNA_ALPHABET), min_size=0, max_size=1000))
@settings(max_examples=500)
def test_rust_matches_reference_length_and_string(seq: str) -> None:
    """Vérifie que la longueur et la représentation string sont identiques."""
    ref = DnaReference(seq)
    rust = DnaSequence(seq)

    assert len(rust) == len(ref)
    assert str(rust) == ref.to_string()


@given(
    seq=text(alphabet=sampled_from(DNA_ALPHABET), min_size=1, max_size=500),
    indices=sampled_from(list(range(-5, 5))),  # indices relatifs, ajustés par le test
)
@settings(max_examples=300)
def test_rust_matches_reference_getitem(seq: str, indices: int) -> None:
    """Vérifie l'accès par index (positif et négatif).

    Utilise une stratégie Hypothesis pour les indices au lieu de random.randint
    afin de garantir la reproductibilité et la minimisation des contre-exemples.
    """
    ref = DnaReference(seq)
    rust = DnaSequence(seq)

    # Ajuste l'index pour qu'il soit valide
    idx = indices % len(ref) if indices >= 0 else indices

    try:
        expected = ref[idx]
    except IndexError:
        with pytest.raises(IndexError):
            _ = rust[idx]
        return

    assert rust[idx] == expected


@given(seq=text(alphabet=sampled_from(DNA_ALPHABET), min_size=0, max_size=200))
@settings(max_examples=200)
def test_reverse_complement_matches_reference(seq: str) -> None:
    """Vérifie que reverse_complement produit le même résultat que la référence.

    Invariant : reverse_complement(reverse_complement(s)) == s.upper()
    """
    ref = DnaReference(seq)
    rust = DnaSequence(seq)

    ref_rc = ref.reverse_complement()
    rust_rc = rust.reverse_complement()

    assert str(rust_rc) == ref_rc.to_string()

    # Invariant d'involution
    if len(rust) > 0:
        assert str(rust_rc.reverse_complement()) == str(rust).upper()


def test_rust_matches_reference_errors() -> None:
    """Vérifie que les erreurs sont levées de manière cohérente."""
    # Caractère invalide (ex: 'X', 'N' qui n'est PAS dans Dna strict)
    for bad in ("ATGX", "ATGN", "ATGW"):
        with pytest.raises(ValueError):
            DnaReference(bad)
        with pytest.raises(ValueError):
            DnaSequence(bad)

    # Index hors limites
    ref = DnaReference("A")
    rust = DnaSequence("A")

    with pytest.raises(IndexError):
        _ = ref[1]
    with pytest.raises(IndexError):
        _ = rust[1]

    with pytest.raises(IndexError):
        _ = ref[-2]
    with pytest.raises(IndexError):
        _ = rust[-2]
