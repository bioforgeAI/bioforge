# Spécifications des Formats Supportés par BioForge

## FASTQ
- **Variantes supportées** : Illumina (Phred+33), Sanger (Phred+33), Solexa (Phred+64).
- **Non supporté** : SOLiD (encodage différent).
- **Paramètres** :
  - `encoding`: `"phred33"`, `"phred64"`, `"solexa"`, `"auto"` (par défaut).
  - `strict`: `bool = True` (lève `ValueError` si ambigu).

## FASTA
- **Support complet** des en-têtes et séquences multi-lignes.

## VCF/GFF
- **À implémenter** (non prioritaire pour le MVP).
  