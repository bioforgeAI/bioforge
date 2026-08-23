# reference/sequence.py
"""
Implémentation de référence naïve pour l'encodage 3-bit (2 bases/octet).
CE FICHIER NE DOIT JAMAIS ÊTRE IMPORTÉ DANS src/ OU bioforge/.
Usage autorisé : Uniquement dans les tests de validation (ex: tests/test_sequence_reference.py).
"""

# Mapping conforme à la logique Rust du MVP (A=0, C=1, G=2, T=3, N=4, R=5, Y=6, S=7)
# Les autres bases IUPAC (W, K, M, B, D, H, V) sont dégradées en N (4) pour le MVP.
ENCODE_MAP = {
    "A": 0,
    "a": 0,
    "C": 1,
    "c": 1,
    "G": 2,
    "g": 2,
    "T": 3,
    "t": 3,
    "N": 4,
    "n": 4,
    "R": 5,
    "r": 5,
    "Y": 6,
    "y": 6,
    "S": 7,
    "s": 7,
    "W": 4,
    "w": 4,
    "K": 4,
    "k": 4,
    "M": 4,
    "m": 4,
    "B": 4,
    "b": 4,
    "D": 4,
    "d": 4,
    "H": 4,
    "h": 4,
    "V": 4,
    "v": 4,
}

DECODE_MAP = ["A", "C", "G", "T", "N", "R", "Y", "S"]


def encode_sequence_reference(seq: str) -> list[int]:
    """Encode une séquence en liste d'entiers (0-7) pour validation."""
    result = []
    for char in seq:
        if char not in ENCODE_MAP:
            raise ValueError(f"Invalid character in sequence: {char}")
        result.append(ENCODE_MAP[char])
    return result


def decode_sequence_reference(encoded: list[int]) -> str:
    """Décode une liste d'entiers (0-7) en chaîne de caractères."""
    return "".join(DECODE_MAP[val] for val in encoded)
