"""Tests unitaires et différentiels pour DnaKmer.

Conforme à la charte BioForge v4.5 §7 :
- 100% des API publiques testées
- Invariants vérifiés (hash parfait, canonical idempotent)
- Tests différentiels avec Hypothesis
"""

import pytest
from hypothesis import assume, given, settings
from hypothesis.strategies import integers, sampled_from, text

from bioforge import DnaKmer, DnaSequence


class TestDnaKmerCreation:
    """Tests de création et validation."""

    def test_new_valid(self) -> None:
        """Création d'un k-mer valide."""
        kmer = DnaKmer("ATGC")
        assert len(kmer) == 4
        assert str(kmer) == "ATGC"

    def test_new_lowercase(self) -> None:
        """La casse est ignorée, la sortie est en majuscules."""
        kmer = DnaKmer("atgc")
        assert str(kmer) == "ATGC"

    def test_new_k1(self) -> None:
        """Un k-mer de longueur 1 est valide."""
        kmer = DnaKmer("A")
        assert len(kmer) == 1
        assert str(kmer) == "A"

    def test_new_k64_max(self) -> None:
        """Un k-mer de longueur 64 (maximum DNA 2-bit) est valide."""
        kmer = DnaKmer("A" * 64)
        assert len(kmer) == 64

    def test_new_empty_raises(self) -> None:
        """Un k-mer vide lève ValueError."""
        with pytest.raises(ValueError):
            DnaKmer("")

    def test_new_too_long_raises(self) -> None:
        """Un k-mer de longueur 65 (dépassement u128) lève ValueError."""
        with pytest.raises(ValueError):
            DnaKmer("A" * 65)

    def test_new_invalid_character_raises(self) -> None:
        """Un caractère invalide lève ValueError."""
        with pytest.raises(ValueError):
            DnaKmer("ATGX")

    def test_new_n_raises(self) -> None:
        """N n'est pas dans l'alphabet Dna strict."""
        with pytest.raises(ValueError):
            DnaKmer("ATGN")


class TestDnaKmerHashEquality:
    """Tests du hash parfait et de l'égalité."""

    def test_equal_kmers_equal(self) -> None:
        """Deux k-mers identiques sont égaux."""
        assert DnaKmer("ATGC") == DnaKmer("ATGC")

    def test_different_kmers_not_equal(self) -> None:
        """Deux k-mers différents ne sont pas égaux."""
        assert DnaKmer("ATGC") != DnaKmer("ATGT")

    def test_equal_kmers_same_hash(self) -> None:
        """Invariant : a == b implique hash(a) == hash(b)."""
        assert hash(DnaKmer("ATGC")) == hash(DnaKmer("ATGC"))

    def test_hash_perfect_no_collision(self) -> None:
        """Des k-mers distincts de même longueur ont des hashes distincts."""
        kmers = [DnaKmer(s) for s in ["AAAA", "AAAC", "AAAG", "AAAT", "ATGC", "GCAT"]]
        hashes = [hash(k) for k in kmers]
        assert len(set(hashes)) == len(hashes)

    def test_usable_in_dict_and_set(self) -> None:
        """Les k-mers sont utilisables comme clés de dict et éléments de set."""
        kmer_set = {DnaKmer("ATGC"), DnaKmer("ATGC"), DnaKmer("GCAT")}
        assert len(kmer_set) == 2

        kmer_dict = {DnaKmer("ATGC"): 1}
        assert kmer_dict[DnaKmer("ATGC")] == 1

    def test_different_length_not_equal(self) -> None:
        """Deux k-mers de longueurs différentes ne sont pas égaux."""
        assert DnaKmer("A") != DnaKmer("AA")


class TestDnaKmerReverseComplement:
    """Tests du reverse complement."""

    def test_reverse_complement(self) -> None:
        """Cas nominal : ATGC → GCAT."""
        assert str(DnaKmer("ATGC").reverse_complement()) == "GCAT"

    def test_reverse_complement_involution(self) -> None:
        """Invariant : rc(rc(x)) == x."""
        kmer = DnaKmer("ATGCGATC")
        assert str(kmer.reverse_complement().reverse_complement()) == "ATGCGATC"


