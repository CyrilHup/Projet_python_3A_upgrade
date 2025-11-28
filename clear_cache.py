#!/usr/bin/env python3
"""
Script de nettoyage des caches du projet.
Exécuter périodiquement pour libérer de l'espace disque.

Usage: python clear_cache.py [--all]
  --all : Supprime aussi le cache de sprites (nécessitera un rechargement plus long)
"""

import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

# Dossiers de cache à nettoyer
CACHE_DIRS = [
    "__pycache__",
    ".pytest_cache",
]

# Dossiers de cache volumineux (optionnel avec --all)
HEAVY_CACHE_DIRS = [
    ".sprite_cache",
]

# Extensions de fichiers cache
CACHE_EXTENSIONS = [".pyc", ".pyo", ".cache", ".pkl", ".pickle"]


def get_size(path: Path) -> int:
    """Retourne la taille d'un fichier ou dossier en bytes."""
    if path.is_file():
        return path.stat().st_size
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            total += child.stat().st_size
    return total


def format_size(size_bytes: int) -> str:
    """Formate une taille en bytes en format lisible."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def clear_pycache(root: Path) -> int:
    """Supprime tous les dossiers __pycache__ récursivement."""
    total_freed = 0
    for cache_dir in root.rglob("__pycache__"):
        if cache_dir.is_dir():
            size = get_size(cache_dir)
            shutil.rmtree(cache_dir, ignore_errors=True)
            total_freed += size
            print(f"  Supprimé: {cache_dir.relative_to(root)} ({format_size(size)})")
    return total_freed


def clear_cache_files(root: Path) -> int:
    """Supprime les fichiers cache par extension."""
    total_freed = 0
    for ext in CACHE_EXTENSIONS:
        for cache_file in root.rglob(f"*{ext}"):
            if cache_file.is_file() and "venv" not in str(cache_file):
                size = cache_file.stat().st_size
                cache_file.unlink()
                total_freed += size
                print(f"  Supprimé: {cache_file.relative_to(root)} ({format_size(size)})")
    return total_freed


def clear_heavy_cache(root: Path) -> int:
    """Supprime les caches volumineux (sprites, etc.)."""
    total_freed = 0
    for dir_name in HEAVY_CACHE_DIRS:
        cache_dir = root / dir_name
        if cache_dir.exists():
            size = get_size(cache_dir)
            shutil.rmtree(cache_dir, ignore_errors=True)
            total_freed += size
            print(f"  Supprimé: {dir_name}/ ({format_size(size)})")
    return total_freed


def main():
    include_heavy = "--all" in sys.argv
    
    print("=" * 50)
    print("🧹 NETTOYAGE DES CACHES DU PROJET")
    print("=" * 50)
    
    total_freed = 0
    
    print("\n📁 Nettoyage des __pycache__...")
    total_freed += clear_pycache(PROJECT_ROOT)
    
    print("\n📄 Nettoyage des fichiers cache...")
    total_freed += clear_cache_files(PROJECT_ROOT)
    
    if include_heavy:
        print("\n💾 Nettoyage des caches volumineux (sprites)...")
        total_freed += clear_heavy_cache(PROJECT_ROOT)
    else:
        # Afficher la taille des caches lourds
        heavy_size = sum(
            get_size(PROJECT_ROOT / d) 
            for d in HEAVY_CACHE_DIRS 
            if (PROJECT_ROOT / d).exists()
        )
        if heavy_size > 0:
            print(f"\n💡 Cache de sprites: {format_size(heavy_size)}")
            print("   Utilisez 'python clear_cache.py --all' pour le supprimer aussi")
    
    print("\n" + "=" * 50)
    print(f"✅ Espace libéré: {format_size(total_freed)}")
    print("=" * 50)


if __name__ == "__main__":
    main()
