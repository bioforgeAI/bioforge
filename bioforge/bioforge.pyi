"""Stub de typage pour le module compilé `bioforge.bioforge` (PyO3).

Ce fichier permet à pyright de typer le module Rust compilé sans pouvoir
l'introspecter directement. Il doit refléter fidèlement l'API exposée
par `src/seq/dna.rs`, `src/seq/iupac.rs`, `src/seq/amino.rs`,
`src/seq/kmer.rs` et `src/seq/standalone.rs`.
"""

from collections.abc import Iterator
from typing import overload

class DnaSequence:
    """Séquence d'ADN stricte (A, C, G, T) encodée sur 2 bits.

    Args:
        seq: Chaîne de caractères représentant l'ADN. Doit contenir
            uniquement A, C, G, T (casse ignorée).

    Raises:
        ValueError: Si `seq` contient un caractère invalide.

    Invariants:
        - len(self) == len(seq)
        - all(c in "ACGT" for c in str(self).upper())
        - str(self.reverse_complement().reverse_complement()) == str(self).upper()
    """

    def __init__(self, seq: str) -> None: ...
    def __len__(self) -> int: ...
    def __str__(self) -> str: ...
    @overload
    def __getitem__(self, index: int) -> str: ...
    @overload
    def __getitem__(self, index: slice) -> DnaSequence: ...
    def reverse_complement(self) -> DnaSequence: ...
    def kmers(self, k: int) -> Iterator[DnaKmer]:
        """Itère sur tous les k-mers de longueur k, de gauche à droite.

        Args:
            k: Longueur des k-mers. Doit être >= 1 et <= len(self).

        Returns:
            Iterator[DnaKmer]: Itérateur paresseux sur les k-mers.

        Raises:
            ValueError: Si k < 1 ou k > len(self).

        Invariants:
            - Nombre de k-mers == len(self) - k + 1
            - Chaque k-mer a une longueur == k
            - L'ordre est déterministe (gauche à droite)
        """
        ...

class IupacSequence:
    """Séquence d'ADN avec ambiguïtés IUPAC encodée sur 4 bits.

    Préserve la totalité de l'information IUPAC (15 codes d'ambiguïté).

    Invariants:
        - len(self) == len(seq)
        - all(c in "ACGTNRYSWKMBDHV" for c in str(self).upper())
        - str(self.reverse_complement().reverse_complement()) == str(self).upper()
    """

    def __init__(self, seq: str) -> None: ...
    def __len__(self) -> int: ...
    def __str__(self) -> str: ...
    @overload
    def __getitem__(self, index: int) -> str: ...
    @overload
    def __getitem__(self, index: slice) -> IupacSequence: ...
    def reverse_complement(self) -> IupacSequence: ...

class AminoSequence:
    """Séquence protéique encodée sur 6 bits par acide aminé.

    Supporte 27 symboles (20 AA standards + B/J/Z + O/U/X + *).

    Invariants:
        - len(self) == len(seq)
        - all(c in "ACDEFGHIKLMNPQRSTVWYBJZOUX*" for c in str(self).upper())
        - Pas de reverse_complement (protéines sans brin complémentaire)
    """

    def __init__(self, seq: str) -> None: ...
    def __len__(self) -> int: ...
    def __str__(self) -> str: ...
    @overload
    def __getitem__(self, index: int) -> str: ...
    @overload
    def __getitem__(self, index: slice) -> AminoSequence: ...

class DnaKmer:
    """Un k-mer d'ADN de longueur fixe, encodé de manière compacte.

    Stockage 2 bits/base dans un registre u128, hashing parfait pour k <= 64.

    Invariants:
        - len(self) == len(seq)
        - 1 <= len(self) <= 64
        - all(c in "ACGT" for c in str(self))
        - (a == b) implique hash(a) == hash(b)
        - canonical() est idempotent
    """

    def __init__(self, seq: str) -> None: ...
    def __len__(self) -> int: ...
    def __str__(self) -> str: ...
    def __hash__(self) -> int: ...
    def __eq__(self, other: object) -> bool: ...
    def reverse_complement(self) -> DnaKmer: ...
    def canonical(self) -> DnaKmer: ...

def reverse_complement_strict(seq: str) -> str:
    """Retourne le complément inverse d'une séquence ADN stricte (A, C, G, T).

    Args:
        seq: Séquence ADN composée uniquement de A, C, G, T.

    Returns:
        str: La séquence complément inverse, en majuscules.

    Raises:
        ValueError: Si `seq` contient un caractère autre que A/C/G/T.

    Invariants:
        - len(output) == len(input)
        - reverse_complement_strict(reverse_complement_strict(s)) == s.upper()
    """
    ...

def reverse_complement_ambiguous(seq: str) -> str:
    """Retourne le complément inverse d'une séquence ADN avec ambiguïtés IUPAC.

    Args:
        seq: Séquence ADN avec ambiguïtés IUPAC (A C G T N R Y S W K M B D H V).

    Returns:
        str: La séquence complément inverse, en majuscules.

    Raises:
        ValueError: Si `seq` contient un caractère hors alphabet IUPAC.

    Invariants:
        - len(output) == len(input)
        - reverse_complement_ambiguous(reverse_complement_ambiguous(s)) == s.upper()
    """
    ...
