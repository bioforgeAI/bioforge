"""Oracle de référence pour les séquences protéiques.

Implémentation naïve et lisible, indépendante de toute représentation mémoire
(bit-packing, SIMD, etc.). Sert de source de vérité pour le differential testing
conformément à la charte BioForge v4.5 §6.

⚠️ CE FICHIER NE DOIT JAMAIS ÊTRE IMPORTÉ DANS src/ OU bioforge/.
"""

from __future__ import annotations

# Alphabet protéique complet (27 symboles)
_AMINO_ALPHABET = frozenset("ACDEFGHIKLMNPQRSTVWYBJZOUX*")


def _canonicalize(seq: str) -> list[str]:
    """Normalise la séquence : majuscules + validation stricte.

    Args:
        seq: chaîne d'entrée.

    Returns:
        Liste de caractères normalisés.

    Raises:
        ValueError: si un caractère n'appartient pas à l'alphabet protéique.
    """
    result: list[str] = []
    for i, c in enumerate(seq):
        # * est un symbole littéral, pas sensible à la casse
        if c == "*":
            result.append("*")
        else:
            upper = c.upper()
            if upper not in _AMINO_ALPHABET:
                raise ValueError(f"Invalid amino acid symbol '{c}' at position {i}")
            result.append(upper)
    return result


class AminoReference:
    """Oracle naïf pour AminoSequence.

    Invariants:
        - len(self) == len(input)
        - str(self) est en majuscules et contient uniquement des symboles protéiques
        - Pas de reverse_complement (protéines)
    """

    def __init__(self, seq: str) -> None:
        self._symbols: list[str] = _canonicalize(seq)

    def __len__(self) -> int:
        return len(self._symbols)

    def __getitem__(self, index: int) -> str:
        return self._symbols[index]

    def to_string(self) -> str:
        return "".join(self._symbols)
