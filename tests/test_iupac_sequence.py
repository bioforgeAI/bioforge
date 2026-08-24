"""Tests unitaires pour IupacSequence.

Conforme à la charte BioForge v4.4 §7 :
- 100% des API publiques testées
- Invariants vérifiés
- Edge cases couverts
"""

import pytest

from bioforge import IupacSequence


class TestIupacSequenceCreation:
    """Tests de création et validation."""

    def test_new_valid_basic(self) -> None:
        """Création avec les 4 bases standard."""
        seq = IupacSequence("ATGC")
        assert len(seq) == 4
        assert str(seq) == "ATGC"

    def test_new_valid_all_iupac(self) -> None:
        """Création avec les 15 symboles IUPAC."""
        seq = IupacSequence("ACGTNRYSWKMBDHV")
        assert len(seq) == 15
        assert str(seq) == "ACGTNRYSWKMBDHV"

    def test_new_lowercase_canonicalized(self) -> None:
        """Les minuscules sont canonicalisées en majuscules."""
        seq = IupacSequence("atgcnryswkmbdhv")
        # L'input "atgc..." devient "ATGC..." (et non "ACGT...")
        assert str(seq) == "ATGCNRYSWKMBDHV"

    def test_new_invalid_character(self) -> None:
        """Un caractère hors alphabet IUPAC lève ValueError."""
        with pytest.raises(ValueError, match="Invalid"):
            IupacSequence("ATGX")

    def test_new_invalid_gap_character(self) -> None:
        """Le caractère '-' (gap) n'est PAS dans l'alphabet IUPAC actuel."""
        with pytest.raises(ValueError, match="Invalid"):
            IupacSequence("ATG-")

    def test_new_empty(self) -> None:
        """Une séquence vide est valide."""
        seq = IupacSequence("")
        assert len(seq) == 0
        assert str(seq) == ""


class TestIupacSequenceNoInformationLoss:
    """Tests critiques : aucune dégradation des bases ambiguës.

    C'est la différence fondamentale avec le prototype 3-bit obsolète
    qui dégradait W/K/M/B/D/H/V en N.
    """

    @pytest.mark.parametrize("symbol", list("WKMBDHV"))
    def test_ambiguous_base_preserved(self, symbol: str) -> None:
        """Chaque base ambiguë est préservée, PAS dégradée en N."""
        seq = IupacSequence(symbol)
        assert str(seq) == symbol
        assert str(seq) != "N"  # Vérification explicite de non-dégradation

    def test_all_ambiguous_preserved_in_context(self) -> None:
        """Les bases ambiguës sont préservées dans un contexte réaliste."""
        input_seq = "ATGWKMBDHVN"
        seq = IupacSequence(input_seq)
        assert str(seq) == input_seq


class TestIupacSequenceIndexing:
    """Tests d'accès par index."""

    def test_getitem_positive(self) -> None:
        """Accès par index positif."""
        seq = IupacSequence("ATGNRY")
        assert seq[0] == "A"
        assert seq[1] == "T"
        assert seq[2] == "G"
        assert seq[3] == "N"
        assert seq[4] == "R"
        assert seq[5] == "Y"

    def test_getitem_negative(self) -> None:
        """Accès par index négatif."""
        seq = IupacSequence("ATGNRY")
        assert seq[-1] == "Y"
        assert seq[-2] == "R"
        assert seq[-6] == "A"

    def test_getitem_out_of_bounds(self) -> None:
        """Index hors limites lève IndexError."""
        seq = IupacSequence("ATGC")
        with pytest.raises(IndexError):
            _ = seq[4]
        with pytest.raises(IndexError):
            _ = seq[-5]

    def test_getitem_slice(self) -> None:
        """Le slicing retourne une nouvelle IupacSequence (copie)."""
        seq = IupacSequence("ATGNRYWK")
        sliced = seq[2:6]
        assert isinstance(sliced, IupacSequence)
        assert str(sliced) == "GNRY"
        assert len(sliced) == 4

    def test_getitem_slice_empty(self) -> None:
        """Un slice vide retourne une séquence vide."""
        seq = IupacSequence("ATGC")
        sliced = seq[2:2]
        assert len(sliced) == 0


class TestIupacSequenceReverseComplement:
    """Tests du complément inverse IUPAC."""

    def test_reverse_complement_basic(self) -> None:
        """Complément inverse des bases standard."""
        seq = IupacSequence("ATGC")
        assert str(seq.reverse_complement()) == "GCAT"

    def test_reverse_complement_ambiguous(self) -> None:
        """Complément inverse avec bases ambiguës.

        Table : R↔Y S↔S W↔W K↔M B↔V D↔H N↔N
        """
        seq = IupacSequence("ATGNRY")
        rc = seq.reverse_complement()
        # Reverse: Y R N G T A
        # Complement: R Y N C A T
        assert str(rc) == "RYNCAT"

    def test_reverse_complement_all_ambiguous(self) -> None:
        """Complément inverse de tous les symboles IUPAC."""
        seq = IupacSequence("ACGTNRYSWKMBDHV")
        rc = seq.reverse_complement()
        # Reverse: V H D B M K W S Y R N T G C A
        # Complement: B D H V K M W S R Y N A C G T
        assert str(rc) == "BDHVKMWSRYNACGT"

    def test_reverse_complement_involution(self) -> None:
        """Invariant : reverse_complement(reverse_complement(s)) == s.upper()."""
        seq = IupacSequence("ATGNRYSWKMBDHV")
        rc2 = seq.reverse_complement().reverse_complement()
        assert str(rc2) == str(seq).upper()

    def test_reverse_complement_empty(self) -> None:
        """Le complément inverse d'une séquence vide est vide."""
        seq = IupacSequence("")
        assert str(seq.reverse_complement()) == ""

    def test_reverse_complement_single_n(self) -> None:
        """N est son propre complément (N ↔ N)."""
        seq = IupacSequence("N")
        assert str(seq.reverse_complement()) == "N"

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
        seq = IupacSequence(symbol)
        assert str(seq.reverse_complement()) == expected_complement
