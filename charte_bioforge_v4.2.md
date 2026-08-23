# Charte d'Ingénierie BioForge (v4.2) - Norme de Production
Ce document définit les règles strictes, binaires et scientifiquement rigoureuses pour le développement de BioForge. Toute génération de code par une IA doit s'y conformer. Le non-respect de ces règles invalide la génération.
## 1. Environnement, Stack et Workflow
- **Python** : 3.12+ minimum (avec conscience de la compatibilité free-threaded 3.13+). Utiliser les fonctionnalités natives de typage (`type Alias = ...`, `def func[T](x: T)`).
- **Rust** : Édition 2021, avec un MSRV (Minimum Supported Rust Version) de 1.70.0 (compatible avec PyO3 0.20+) explicitement défini dans `Cargo.toml` :
```toml
[package]
edition = "2021"
rust-version = "1.70.0"
```
- **Workflow "API First" (Obligatoire)** : Avant toute implémentation, l'IA doit proposer les signatures (stubs Python avec docstrings Google + section `Invariants`, et stubs Rust `#[pyfunction]` avec `#[pyo3(signature)]` retournant `PyResult`). L'implémentation n'est générée qu'après validation humaine de cette interface sémantique.
- **Représentation Canonique des Types** : Un type de donnée ne doit être défini qu'une seule fois. Son emplacement est dicté par des critères quantitatifs :
    - *Hot-path data* (>100 000 instances ou boucles critiques, ex: `Sequence`, `FastqRecord`) → Struct Rust native (`#[pyclass]`) ou `@dataclass(frozen=True, slots=True)` en Python.
    - *Configuration / Frontières externes* (<10 000 instances) → `pydantic` en Python.

## 2. Qualité du Code Python (Frontend)
- **Typage Strict** : 100% du code doit passer `pyright` en mode `strict`. `# type: ignore[...]` est autorisé **UNIQUEMENT** pour les dépendances externes non typées ou bugs avérés, avec un commentaire explicatif obligatoire.
- **Linting** : `ruff check` et `ruff format` sans aucune erreur.
- **Docstrings** : Format Google obligatoire (`Args`, `Returns`, `Raises`, `Example`). Doit inclure une section **`Invariants`** listant les propriétés mathématiques/logiques toujours vraies (ex: `len(output) == len(input)`).
- **Architecture (SRP Pragmatique)** : Un module = un concept. Une fonction = une responsabilité logique unique. L'extraction artificielle de fonctions sans valeur sémantique est interdite.
- **Usage de Pydantic** : Réservé aux objets de configuration ou aux frontières externes. Interdit dans les structures du "hot path" (ex: parsing de millions de records).

