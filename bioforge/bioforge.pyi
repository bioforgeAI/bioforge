"""Stub de typage pour le module compilé `bioforge.bioforge` (PyO3).

Ce fichier permet à pyright de typer le module Rust compilé sans pouvoir
l'introspecter directement. Il doit refléter fidèlement l'API exposée
par `src/seq/dna.rs` et `src/seq/iupac.rs`.
"""

from typing import overload

class DnaSequence:
    """Séquence d'ADN stricte (A, C, G, T) encodée sur 2 bits.

    Args:
        seq: Chaîne de caractères représentant l'ADN. Doit contenir
            uniquement A, C, G, T (casse ignorée).

    Raises:
        ValueError: Si `seq` contient un caractère invalide.

    Example:
        >>> dna = DnaSequence("ATGC")
        >>> len(dna)
        4
        >>> str(dna[1:3])
        'TG'
        >>> str(dna.reverse_complement())
        'GCAT'

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

class IupacSequence:
    """Séquence d'ADN avec ambiguïtés IUPAC encodée sur 4 bits.

    Préserve la totalité de l'information IUPAC (15 codes d'ambiguïté).
    Aucune base ambiguë n'est dégradée en N.

    Args:
        seq: Chaîne de caractères représentant l'ADN avec ambiguïtés.
            Alphabet accepté : A C G T N R Y S W K M B D H V
            (casse ignorée).

    Raises:
        ValueError: Si `seq` contient un caractère hors de l'alphabet IUPAC.

    Example:
        >>> iupac = IupacSequence("ATGNRY")
        >>> len(iupac)
        6
        >>> str(iupac)
        'ATGNRY'
        >>> str(iupac.reverse_complement())
        'RYNCAT'

    Invariants:
        - len(self) == len(seq)
        - all(c in "ACGTNRYSWKMBDHV" for c in str(self).upper())
        - str(self.reverse_complement().reverse_complement()) == str(self).upper()
        - Aucune perte d'information : decode(encode(seq)) == canonicalize(seq)
    """

    def __init__(self, seq: str) -> None: ...
    def __len__(self) -> int: ...
    def __str__(self) -> str: ...
    @overload
    def __getitem__(self, index: int) -> str: ...
    @overload
    def __getitem__(self, index: slice) -> IupacSequence: ...
    def reverse_complement(self) -> IupacSequence: ...
