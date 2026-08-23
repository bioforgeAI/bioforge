class Sequence3Bit:
    """Séquence d'ADN encodée en 3-bit.

    L'encodage interne utilise 2 bases par octet (6 bits utiles) pour maximiser la vitesse d'accès aléatoire (O(1))
    tout en réduisant l'empreinte mémoire de 62.5% par rapport à un encodage texte brut.

    **Encodage** :
    - A = 000, C = 001, G = 010, T = 011
    - N = 100, R = 101, Y = 110, S = 111 (les autres ambiguës sont encodées comme N)

    Args:
        seq: Chaîne de caractères représentant l'ADN. Doit contenir uniquement les bases valides :
            A, C, G, T (obligatoires) et N, R, Y, S, W, K, M, B, D, H, V (optionnelles).
            La chaîne est **convertie en majuscules** avant encodage.

    Raises:
        ValueError: Si `seq` contient un caractère invalide.
        IndexError: Si un index est hors limites (dans `__getitem__`).

    Example:
        >>> seq = Sequence3Bit("ATGC")
        >>> seq[0]
        'A'
        >>> seq[-1]
        'C'
        >>> len(seq)
        4
        >>> str(seq)
        'ATGC'
        >>> seq.as_bytes()  # Buffer interne (2 bases/octet)
        b'\\x00\\x01\\x02\\x03'

    Invariants:
        - len(self) == len(seq) pour la séquence d'origine.
        - self[i] in {"A", "C", "G", "T", "N", "R", "Y", "S", "W", "K", "M", "B", "D", "H", "V"} pour tout i valide.
        - str(self) == seq.upper() pour la séquence d'origine (si valide).
        - as_bytes() retourne une copie du buffer interne (modifiable sans effet sur self).
    """

    def __init__(self, seq: str) -> None: ...
    def __getitem__(self, index: int) -> str: ...
    def __len__(self) -> int: ...
    def to_string(self) -> str: ...
    def as_bytes(self) -> bytes: ...