## 3. Qualité du Code Rust (Backend)
- Sécurité Mémoire & GIL :
    - **INTERDICTION FORMELLE** de `.unwrap()` ou `.expect()` en production (`src/`). Utiliser l'opérateur `?`.
    - **Libération du GIL et Rayon** : Tout calcul Rust long ou parallèle doit être exécuté dans un bloc `py.allow_threads(|| { ... })`, où `py` est une référence à Python (premier argument d'une `#[pyfunction]`).
    - **Zéro PyO3 dans Rayon** : Il est **STRICTEMENT INTERDIT** d'utiliser n'importe quel objet PyO3 (`PyObject`, `Py<T>`, `Bound<T>`, `Python`, etc.) ou `Python::with_gil` à l'intérieur des closures `rayon`. Seuls les types Rust natifs (`Vec<T>`, `&[T]`, `T` où `T: Send + Sync`) sont autorisés.
    - **Déterminisme avec Rayon** : Les opérations parallèles DOIVENT être déterministes.
        - ✅ Déterministe (ordre conservé) : `data.into_par_iter().map(|x| x * 2).collect()`
        - ✅ Déterministe (avec index) : `data.indexed_par_iter().map(|(i, x)| (i, x * 2)).collect()`
        - ❌ Non déterministe (interdit si l'ordre compte) : `data.par_iter().map(|x| x * 2).collect()`
        - ✅ Autorisé (ordre sans importance) : `data.par_iter().map(|x| x * 2).sum()`
    - **Gestion des Buffers (Ownership Explicite)** : Les buffers Python (`PyBuffer`) doivent être soit utilisés immédiatement (emprunt temporaire), soit explicitement possédés (`to_vec()`, `Arc<[u8]>`). **Interdiction formelle** de stocker une référence brute (`&[u8]`) à un `PyBuffer` dans une structure Rust au-delà de la durée de vie de l'appel.
- **Gestion des Erreurs** : Toute erreur DOIT être définie dans une `enum` avec `thiserror`. L'implémentation de `From<BioForgeError> for PyErr` DOIT mapper **explicitement et exhaustivement** TOUTES les variantes vers une exception Python.
    - *Exemple de mapping exhaustif* :
        ```rust
        #[derive(thiserror::Error, Debug)]
        pub enum BioForgeError {
            #[error("Invalid FASTQ format: {0}")]
            FastqParseError(String),
            #[error("Invalid sequence: {0}")]
            SequenceError(String),
            #[error("IO error")]
            IoError(#[from] std::io::Error),
        }
        impl From<BioForgeError> for PyErr {
            fn from(err: BioForgeError) -> Self {
                match err {
                    BioForgeError::FastqParseError(msg) => PyValueError::new_err(msg),
                    BioForgeError::SequenceError(msg) => PyTypeError::new_err(msg),
                    BioForgeError::IoError(e) => PyIOError::new_err(e.to_string()),
                    // Clippy échouera si une variante est oubliée ici
                }
            }
        }
        ```
- **Documentation & Linting** : Tout item public en Rust DOIT avoir une docstring (`///`) avec Description, Arguments, Returns, Errors. Le code doit passer `cargo fmt` et `cargo clippy -- -D warnings` (avec lints `pedantic`). Les `#[allow(...)]` sont autorisés de manière localisée avec une justification technique stricte.

## 4. Gestion de la Mémoire et des Données
- Données Tabulaires : `polars` en Rust est **AUTORISÉ** pour les opérations internes sur des données tabulaires, mais **INTERDIT** comme type exposé en Python. Les données DOIVENT être converties en types natifs (ex: `Vec<Record>`) avant de traverser la frontière Python.
- **Encodage des Séquences (3-bit par défaut pour le MVP)** :
    - **Règle** : Utiliser l’implémentation **2 bases par octet (6 bits utilisés, 2 bits perdus)** pour le MVP.
    - *Justification* : Simplicité (pas de gestion de chevauchement), performance (accès O(1) trivial) et maintenabilité. La version compacte (sans gaspillage) est réservée à une optimisation future uniquement si des benchmarks montrent un gain mémoire >20% sans perte de performance.
    - *Implémentation MVP obligatoire* :
        ```rust
        let octet_idx = i / 2;
        let shift = 4 * (i % 2); // 0 ou 4
        let bits = (data[octet_idx] >> shift) & 0b111;
        ```
    - *Règle de documentation* : Tout module doit documenter la version utilisée (ex: `// Encodage: 2 bases/octet`).
- **Encapsulation Python** : Les vues mémoire provenant de Rust DOIVENT être encapsulées dans des classes Python sûres (ex: `Sequence3Bit`) exposant une API propre (`__getitem__`, `__len__`). L'accès direct à la mémoire brute est interdit.

## 5. Gestion des Dépendances
- **Python Core** : `pyarrow`, `numpy`, `pydantic`. (Optionnel : `polars`, `httpx`, `rich`). Dev : `pytest`, `pytest-benchmark`, `pytest-regressions`, `hypothesis`, `ruff`, `pyright`.
- **Rust Core** : `pyo3`, `thiserror`, `serde`, `flate2`. (Optionnel : `rayon`).
- **Reproductibilité** : Utiliser un gestionnaire de lockfile (ex: `uv` ou `poetry`) pour garantir la résolution exacte. Les contraintes dans `pyproject.toml` doivent être des plages raisonnables (ex: `pydantic>=2.0,<3.0`).
- **Règle Biopython** : BioForge ne dépend **jamais** de Biopython à l'exécution. Biopython est autorisé **uniquement** comme oracle de validation, implémentation de référence ou dans les benchmarks différentiels.

## 6. Spécificités Bioinformatiques (Rigueur Scientifique)
- **Référence Scientifique & Implémentation de Référence** : Tout algorithme non trivial doit avoir une source bibliographique identifiable. Une implémentation de référence naïve mais correcte DOIT exister dans un dossier `reference/` (ex: `reference/alignment.py`) pour valider la correction des versions optimisées via les tests.
    - **Règles strictes pour `reference/`** : Interdiction absolue d'importer tout fichier de `reference/` dans `src/` ou `bioforge/`. Usage autorisé **uniquement** dans les tests. Une vérification CI doit échouer si un tel import est détecté (ex: `grep -r "from reference" src/ bioforge/`).
- **Déterminisme** : Même entrée + mêmes paramètres = même résultat, indépendamment du degré de parallélisme, sauf comportement non déterministe explicitement documenté.
- **Formats et Encodages** : Un fichier `FORMAT_SPEC.md` doit lister les variantes supportées.
    - **FASTQ** : Le paramètre `encoding` doit être explicite (`"phred33"`, `"phred64"`, `"solexa"`, `"auto"`). Le mode `"auto"` est une heuristique. Le paramètre `strict: bool = True` (par défaut) DOIT lever une `ValueError` si l'offset est ambigu.
- **Manipulation de Séquences** : `reverse_complement_strict` (lève `ValueError` si autre que A/C/G/T) et `reverse_complement_ambiguous` (gère N, R, Y, etc.) doivent être des fonctions distinctes.
- **Gestion du Doute (`NotImplementedError`)** : INTERDIT dans les chemins de code concrets de production (`src/`). Autorisé uniquement dans les classes abstraites/protocoles ou les tests. S'il est utilisé, il DOIT être accompagné d'un `TODO(@responsable, YYYY-MM-DD)`, suivi par le label GitHub `spec-verification-required`, et faire échouer la CI s'il est détecté dans `src/`.

## 7. Tests et Validation (Exigence de Preuve)
- **Couverture et Propriétés** : 100% des API publiques doivent avoir au moins un test couvrant les invariants et les edge cases. L'utilisation de `hypothesis` (property-based testing) est **fortement recommandée**.
- **Benchmarks Multi-Niveaux** : Comparaison obligatoire avec Biopython ET une référence algorithmique minimale. Mesurer : temps, throughput, ET mémoire.
    - **Version de Biopython pour les benchmarks** : Version figée à `biopython==1.84.0`. Stockée dans `benchmarks/requirements.txt`. Mise à jour uniquement après validation manuelle.
- **Smoke Test de Benchmark (CI Standard)** : Jeu de données : Fichier FASTQ de 1000 reads. Métriques : Temps (médiane sur 3 runs) et Mémoire (peak RSS). Seuils d'échec : > 2x le temps de Biopython OU > 1.5x la mémoire de Biopython.
- **Tests de Mémoire** : AddressSanitizer (ASan) et LeakSanitizer (LSan) sont **obligatoires** dans la CI standard. `Miri` est optionnel, utilisé **uniquement** si le projet contient du code `unsafe`.
- **Tests de Régression** : Les algorithmes complexes DOIVENT utiliser `pytest-regressions`.
