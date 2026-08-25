#!/usr/bin/env bash
# Lancer les benchmarks Rust natifs avec l'environnement Python correct.
# Nécessaire car les benchmarks linkent contre libpython (charte v4.5 §7).

set -euo pipefail

# Détection du chemin vers libpython
if [[ -n "${CONDA_PREFIX:-}" ]]; then
    PYTHON_LIB_DIR="$CONDA_PREFIX/lib"
else
    PYTHON_LIB_DIR="$(python -c 'import sysconfig; print(sysconfig.get_config_var("LIBDIR"))')"
fi

echo "Using Python library directory: $PYTHON_LIB_DIR"

# Configuration du dynamic loader selon l'OS
if [[ "$(uname)" == "Darwin" ]]; then
    export DYLD_FALLBACK_LIBRARY_PATH="$PYTHON_LIB_DIR:${DYLD_FALLBACK_LIBRARY_PATH:-}"
else
    export LD_LIBRARY_PATH="$PYTHON_LIB_DIR:${LD_LIBRARY_PATH:-}"
fi

cargo bench "$@"
