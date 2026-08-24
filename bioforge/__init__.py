"""
BioForge - Bibliothèque de bioinformatique moderne pour Python.

Architecture inspirée de bio-seq (MIT License).
"""

from .bioforge import (
    DnaSequence,
    IupacSequence,
    reverse_complement_ambiguous,
    reverse_complement_strict,
)

__all__ = [
    "DnaSequence",
    "IupacSequence",
    "reverse_complement_strict",
    "reverse_complement_ambiguous",
]
__version__ = "0.1.0"
