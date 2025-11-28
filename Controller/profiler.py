# Controller/profiler.py
"""
Outil de benchmark pour identifier les goulots d'étranglement.
"""

import time
from collections import defaultdict
from functools import wraps

# Stockage des temps
_timings = defaultdict(list)
_enabled = True
_frame_count = 0
_last_report_time = 0
_report_interval = 5.0  # Rapport toutes les 5 secondes


def enable_profiling(enabled=True):
    """Active ou désactive le profiling."""
    global _enabled
    _enabled = enabled


def reset_profiler():
    """Réinitialise les statistiques."""
    global _timings, _frame_count, _last_report_time
    _timings.clear()
    _frame_count = 0
    _last_report_time = time.time()


class ProfileSection:
    """Context manager pour mesurer une section de code."""
    
    def __init__(self, name):
        self.name = name
        self.start_time = 0
    
    def __enter__(self):
        if _enabled:
            self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, *args):
        if _enabled and self.start_time:
            elapsed = (time.perf_counter() - self.start_time) * 1000  # en ms
            _timings[self.name].append(elapsed)


def profile_function(name=None):
    """Décorateur pour profiler une fonction."""
    def decorator(func):
        func_name = name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not _enabled:
                return func(*args, **kwargs)
            
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            _timings[func_name].append(elapsed)
            return result
        
        return wrapper
    return decorator


def tick_frame():
    """Appelé à chaque frame pour le suivi."""
    global _frame_count, _last_report_time
    _frame_count += 1
    
    current_time = time.time()
    if current_time - _last_report_time >= _report_interval:
        print_report()
        _last_report_time = current_time


def get_stats():
    """Retourne les statistiques actuelles."""
    stats = {}
    for name, times in _timings.items():
        if times:
            stats[name] = {
                'count': len(times),
                'total': sum(times),
                'avg': sum(times) / len(times),
                'min': min(times),
                'max': max(times),
            }
    return stats


def print_report():
    """Affiche un rapport de performance."""
    global _frame_count
    
    if not _timings:
        return
    
    print("\n" + "="*60)
    print("RAPPORT DE PERFORMANCE")
    print("="*60)
    print(f"Frames analysées: {_frame_count}")
    print("-"*60)
    print(f"{'Section':<30} {'Avg(ms)':<10} {'Max(ms)':<10} {'Total%':<10}")
    print("-"*60)
    
    stats = get_stats()
    
    # Calculer le temps total de frame pour les pourcentages
    frame_total = stats.get('frame_total', {}).get('avg', 1)
    
    # Trier par temps moyen décroissant
    sorted_stats = sorted(stats.items(), key=lambda x: x[1]['avg'], reverse=True)
    
    for name, data in sorted_stats[:15]:  # Top 15
        avg = data['avg']
        max_time = data['max']
        pct = (avg / frame_total * 100) if frame_total > 0 else 0
        print(f"{name:<30} {avg:>8.2f}  {max_time:>8.2f}  {pct:>8.1f}%")
    
    print("="*60 + "\n")
    
    # Reset pour la prochaine période
    _timings.clear()
    _frame_count = 0


def get_simple_report():
    """Retourne un rapport simplifié sous forme de string."""
    stats = get_stats()
    if not stats:
        return "Pas de données"
    
    lines = []
    sorted_stats = sorted(stats.items(), key=lambda x: x[1]['avg'], reverse=True)
    
    for name, data in sorted_stats[:5]:
        lines.append(f"{name}: {data['avg']:.1f}ms")
    
    return " | ".join(lines)
