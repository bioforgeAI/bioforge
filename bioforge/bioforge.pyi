"""Stub de typage pour le module compilé `bioforge.bioforge` (PyO3).

Ce fichier permet à pyright de typer le module Rust compilé sans pouvoir
l'introspecter directement. Il doit refléter fidèlement l'API exposée
par `src/seq/dna.rs`, `src/seq/iupac.rs`, `src/seq/amino.rs` et
`src/seq/standalone.rs`.
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

class AminoSequence:
    """Séquence protéique encodée sur 6 bits par acide aminé.

    Supporte les 20 acides aminés standards, les codes ambigus (B, J, Z),
    les codes spéciaux (O, U, X) et le stop codon (*).

    Args:
        seq: Chaîne de caractères représentant une séquence protéique.
            Alphabet accepté : A C D E F G H I K L M N P Q R S T V W Y B J Z O U X *
            (casse ignorée, sauf pour * qui est un symbole littéral).

    Raises:
        ValueError: Si `seq` contient un caractère hors de l'alphabet protéique.

    Example:
        >>> protein = AminoSequence(
            "MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG"
            )
        >>> len(protein)
        66
        >>> protein[0]
        'M'
        >>> str(protein[0:10])
        'MKTVRQERLK'

    Invariants:
        - len(self) == len(seq)
        - all(c in "ACDEFGHIKLMNPQRSTVWYBJZOUX*" for c in str(self).upper())
        - Aucune opération de reverse_complement
        - decode(encode(seq)) == canonicalize(seq)
    """

    def __init__(self, seq: str) -> None: ...
    def __len__(self) -> int: ...
    def __str__(self) -> str: ...
    @overload
    def __getitem__(self, index: int) -> str: ...
    @overload
    def __getitem__(self, index: slice) -> AminoSequence: ...

    # Note : Pas de méthode reverse_complement() pour les protéines.

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

    Invariants:
        - len(output) == len(input)
        - output est toujours en majuscules
        - reverse_complement_ambiguous(reverse_complement_ambiguous(s)) == s.upper()
        - Aucune perte d'information IUPAC
        - "" → ""
    """
    ...
