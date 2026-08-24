"""Stub de typage pour le module compilé `bioforge.bioforge` (PyO3).

Ce fichier permet à pyright de typer le module Rust compilé sans pouvoir
l'introspecter directement. Il doit refléter fidèlement l'API exposée
par `src/seq/dna.rs`, `src/seq/iupac.rs` et `src/seq/standalone.rs`.
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

def reverse_complement_strict(seq: str) -> str:
    """Retourne le complément inverse d'une séquence ADN stricte (A, C, G, T).

    Version stricte qui rejette toute séquence contenant un caractère
    autre que A, C, G, T (casse ignorée). Pour les séquences avec
    ambiguïtés IUPAC (N, R, Y, etc.), utiliser `reverse_complement_ambiguous`.

    Args:
        seq: Séquence ADN composée uniquement de A, C, G, T (insensible
            à la casse).

    Returns:
        str: La séquence complément inverse, toujours en majuscules.

    Raises:
        ValueError: Si `seq` contient un caractère autre que A/C/G/T
            (y compris N et les codes IUPAC ambigus).

    Example:
        >>> reverse_complement_strict("ATGC")
        'GCAT'
        >>> reverse_complement_strict("atgc")  # casse ignorée
        'GCAT'
        >>> reverse_complement_strict("ATGN")
        Traceback (most recent call last):
            ...
        ValueError: Invalid symbol 'N' at position 3

    Invariants:
        - len(output) == len(input)
        - output est toujours en majuscules
        - reverse_complement_strict(reverse_complement_strict(s)) == s.upper()
        - output ne contient que A/C/G/T
        - "" → ""
    """
    ...

def reverse_complement_ambiguous(seq: str) -> str:
    """Retourne le complément inverse d'une séquence ADN avec ambiguïtés IUPAC.

    Version permissive qui accepte tous les codes IUPAC (A C G T N R Y S
    W K M B D H V) et préserve l'information d'ambiguïté lors du complément.
    Pour une validation stricte A/C/G/T uniquement, utiliser
    `reverse_complement_strict`.

    Table de complément (involution) :
        A↔T  C↔G  N↔N  R↔Y  S↔S  W↔W  K↔M  B↔V  D↔H

    Args:
        seq: Séquence ADN avec ambiguïtés IUPAC (insensible à la casse).
            Alphabet accepté : A C G T N R Y S W K M B D H V.

    Returns:
        str: La séquence complément inverse, toujours en majuscules,
            avec les codes d'ambiguïté préservés.

    Raises:
        ValueError: Si `seq` contient un caractère hors de l'alphabet
            IUPAC (ex: X, -, chiffres, etc.).

    Example:
        >>> reverse_complement_ambiguous("ATGNRY")
        'RYNCAT'
        >>> reverse_complement_ambiguous("WKMBDHV")
        'BDHVKMW'
        >>> reverse_complement_ambiguous("atgn")  # casse ignorée
        'NCAT'

    Invariants:
        - len(output) == len(input)
        - output est toujours en majuscules
        - reverse_complement_ambiguous(reverse_complement_ambiguous(s)) == s.upper()
        - Aucune perte d'information : les codes d'ambiguïté sont transformés
          selon la table IUPAC (pas dégradés en N)
        - output ne contient que des symboles IUPAC valides
        - "" → ""
    """
    ...
