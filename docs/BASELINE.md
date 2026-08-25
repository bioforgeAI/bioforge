# Baseline de Performance BioForge

**Date** : 2026-08-25
**Commit** : adf256f194aca9b3a1bf2e7f574d3a1a3d4c1e5a
**État** : Implémentation symbole-par-symbole (pré-optimisation Phase 2)
**Machine** : macOS x86_64, CPython 3.12, Rust release (optimized)

> ⚠️ Cette baseline capture l'état AVANT les optimisations Phase 2.
> Toute optimisation Phase 2 devra être comparée à ces chiffres.

---

## 1. Benchmarks Kernels Rust (criterion)

Source : `baseline_kernels.txt`

| Kernel | 1000 | 1001 | 1002 | 1003 | 10000 | 100000 |
|---|---|---|---|---|---|---|
| `encode_dna` | 1.3678 µs | 1.3939 µs | 1.3906 µs | 1.4053 µs | 12.088 µs | 135.03 µs |
| `decode_full_dna` | 1.6448 µs | 1.6049 µs | 1.4943 µs | 1.4839 µs | 13.702 µs | 138.86 µs |
| `get_individual_dna` | 589.44 ns | 585.26 ns | 588.47 ns | 587.86 ns | 5.8327 µs | 58.509 µs |
| `reverse_complement_dna` | 2.6332 µs | 2.6757 µs | 2.6350 µs | 2.6260 µs | 24.872 µs | 247.13 µs |

### Observations clés

- **Couverture `len % 4`** : les tailles 1000/1001/1002/1003 couvrent toutes les classes de reste modulo 4 (0/1/2/3). Les performances sont quasi-identiques entre elles, ce qui confirme que l'implémentation actuelle est insensible à l'alignement (symbole-par-symbole).
- **Scaling linéaire** : le temps scale linéairement avec la taille (~10x pour 10x bases), comme attendu pour une implémentation O(n) symbole-par-symbole.
- **`reverse_complement` est le kernel le plus lent** (~2x `encode`), car il décode puis re-encode symbole par symbole. C'est la cible prioritaire de la Phase 2 (RC bit-natif).

---

## 2. Benchmarks Python (pytest-benchmark)

Source : `baseline_sequence.json`, `baseline_kmers.json`

### Résumé

| Opération | 1k | 10k | 100k | 1000k |
|---|---|---|---|---|
| test_creation__bioforge | 99.76 µs | 928.61 µs | 10.67 ms | 95.20 ms |
| test_creation__biopython | 1.42 µs | 1.58 µs | 4.80 µs | 45.55 µs |
| test_creation__reference | 287.52 µs | 1.45 ms | 13.87 ms | 142.90 ms |
| test_reverse_complement__bioforge | 95.69 µs | 920.77 µs | 9.24 ms | — |
| test_reverse_complement__biopython | 2.00 µs | 12.22 µs | 127.57 µs | — |
| test_reverse_complement__reference | 125.55 µs | 1.17 ms | 14.98 ms | — |
| test_slicing__bioforge | 42.58 µs | 80.90 µs | 83.47 µs | — |
| test_slicing__biopython | 1.27 µs | 1.16 µs | 1.17 µs | — |
| test_str_conversion__bioforge | 41.29 µs | 390.41 µs | 4.02 ms | — |
| test_str_conversion__biopython | 362.30 ns | 1.29 µs | 12.51 µs | — |
| test_str_conversion__reference | 6.98 µs | 66.97 µs | 857.03 µs | — |
| test_kmer_iteration__bioforge_lazy | 9.32 ms | 101.61 ms | 854.88 ms | — |
| test_kmer_iteration__biopython_manual | 598.77 µs | 6.20 ms | 61.58 ms | — |

### Ratios BioForge / Biopython

| Opération | 1k | 10k | 100k | 1000k |
|---|---|---|---|
| Création | 70.3x | 587.7x | 2 223x | 2 090x |
| Reverse complement | 47.8x | 75.3x | 72.4x | — |
| Slicing | 33.5x | 69.7x | 71.3x | — |
| Str conversion | 113.9x | 302.6x | 321.3x | — |
| K-mer iteration | 15.6x | 16.4x | 13.9x | — |

### Analyse des ratios

- **Création (le pire point, 2223x à 100k)** : Biopython `Seq` stocke directement la chaîne sans validation, alors que BioForge bit-pack upfront (validation + encodage). Le vrai coût vient de la **double passe** `char → DnaBase → u8` identifiée par Claude.
- **Str conversion (113-321x)** : BioForge doit décoder du bit-packing vers String, alors que Biopython retourne une chaîne déjà stockée. **Ce n'est pas un bug d'implémentation**, c'est le coût intrinsèque de la représentation compacte (analyse de ChatGPT).
- **Reverse complement (48-75x)** : L'implémentation actuelle décode puis re-encode symbole par symbole. La **preuve algébrique de Claude** montre que `reverse_pairs(b) ^ 0xFF` est exact par octet — c'est la cible prioritaire de la Phase 2.
- **Slicing (34-71x)** : Utilise `get()` dans une boucle pour re-encoder une nouvelle séquence. Même anti-pattern que reverse_complement.
- **K-mer iteration (14-16x)** : Relativement meilleure performance car notre itérateur lazy (O(1) mémoire) est bien conçu. C'est le seul cas où le bit-packing est exploité.

### Cibles prioritaires pour la Phase 2

1. **Reverse complement** : RC bit-natif `reverse_pairs(b) ^ 0xFF` par octet (preuve algébrique Claude)
2. **Création** : Fusion `char → 2bit` en un lookup `[Option<u8>; 128]` + encodage par blocs de 4
3. **Slicing** : Éviter la boucle `get()` en copiant les octets directement avec décalage
4. **Str conversion** : Table de décodage `[[char; 4]; 256]` pour décoder 4 symboles en un load

## 3. Notes

- Les tailles 1001, 1002, 1003 (kernels Rust) couvrent les cas `len % 4 ∈ {1, 2, 3}`.
- Les benchmarks Python utilisent `"ATGC" * N` (toujours multiple de 4), contrairement aux kernels Rust.
- `reverse_complement` et `__getitem__` (slicing) sont les cibles prioritaires de la Phase 2.
- Le harnais criterion est dans `benches/bench_kernels.rs`.