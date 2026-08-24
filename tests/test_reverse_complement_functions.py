"""Tests unitaires et différentiels pour les fonctions standalone
reverse_complement_strict et reverse_complement_ambiguous.

Conforme à la charte BioForge v4.4 §6 et §7 :
- Fonctions distinctes (pas de boolean trap)
- 100% des API publiques testées
- Tests différentiels avec Hypothesis
"""

import pytest
from hypothesis import given, settings
from hypothesis.strategies import sampled_from, text

from bioforge import (
    DnaSequence,
    IupacSequence,
    reverse_complement_ambiguous,
    reverse_complement_strict,
)


class TestReverseComplementStrict:
    """Tests unitaires pour reverse_complement_strict."""

    def test_basic(self) -> None:
        """Cas nominal : ATGC → GCAT."""
        assert reverse_complement_strict("ATGC") == "GCAT"

    def test_lowercase(self) -> None:
        """La casse est ignorée, la sortie est en majuscules."""
        assert reverse_complement_strict("atgc") == "GCAT"
        assert reverse_complement_strict("AtGc") == "GCAT"

    def test_empty(self) -> None:
        """Une séquence vide retourne une séquence vide."""
        assert reverse_complement_strict("") == ""

    def test_single_base(self) -> None:
        """Complément d'une seule base."""
        assert reverse_complement_strict("A") == "T"
        assert reverse_complement_strict("T") == "A"
        assert reverse_complement_strict("C") == "G"
        assert reverse_complement_strict("G") == "C"

    def test_rejects_n(self) -> None:
        """N est rejeté par la version stricte."""
        with pytest.raises(ValueError, match="Invalid"):
            reverse_complement_strict("ATGN")

    def test_rejects_ambiguous_codes(self) -> None:
        """Tous les codes IUPAC ambigus sont rejetés."""
        for symbol in "RYSWKMBDHV":
            with pytest.raises(ValueError, match="Invalid"):
                reverse_complement_strict(f"ATG{symbol}")

    def test_rejects_invalid_characters(self) -> None:
        """Les caractères non-biologiques sont rejetés."""
        for bad in ("ATGX", "ATG-", "ATG1", "ATG ", "ATG!"):
            with pytest.raises(ValueError, match="Invalid"):
                reverse_complement_strict(bad)

    def test_involution(self) -> None:
        """Invariant : f(f(s)) == s.upper()."""
        seq = "ATGCGATTAGC"
        assert reverse_complement_strict(reverse_complement_strict(seq)) == seq.upper()


class TestReverseComplementAmbiguous:
    """Tests unitaires pour reverse_complement_ambiguous."""

    def test_basic(self) -> None:
        """Cas nominal avec bases standard."""
        assert reverse_complement_ambiguous("ATGC") == "GCAT"

    def test_with_n(self) -> None:
        """N est accepté et préservé (N ↔ N)."""
        assert reverse_complement_ambiguous("ATGN") == "NCAT"
        assert reverse_complement_ambiguous("N") == "N"

    def test_with_ambiguous_codes(self) -> None:
        """Les codes IUPAC ambigus sont acceptés et complémentés correctement."""
        assert reverse_complement_ambiguous("ATGNRY") == "RYNCAT"

    def test_all_ambiguous_codes(self) -> None:
        """Vérification exhaustive de la table de complément IUPAC."""
        result = reverse_complement_ambiguous("ACGTNRYSWKMBDHV")
        # Reverse: V H D B M K W S Y R N T G C A
        # Complement: B D H V K M W S R Y N A C G T
        assert result == "BDHVKMWSRYNACGT"

    def test_lowercase(self) -> None:
        """La casse est ignorée, la sortie est en majuscules."""
        assert reverse_complement_ambiguous("atgn") == "NCAT"
        assert reverse_complement_ambiguous("wkmbdhv") == "BDHVKMW"

    def test_empty(self) -> None:
        """Une séquence vide retourne une séquence vide."""
        assert reverse_complement_ambiguous("") == ""

    def test_rejects_invalid_characters(self) -> None:
        """Les caractères hors IUPAC sont rejetés."""
        for bad in ("ATGX", "ATG-", "ATG1", "ATG!", "ATG "):
            with pytest.raises(ValueError, match="Invalid"):
                reverse_complement_ambiguous(bad)

    def test_involution(self) -> None:
        """Invariant : f(f(s)) == s.upper()."""
        seq = "ATGNRYSWKMBDHV"
        assert (
            reverse_complement_ambiguous(reverse_complement_ambiguous(seq))
            == seq.upper()
        )

    @pytest.mark.parametrize(
        "symbol,expected_complement",
        [
            ("A", "T"),
            ("T", "A"),
            ("C", "G"),
            ("G", "C"),
            ("N", "N"),
            ("R", "Y"),
            ("Y", "R"),
            ("S", "S"),
            ("W", "W"),
            ("K", "M"),
            ("M", "K"),
            ("B", "V"),
            ("V", "B"),
            ("D", "H"),
            ("H", "D"),
        ],
    )
    def test_complement_table_exhaustive(
        self, symbol: str, expected_complement: str
    ) -> None:
        """Vérification exhaustive de la table de complément IUPAC."""
        assert reverse_complement_ambiguous(symbol) == expected_complement


class TestDifferentialVsClasses:
    """Tests différentiels : les fonctions standalone doivent produire
    exactement le même résultat que les classes DnaSequence/IupacSequence.
    """

    @given(seq=text(alphabet=sampled_from("ACGTacgt"), min_size=0, max_size=500))
    @settings(max_examples=300)
    def test_strict_matches_dna_sequence(self, seq: str) -> None:
        """reverse_complement_strict(s) == str(DnaSequence(s).reverse_complement())."""
        func_result = reverse_complement_strict(seq)
        class_result = str(DnaSequence(seq).reverse_complement())
        assert func_result == class_result

    @given(
        seq=text(
            alphabet=sampled_from("ACGTNRYSWKMBDHVacgtnryswkmbdhv"),
            min_size=0,
            max_size=500,
        )
    )
    @settings(max_examples=300)
    def test_ambiguous_matches_iupac_sequence(self, seq: str) -> None:
        """reverse_complement_ambiguous(s) ==
        str(IupacSequence(s).reverse_complement())."""
        func_result = reverse_complement_ambiguous(seq)
        class_result = str(IupacSequence(seq).reverse_complement())
        assert func_result == class_result

    @given(seq=text(alphabet=sampled_from("ACGTacgt"), min_size=0, max_size=200))
    @settings(max_examples=100)
    def test_strict_involution_property(self, seq: str) -> None:
        """Propriété : f(f(s)) == s.upper() pour toute séquence ADN valide."""
        assert reverse_complement_strict(reverse_complement_strict(seq)) == seq.upper()

    @given(
        seq=text(
            alphabet=sampled_from("ACGTNRYSWKMBDHVacgtnryswkmbdhv"),
            min_size=0,
            max_size=200,
        )
    )
    @settings(max_examples=100)
    def test_ambiguous_involution_property(self, seq: str) -> None:
        """Propriété : f(f(s)) == s.upper() pour toute séquence IUPAC valide."""
        assert (
            reverse_complement_ambiguous(reverse_complement_ambiguous(seq))
            == seq.upper()
        )
