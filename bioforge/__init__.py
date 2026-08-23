# bioforge/__init__.py
from . import bioforge  # Module compilé par maturin

# Ré-exposer Sequence3Bit au niveau racine (optionnel)
Sequence3Bit = bioforge.Sequence3Bit

__all__ = ["Sequence3Bit"]
