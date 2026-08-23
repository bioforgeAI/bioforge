import pytest

from bioforge import DnaSequence


class TestDnaSequence:
    def test_new_valid(self):
        dna = DnaSequence("ATGC")
        assert len(dna) == 4
        assert str(dna) == "ATGC"

    def test_new_invalid(self):
        with pytest.raises(ValueError, match="Invalid symbol"):
            DnaSequence("ATGX")

    def test_getitem(self):
        dna = DnaSequence("ATGC")
        assert dna[0] == "A"
        assert dna[1] == "T"
        assert dna[-1] == "C"
        with pytest.raises(IndexError):
            _ = dna[10]

    def test_slice(self):
        dna = DnaSequence("ATGCATGC")
        assert str(dna[1:5]) == "TGCA"

    def test_reverse_complement(self):
        dna = DnaSequence("ATGC")
        assert str(dna.reverse_complement()) == "GCAT"
        # Invariant: double reverse complement == original
        assert str(dna.reverse_complement().reverse_complement()) == "ATGC"

    def test_to_bytes(self):
        dna = DnaSequence("ATGC")
        # A(00) T(11) G(10) C(01) -> lu de droite à gauche dans l'octet: 01 10 11 00 = 0x6C
        assert dna.to_bytes == b"\x6c"
