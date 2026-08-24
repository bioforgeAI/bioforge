"""
Tests unitaires pour DnaSequence.

Conforme à la charte BioForge v4.4 §7 :
- 100% des API publiques testées
- Invariants vérifiés
- Edge cases couverts
"""

import pytest

from bioforge import DnaSequence


class TestDnaSequence:
    """Tests unitaires pour la classe DnaSequence."""

    def test_new_valid(self) -> None:
        """Test de création avec une séquence valide."""
        dna = DnaSequence("ATGC")
        assert len(dna) == 4
        assert str(dna) == "ATGC"

    def test_new_invalid(self) -> None:
        """Test de création avec un caractère invalide."""
        with pytest.raises(ValueError, match="Invalid symbol"):
            DnaSequence("ATGX")

    def test_getitem(self) -> None:
        """Test de l'accès par index (positif et négatif)."""
        dna = DnaSequence("ATGC")
        assert dna[0] == "A"
        assert dna[1] == "T"
        assert dna[-1] == "C"
        with pytest.raises(IndexError):
            _ = dna[10]

    def test_slice(self) -> None:
        """Test du slicing (création d'une copie)."""
        dna = DnaSequence("ATGCATGC")
        assert str(dna[1:5]) == "TGCA"

    def test_reverse_complement(self) -> None:
        """Test du complément inverse."""
        dna = DnaSequence("ATGC")
        assert str(dna.reverse_complement()) == "GCAT"
        # Invariant: double reverse complement == original
        assert str(dna.reverse_complement().reverse_complement()) == "ATGC"
