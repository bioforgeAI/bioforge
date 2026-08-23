# bioforge.pyi
"""
Stubs de typage pour le module compilé Rust de BioForge.
Généré pour correspondre à l'API exposée par PyO3.
"""

class Sequence3Bit:
    """
    Séquence d'ADN encodée de manière compacte (3-bit, 2 bases/octet).

    Invariants:
        - len(seq) == len(canonicalize(input_string))
        - str(seq) == canonicalize(input_string)
    """
    def __init__(self, seq: str) -> None: ...
    def __len__(self) -> int: ...
    def __getitem__(self, index: int) -> str: ...
    def to_string(self) -> str: ...
    def __str__(self) -> str: ...
    def to_bytes(self) -> bytes:
        """Retourne une copie du buffer interne encodé."""
        ...
