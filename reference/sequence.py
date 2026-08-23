# reference/sequence.py
"""
Implémentation de référence naïve et transparente pour la séquence ADN.
CE FICHIER NE DOIT JAMAIS ÊTRE IMPORTÉ DANS src/ OU bioforge/.
Usage autorisé : Uniquement dans les tests différentiels (tests/test_sequence_differential.py).
"""

# Dictionnaire de canonicalisation explicite (conforme à la logique Rust MVP)
_CANONICAL_MAP: dict[str, str] = {
    "A": "A",
    "C": "C",
    "G": "G",
    "T": "T",
    "N": "N",
    "R": "R",
    "Y": "Y",
    "S": "S",
    # Dégradation des bases IUPAC complexes en 'N' pour le MVP
    "W": "N",
    "K": "N",
    "M": "N",
    "B": "N",
    "D": "N",
    "H": "N",
    "V": "N",
}


def canonicalize(seq: str) -> str:
    """Normalise la séquence : majuscules + dégradation des bases ambiguës complexes en 'N'."""
    result: list[str] = []
    for char in seq:
        upper_char = char.upper()
        if upper_char not in _CANONICAL_MAP:
            raise ValueError(f"Invalid character in sequence: '{char}'")
        result.append(_CANONICAL_MAP[upper_char])
    return "".join(result)


class ReferenceSequence:
    """Oracle de comportement naïf pour valider l'implémentation Rust."""

    def __init__(self, seq: str) -> None:
        # On stocke en liste de strings pour un accès O(1) naïf et transparent
        self._symbols: list[str] = list(canonicalize(seq))

    def __len__(self) -> int:
        return len(self._symbols)

    def __getitem__(self, index: int) -> str:
        idx = index
        if idx < 0:
            idx += len(self._symbols)

        if idx < 0 or idx >= len(self._symbols):
            raise IndexError(
                f"Index out of bounds: {index} (length: {len(self._symbols)})"
            )

        return self._symbols[idx]

    def to_string(self) -> str:
        return "".join(self._symbols)

    def to_bytes(self) -> bytes:
        """Retourne une représentation bytes naïve (pour comparaison conceptuelle, pas bit-à-bit)."""
        return self.to_string().encode("ascii")
