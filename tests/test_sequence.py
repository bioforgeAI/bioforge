import pytest

from bioforge import Sequence3Bit


class TestSequence3Bit:
    def test_new_valid_sequence(self):
        seq = Sequence3Bit("ATGC")
        assert len(seq) == 4
        assert str(seq) == "ATGC"

    def test_new_invalid_character(self):
        with pytest.raises(ValueError, match="Invalid character"):
            Sequence3Bit("ATGX")

    def test_new_ambiguous_bases(self):
        seq = Sequence3Bit("RYSWKMBDHV")
        assert str(seq) == "RYSNNNNNNN"  # W,K,M,B,D,H,V → N

    def test_getitem(self):
        seq = Sequence3Bit("ATGC")
        assert seq[0] == "A"
        assert seq[-1] == "C"
        with pytest.raises(IndexError):
            _ = seq[10]

    def test_to_bytes(self):
        seq = Sequence3Bit("ATGC")
        # ✅ Correction : to_bytes est maintenant une méthode, il faut l'appeler avec ()
        assert seq.to_bytes() == b"\x03\x11"  # A=000, T=011 → 0x03; G=010, C=001 → 0x11
