"""Extrait les chiffres clés de baseline_sequence.json pour BASELINE.md.

Usage:
    python scripts/extract_baseline.py baseline_sequence.json
"""

import json
import sys
from collections import defaultdict


def extract_benchmarks(json_path: str) -> None:
    """Extrait et affiche les temps moyens par test et par taille.

    Args:
        json_path: Chemin vers le fichier JSON de pytest-benchmark.
    """
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    # Regroupe par nom de test (ex: test_creation__bioforge)
    results = defaultdict(dict)
    for bench in data["benchmarks"]:
        name = bench["name"]
        # Extrait la taille du paramètre (ex: [1k], [10k], [100k])
        if "[" in name and "]" in name:
            base_name = name.split("[")[0]
            size = name.split("[")[1].rstrip("]")
            # Temps moyen en secondes → conversion en unité lisible
            mean_ns = bench["stats"]["mean"]
            results[base_name][size] = mean_ns

    # Affiche un tableau Markdown
    sizes = ["1k", "10k", "100k", "1000k"]
    print("| Opération | " + " | ".join(sizes) + " |")
    print("|" + "---|" * (len(sizes) + 1))
    for test_name in sorted(results.keys()):
        row = [test_name]
        for size in sizes:
            if size in results[test_name]:
                ns = results[test_name][size]
                row.append(format_time(ns))
            else:
                row.append("—")
        print("| " + " | ".join(row) + " |")


def format_time(seconds: float) -> str:
    """Formate un temps en secondes vers une unité lisible.

    Args:
        seconds: Temps en secondes.

    Returns:
        str: Temps formaté (ns, µs, ms, s).
    """
    if seconds < 1e-6:
        return f"{seconds * 1e9:.2f} ns"
    if seconds < 1e-3:
        return f"{seconds * 1e6:.2f} µs"
    if seconds < 1:
        return f"{seconds * 1e3:.2f} ms"
    return f"{seconds:.2f} s"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/extract_baseline.py <baseline.json>")
        sys.exit(1)
    extract_benchmarks(sys.argv[1])
