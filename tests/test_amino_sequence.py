"""Tests unitaires et différentiels pour AminoSequence.

Conforme à la charte BioForge v4.5 §7 :
- 100% des API publiques testées
- Invariants vérifiés
- Tests différentiels avec Hypothesis
"""

import pytest
from hypothesis import given, settings
from hypothesis.strategies import sampled_from, text

from bioforge import AminoSequence
from reference.amino import AminoReference


class TestAminoSequenceCreation:
    """Tests de création et validation."""

    def test_new_valid_standard_amino_acids(self) -> None:
        """Création avec les 20 acides aminés standards."""
        seq = AminoSequence("ACDEFGHIKLMNPQRSTVWY")
        assert len(seq) == 20
        assert str(seq) == "ACDEFGHIKLMNPQRSTVWY"

    def test_new_valid_ambiguous_codes(self) -> None:
        """Création avec les codes ambigus B, J, Z."""
        seq = AminoSequence("BJZ")
        assert len(seq) == 3
        assert str(seq) == "BJZ"

    def test_new_valid_special_codes(self) -> None:
        """Création avec les codes spéciaux O, U, X."""
        seq = AminoSequence("OUX")
        assert len(seq) == 3
        assert str(seq) == "OUX"

    def test_new_valid_stop_codon(self) -> None:
        """Création avec le stop codon *."""
        seq = AminoSequence("MKTV*")
        assert len(seq) == 5
        assert str(seq) == "MKTV*"

    def test_new_valid_full_alphabet(self) -> None:
        """Création avec les 27 symboles de l'alphabet protéique."""
        seq = AminoSequence("ACDEFGHIKLMNPQRSTVWYBJZOUX*")
        assert len(seq) == 27
        assert str(seq) == "ACDEFGHIKLMNPQRSTVWYBJZOUX*"

    def test_new_lowercase_canonicalized(self) -> None:
        """Les minuscules sont canonicalisées en majuscules."""
        seq = AminoSequence("acdefghiklmnpqrstvwy")
        assert str(seq) == "ACDEFGHIKLMNPQRSTVWY"

    def test_new_mixed_case_canonicalized(self) -> None:
        """La casse mixte est canonicalisée en majuscules."""
        seq = AminoSequence("AcDeFg")
        assert str(seq) == "ACDEFG"

    def test_stop_codon_case_insensitive(self) -> None:
        """Le stop codon * est insensible à la casse (symbole littéral)."""
        seq = AminoSequence("mktv*")
        assert str(seq) == "MKTV*"

    def test_new_empty(self) -> None:
        """Une séquence vide est valide."""
        seq = AminoSequence("")
        assert len(seq) == 0
        assert str(seq) == ""

    def test_new_invalid_character(self) -> None:
        """Un caractère hors alphabet lève ValueError."""
        with pytest.raises(ValueError, match="Invalid"):
            AminoSequence("MKTX1")

    def test_new_invalid_gap_character(self) -> None:
        """Le caractère '-' (gap) n'est PAS dans l'alphabet protéique."""
        with pytest.raises(ValueError, match="Invalid"):
            AminoSequence("MKT-")

    def test_new_invalid_lowercase_gap(self) -> None:
        """Les caractères non-protéiques en minuscule sont aussi rejetés."""
        with pytest.raises(ValueError, match="Invalid"):
            AminoSequence("mkt-")


class TestAminoSequenceIndexing:
    """Tests d'accès par index."""

    def test_getitem_positive(self) -> None:
        """Accès par index positif."""
        seq = AminoSequence("MKTV")
        assert seq[0] == "M"
        assert seq[1] == "K"
        assert seq[2] == "T"
        assert seq[3] == "V"

    def test_getitem_negative(self) -> None:
        """Accès par index négatif."""
        seq = AminoSequence("MKTV")
        assert seq[-1] == "V"
        assert seq[-2] == "T"
        assert seq[-4] == "M"

    def test_getitem_out_of_bounds(self) -> None:
        """Index hors limites lève IndexError."""
        seq = AminoSequence("MKTV")
        with pytest.raises(IndexError):
            _ = seq[4]
        with pytest.raises(IndexError):
            _ = seq[-5]

    def test_getitem_slice(self) -> None:
        """Le slicing retourne une nouvelle AminoSequence (copie)."""
        seq = AminoSequence("MKTVRQERLK")
        sliced = seq[2:6]
        assert isinstance(sliced, AminoSequence)
        assert str(sliced) == "TVRQ"
        assert len(sliced) == 4

    def test_getitem_slice_empty(self) -> None:
        """Un slice vide retourne une séquence vide."""
        seq = AminoSequence("MKTV")
        sliced = seq[2:2]
        assert len(sliced) == 0

    def test_getitem_stop_codon(self) -> None:
        """Accès au stop codon *."""
        seq = AminoSequence("MKTV*")
        assert seq[4] == "*"
        assert seq[-1] == "*"


class TestAminoSequenceNoReverseComplement:
    """Tests vérifiant l'absence de reverse_complement pour les protéines."""

    def test_no_reverse_complement_method(self) -> None:
        """AminoSequence n'a pas de méthode reverse_complement."""
        seq = AminoSequence("MKTV")
        assert not hasattr(seq, "reverse_complement")

    def test_no_reverse_complement_attribute_error(self) -> None:
        """Tenter d'appeler reverse_complement lève AttributeError.

        On utilise getattr() car l'attribut n'existe pas dans le stub .pyi
        (c'est le comportement attendu : les protéines n'ont pas de complément).
        """
        seq = AminoSequence("MKTV")
        with pytest.raises(AttributeError):
            getattr(seq, "reverse_complement")()  # noqa: B009 — accès dynamique intentionnel


class TestAminoSequenceDifferential:
    """Tests différentiels : AminoSequence vs AminoReference."""

    AMINO_ALPHABET = "ACDEFGHIKLMNPQRSTVWYBJZOUX*"
    AMINO_ALPHABET_WITH_CASE = AMINO_ALPHABET + AMINO_ALPHABET.lower()

    @given(
        seq=text(
            alphabet=sampled_from(AMINO_ALPHABET_WITH_CASE), min_size=0, max_size=500
        )
    )
    @settings(max_examples=300)
    def test_rust_matches_reference_length_and_string(self, seq: str) -> None:
        """Vérifie que la longueur et la représentation string sont identiques."""
        ref = AminoReference(seq)
        rust = AminoSequence(seq)

        assert len(rust) == len(ref)
        assert str(rust) == ref.to_string()

    @given(
        seq=text(
            alphabet=sampled_from(AMINO_ALPHABET_WITH_CASE), min_size=1, max_size=200
        )
    )
    @settings(max_examples=200)
    def test_rust_matches_reference_getitem(self, seq: str) -> None:
        """Vérifie l'accès par index (premier et dernier)."""
        ref = AminoReference(seq)
        rust = AminoSequence(seq)

        assert rust[0] == ref[0]
        assert rust[-1] == ref[-1]

    def test_rust_matches_reference_errors(self) -> None:
        """Vérifie que les erreurs sont levées de manière cohérente."""
        # Caractères invalides
        for bad in ("MKT1", "MKT-", "MKT!", "MKT ", "123"):
            with pytest.raises(ValueError):
                AminoReference(bad)
            with pytest.raises(ValueError):
                AminoSequence(bad)

        # Index hors limites
        ref = AminoReference("M")
        rust = AminoSequence("M")

        with pytest.raises(IndexError):
            _ = ref[1]
        with pytest.raises(IndexError):
            _ = rust[1]
