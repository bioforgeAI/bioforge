"""Oracle de référence pour les séquences IUPAC (ADN avec ambiguïtés).

Implémentation naïve préservant la totalité de l'information IUPAC (4-bit).
Contrairement au prototype 3-bit, aucune base ambiguë n'est dégradée en N.

⚠️ CE FICHIER NE DOIT JAMAIS ÊTRE IMPORTÉ DANS src/ OU bioforge/.
"""

from __future__ import annotations

_IUPAC_ALPHABET = frozenset("ACGTNRYSWKMBDHV")

# Table de complément IUPAC complète (involution)
# A↔T, C↔G, R↔Y, S↔S, W↔W, K↔M, B↔V, D↔H, N↔N
_COMPLEMENT_TABLE = str.maketrans(
    "ACGTNRYSWKMBDHV",  # source : 15 symboles IUPAC
    "TGCANYRSWMKVHDB",  # cible : compléments correspondants
)


def _canonicalize(seq: str) -> list[str]:
    """Normalise la séquence : majuscules + validation IUPAC stricte."""
    result: list[str] = []
    for i, c in enumerate(seq):
        upper = c.upper()
        if upper not in _IUPAC_ALPHABET:
            raise ValueError(f"Invalid IUPAC symbol '{c}' at position {i}")
        result.append(upper)
    return result


class IupacReference:
    """Oracle naïf pour IupacSequence.

    Invariants:
        - len(self) == len(input)
        - str(self) est en majuscules et contient uniquement des symboles IUPAC
        - Aucune ambiguïté n'est perdue (contrairement au prototype 3-bit)
        - reverse_complement(reverse_complement(s)) == s
    """

    def __init__(self, seq: str) -> None:
        self._symbols: list[str] = _canonicalize(seq)

    def __len__(self) -> int:
        return len(self._symbols)

    def __getitem__(self, index: int) -> str:
        return self._symbols[index]

    def to_string(self) -> str:
        return "".join(self._symbols)

    def reverse_complement(self) -> IupacReference:
        """Retourne le complément inverse avec la table IUPAC complète."""
        reversed_seq = "".join(reversed(self._symbols))
        complemented = reversed_seq.translate(_COMPLEMENT_TABLE)
        return IupacReference(complemented)
