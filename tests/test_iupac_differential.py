"""Tests différentiels : prouve que IupacSequence (Rust) se comporte
exactement comme IupacReference (Python naïf) pour toute entrée valide.

Conforme à la charte BioForge v4.4 §7 : utilisation de hypothesis.
"""

import pytest
from hypothesis import given, settings
from hypothesis.strategies import sampled_from, text

from bioforge import IupacSequence
from reference.iupac import IupacReference

# Alphabet IUPAC complet (majuscules et minuscules pour tester la canonicalization)
IUPAC_ALPHABET = "ACGTNRYSWKMBDHVacgtnryswkmbdhv"


@given(seq=text(alphabet=sampled_from(IUPAC_ALPHABET), min_size=0, max_size=1000))
@settings(max_examples=500)
def test_rust_matches_reference_length_and_string(seq: str) -> None:
    """Vérifie que la longueur et la représentation string sont identiques."""
    ref = IupacReference(seq)
    rust = IupacSequence(seq)

    assert len(rust) == len(ref)
    assert str(rust) == ref.to_string()


@given(seq=text(alphabet=sampled_from(IUPAC_ALPHABET), min_size=1, max_size=500))
@settings(max_examples=300)
def test_rust_matches_reference_getitem(seq: str) -> None:
    """Vérifie l'accès par index (premier et dernier)."""
    ref = IupacReference(seq)
    rust = IupacSequence(seq)

    assert rust[0] == ref[0]
    assert rust[-1] == ref[-1]


@given(seq=text(alphabet=sampled_from(IUPAC_ALPHABET), min_size=0, max_size=200))
@settings(max_examples=200)
def test_reverse_complement_matches_reference(seq: str) -> None:
    """Vérifie que reverse_complement produit le même résultat que la référence."""
    ref = IupacReference(seq)
    rust = IupacSequence(seq)

    ref_rc = ref.reverse_complement()
    rust_rc = rust.reverse_complement()

    assert str(rust_rc) == ref_rc.to_string()

    # Invariant d'involution
    if len(rust) > 0:
        assert str(rust_rc.reverse_complement()) == str(rust).upper()


def test_rust_matches_reference_errors() -> None:
    """Vérifie que les erreurs sont levées de manière cohérente."""
    # Caractères invalides
    for bad in ("ATGX", "ATG-", "ATG!", "123"):
        with pytest.raises(ValueError):
            IupacReference(bad)
        with pytest.raises(ValueError):
            IupacSequence(bad)

    # Index hors limites
    ref = IupacReference("A")
    rust = IupacSequence("A")

    with pytest.raises(IndexError):
        _ = ref[1]
    with pytest.raises(IndexError):
        _ = rust[1]