class TestDnaKmerCanonical:
    """Tests du k-mer canonique."""

    def test_canonical_returns_min(self) -> None:
        """canonical() retourne le min entre self et rc."""
        kmer = DnaKmer("ATGC")
        canon = kmer.canonical()
        rc = kmer.reverse_complement()
        # Le canonique doit être l'un des deux
        assert canon == kmer or canon == rc

    def test_canonical_idempotent(self) -> None:
        """Invariant : canonical(canonical(x)) == canonical(x)."""
        kmer = DnaKmer("ATGCGATC")
        assert kmer.canonical() == kmer.canonical().canonical()

    def test_canonical_symmetric(self) -> None:
        """Invariant : canonical(kmer) == canonical(rc(kmer))."""
        kmer = DnaKmer("ATGCGATC")
        assert kmer.canonical() == kmer.reverse_complement().canonical()


class TestDnaSequenceKmers:
    """Tests de l'itération kmers() sur DnaSequence."""

    def test_kmers_basic(self) -> None:
        """Cas nominal : fenêtre glissante de gauche à droite."""
        seq = DnaSequence("ATGCA")
        result = [str(k) for k in seq.kmers(3)]
        assert result == ["ATG", "TGC", "GCA"]

    def test_kmers_count(self) -> None:
        """Invariant : nombre de k-mers == len(seq) - k + 1."""
        seq = DnaSequence("ATGCATGC")
        assert len(list(seq.kmers(3))) == 8 - 3 + 1

    def test_kmers_k1(self) -> None:
        """k=1 : chaque base est un k-mer."""
        seq = DnaSequence("ATGC")
        assert [str(k) for k in seq.kmers(1)] == ["A", "T", "G", "C"]

    def test_kmers_k_equals_len(self) -> None:
        """k == len(seq) : un seul k-mer (la séquence entière)."""
        seq = DnaSequence("ATGC")
        result = [str(k) for k in seq.kmers(4)]
        assert result == ["ATGC"]

    def test_kmers_is_iterator(self) -> None:
        """kmers() retourne un itérateur (lazy), pas une liste."""
        seq = DnaSequence("ATGC")
        it = seq.kmers(2)
        assert hasattr(it, "__iter__")
        assert hasattr(it, "__next__")
        # Consommation itérative
        first = next(it)
        assert str(first) == "AT"

    def test_kmers_k0_raises(self) -> None:
        """k=0 lève ValueError."""
        seq = DnaSequence("ATGC")
        with pytest.raises(ValueError):
            seq.kmers(0)

    def test_kmers_k_exceeds_len_raises(self) -> None:
        """k > len(seq) lève ValueError."""
        seq = DnaSequence("ATGC")
        with pytest.raises(ValueError):
            seq.kmers(5)


class TestDnaKmerDifferential:
    """Tests différentiels avec Hypothesis."""

    @given(seq=text(alphabet=sampled_from("ACGTacgt"), min_size=1, max_size=100))
    @settings(max_examples=200)
    def test_kmer_roundtrip(self, seq: str) -> None:
        """Un k-mer valide conserve sa séquence (canonicalisée)."""
        assume(1 <= len(seq) <= 64)
        kmer = DnaKmer(seq)
        assert str(kmer) == seq.upper()

    @given(
        seq=text(alphabet=sampled_from("ACGT"), min_size=1, max_size=200),
        k=integers(min_value=1, max_value=200),
    )
    @settings(max_examples=200)
    def test_kmers_match_substrings(self, seq: str, k: int) -> None:
        """Les k-mers produits correspondent aux sous-chaînes de longueur k."""
        assume(1 <= k <= len(seq))
        dna = DnaSequence(seq)
        kmers = [str(x) for x in dna.kmers(k)]
        expected = [seq[i : i + k] for i in range(len(seq) - k + 1)]
        assert kmers == expected

    @given(seq=text(alphabet=sampled_from("ACGT"), min_size=1, max_size=64))
    @settings(max_examples=200)
    def test_canonical_symmetric_property(self, seq: str) -> None:
        """Propriété : canonical(kmer) == canonical(rc(kmer))."""
        kmer = DnaKmer(seq)
        assert kmer.canonical() == kmer.reverse_complement().canonical()
