# 🗺️ Feuille de Route - Projet RTS Python

> **Focus actuel** : Corrections de bugs, optimisations, refactoring et nettoyage du legacy code
> 
> **Date de création** : 28 Novembre 2025

---

## 📊 Légende

- ⬜ À faire
- 🔄 En cours
- ✅ Terminé
- 🔴 Critique / Bloquant
- 🟠 Important
- 🟢 Nice to have

---

## 🔴 PHASE 1 : BUGS CRITIQUES (Priorité Maximale) ✅ TERMINÉE

> Ces bugs cassent le fonctionnement du jeu ou des bots - Tous corrigés !

### 1.1 Chaînes d'Actions/Décisions des Bots

| # | Tâche | Fichier | Ligne(s) | Statut |
|---|-------|---------|----------|--------|
| 1.1.1 | ✅ Fixer `is_under_attack()` qui retourne une liste mais est utilisé comme booléen | `Controller/Bot.py` | ~413 | ✅ |
| 1.1.2 | ✅ Corriger `search_for_target()` qui crash quand `enemy_team=None` | `Controller/Bot.py` | ~175-180 | ✅ |
| 1.1.3 | ✅ Supprimer la boucle dupliquée dans `manage_battle()` | `Controller/Bot.py` | ~218-225 | ✅ |
| 1.1.4 | ✅ Implémenter `repair_buildings_action()` (actuellement vide avec `pass`) | `Controller/Decisonnode.py` | ~68-70 | ✅ |
| 1.1.5 | ✅ Fixer `reallocate_villagers()` - gestion des resource_type invalides | `Controller/Bot.py` | ~125-130 | ✅ |

### 1.2 Bugs dans les Entités

| # | Tâche | Fichier | Ligne(s) | Statut |
|---|-------|---------|----------|--------|
| 1.2.1 | ✅ Corriger `seekRepair()` - condition inversée `hp < max_hp` → `hp >= max_hp` | `Entity/Unit/Villager.py` | ~139-145 | ✅ |
| 1.2.2 | ✅ Fixer `seekCollect()` - vérifier carry avant passage à 'stock' | `Entity/Unit/Villager.py` | ~86-90 | ✅ |
| 1.2.3 | ✅ Corriger `spawn_trained_unit()` - paramètre team inutile supprimé | `Entity/Building/Building.py` | ~137 | ✅ |
| 1.2.4 | ✅ Supprimer méthode `display_path()` dupliquée | `Entity/Unit/Unit.py` | ~125-135 | ✅ |

### 1.3 Bugs de Synchronisation/État

| # | Tâche | Fichier | Ligne(s) | Statut |
|---|-------|---------|----------|--------|
| 1.3.1 | ✅ Restaurer l'état des bots lors du chargement de sauvegarde | `Controller/game_loop.py` | ~144-150 | ✅ |
| 1.3.2 | ✅ Nettoyer `resources` dict quand une ressource est supprimée | `Models/Map.py` | ~156-160 | ✅ |

---

## ⚡ PHASE 2 : OPTIMISATIONS DE PERFORMANCE ✅ TERMINÉE

> Améliorer les FPS et la réactivité du jeu

### 2.1 Optimisations Critiques

| # | Tâche | Fichier | Impact | Statut |
|---|-------|---------|--------|--------|
| 2.1.1 | ✅ Implémenter spatial hashing/quadtree pour `patch()` | `Models/Map.py` | 🔴 Haute | ✅ |
| 2.1.2 | ✅ Mettre en cache le résultat de `is_under_attack()` avec TTL | `Controller/Bot.py` | 🔴 Haute | ✅ |
| 2.1.3 | ✅ Cache du viewport visible dans `draw_map()` | `Controller/drawing.py` | 🔴 Haute | ✅ |
| 2.1.4 | ✅ Implémenter cache de chemins A* ou D* Lite | `AiUtils/aStar.py` | 🟠 Moyenne | ✅ |
| 2.1.5 | ✅ LRU cache plus intelligent par niveau de zoom | `Controller/init_assets.py` | 🟠 Moyenne | ✅ |

### 2.2 Optimisations Secondaires

| # | Tâche | Description | Statut |
|---|-------|-------------|--------|
| 2.2.1 | ⬜ Utiliser `pygame.sprite.Group` au lieu de sets | Meilleure gestion des sprites | |
| 2.2.2 | ⬜ Batch les appels `blit()` pour sprites similaires | Moins de draw calls | |
| 2.2.3 | ✅ Fonctions de distance optimisées ajoutées | `Controller/utils.py` - distance_squared, is_within_distance | ✅ |
| 2.2.4 | ⬜ Lazy loading des sprites rarement utilisés | Réduction mémoire | |
| 2.2.5 | ⬜ Limiter les updates des entités hors écran | Réduction CPU | |

---

## 🏗️ PHASE 3 : REFACTORING & ARCHITECTURE

> Améliorer la maintenabilité et réduire le code spaghetti

### 3.1 Refactoring du game_state (God Object)

| # | Tâche | Nouveau Module | Statut |
|---|-------|----------------|--------|
| 3.1.1 | ⬜ Extraire `CameraState` du game_state | `Models/CameraState.py` | |
| 3.1.2 | ⬜ Extraire `SelectionState` du game_state | `Models/SelectionState.py` | |
| 3.1.3 | ⬜ Extraire `UIState` du game_state | `Models/UIState.py` | |
| 3.1.4 | ⬜ Extraire `GameplayState` du game_state | `Models/GameplayState.py` | |
| 3.1.5 | ⬜ Créer une classe `GameState` typée regroupant les sous-états | `Models/GameState.py` | |

### 3.2 Découpage des Fichiers Volumineux

| # | Fichier Source | Fichiers Cibles | Statut |
|---|----------------|-----------------|--------|
| 3.2.1 | ⬜ `Controller/Bot.py` (~500 LOC) | `BotEconomy.py`, `BotMilitary.py`, `BotConstruction.py` | |
| 3.2.2 | ⬜ `Controller/event_handler.py` (~450 LOC) | `InputHandler.py`, `MenuHandler.py`, `SelectionHandler.py` | |
| 3.2.3 | ⬜ `Controller/drawing.py` (~300 LOC) | `MapRenderer.py`, `UIRenderer.py`, `EntityRenderer.py` | |

### 3.3 Factorisation du Code Dupliqué

| # | Tâche | Occurrences | Statut |
|---|-------|-------------|--------|
| 3.3.1 | ⬜ Créer `Entity.distance_to(other)` | 15+ endroits | |
| 3.3.2 | ⬜ Créer helpers dans `Team` pour itérer buildings/units | 20+ endroits | |
| 3.3.3 | ⬜ Centraliser conversions tile ↔ screen dans `Camera` | 10+ endroits | |
| 3.3.4 | ⬜ Remplacer `game_state.get('key', default)` par propriétés typées | 50+ endroits | |

### 3.4 Réduction du Couplage

| # | Tâche | Description | Statut |
|---|-------|-------------|--------|
| 3.4.1 | ⬜ Extraire interface `BotBrain` | Injection de dépendances Bot ↔ Team | |
| 3.4.2 | ⬜ Créer dataclasses pour configurations | Remplacer magic numbers dans setup.py | |
| 3.4.3 | ⬜ Restructurer imports en couches | Core → Entity → Controller → UI | |

---

## 🧹 PHASE 4 : NETTOYAGE LEGACY CODE ✅ COMPLÈTE

> Supprimer le code mort et moderniser - Terminé avec dataclasses et type hints

### 4.1 Code Mort à Supprimer

| # | Fichier | Lignes/Description | Statut |
|---|---------|-------------------|--------|
| 4.1.1 | ✅ `Entity/Unit/Villager.py` | Bloc commenté ~120 lignes (`display_hitbox`, `collectResource`, etc.) supprimé | FAIT |
| 4.1.2 | ✅ `Controller/Bot.py` | Code mort `scout_map`, `easy_strategy`, `hard_strategy` (~70 lignes) supprimé | FAIT |
| 4.1.3 | ✅ `Controller/game_loop_backup.py` | Fichier supprimé (812 lignes) | FAIT |
| 4.1.4 | ✅ `Controller/game_loop_optimized.py` | Fichier supprimé (490 lignes doublon) | FAIT |
| 4.1.5 | ✅ `Entity/Unit/Unit.py` | Méthode `display_path` dupliquée supprimée (Phase 1) | FAIT |

### 4.2 Nettoyage Debug/Prints

| # | Tâche | Description | Statut |
|---|-------|-------------|--------|
| 4.2.1 | ✅ Supprimé prints DEBUG | `terminal_display.py` (2 prints DEBUG) | FAIT |
| 4.2.2 | ✅ Supprimé print inutile | `Barracks.py` print("not enough...") | FAIT |
| 4.2.3 | ✅ Supprimé print warning | `Map.py` print(f"Warning: Entity team...") | FAIT |
| 4.2.4 | ℹ️ debug_print() conservés | Système conditionné par `terminal_display_debug.py` - OK | N/A |

### 4.3 Modernisation Python

| # | Tâche | Description | Statut |
|---|-------|-------------|--------|
| 4.3.1 | ✅ Convertir configs en `dataclasses` | setup.py - GameConstants, UnitConstants, MapConfig, MinimapConfig, HealthBarConfig | ✅ |
| 4.3.2 | ✅ Ajouter type hints sur les fonctions principales | Entity.py, Resources.py avec annotations de type complètes | ✅ |
| 4.3.3 | ✅ Utiliser `frozenset` quand collections immuables | Dataclasses frozen=True, Tuple pour VALID_LEVELS/VALID_BOT_MODES | ✅ |
| 4.3.4 | ✅ Ajouter docstrings numpy-style | Documentation des modules Entity.py et Resources.py | ✅ |

---

## 🎮 PHASE 5 : GAMEPLAY & IA (Future)

> Améliorations fonctionnelles après stabilisation

### 5.1 Améliorations de l'IA

| # | Tâche | Description | Statut |
|---|-------|-------------|--------|
| 5.1.1 | ⬜ Implémenter Utility AI | Décisions dynamiques basées sur scores | |
| 5.1.2 | ⬜ Planification économique proactive | Anticiper les besoins en ressources | |
| 5.1.3 | ⬜ Micro-management combat | Kiting, focus fire, formations | |
| 5.1.4 | ⬜ Système d'exploration/scouts | Fog of war | |
| 5.1.5 | ⬜ Coordination multi-bots | Attaques coordonnées | |

### 5.2 Nouvelles Fonctionnalités

| # | Tâche | Description | Statut |
|---|-------|-------------|--------|
| 5.2.1 | ⬜ Formations d'unités | Ligne, carré, triangle | |
| 5.2.2 | ⬜ Points de ralliement | Pour bâtiments de production | |
| 5.2.3 | ⬜ Groupes de contrôle | Ctrl+1..9 pour grouper | |
| 5.2.4 | ⬜ File de production Shift+click | Queue d'entraînement | |
| 5.2.5 | ⬜ Système de recherche/upgrades | Amélioration des unités | |

---

## 🎨 PHASE 6 : INTERFACE UTILISATEUR (Future)

> Améliorations UX après stabilisation

### 6.1 GUI Essentielles

| # | Tâche | Description | Statut |
|---|-------|-------------|--------|
| 6.1.1 | ⬜ Panel d'infos détaillées pour sélection | Stats, coûts, etc. | |
| 6.1.2 | ⬜ Minimap drag-to-pan + alertes | Signaux d'attaque | |
| 6.1.3 | ⬜ Affichage trends ressources | +/- avec alertes pénurie | |
| 6.1.4 | ⬜ File de notifications persistante | Remplacer timer 3s | |
| 6.1.5 | ⬜ Hotkeys configurables | Menu d'options | |

### 6.2 Feedback Visuel

| # | Tâche | Description | Statut |
|---|-------|-------------|--------|
| 6.2.1 | ⬜ Indicateurs de dégâts flottants | Nombres au-dessus des entités | |
| 6.2.2 | ⬜ Cercles de sélection sous unités | Meilleure visibilité | |
| 6.2.3 | ⬜ Visualisation zones de contrôle | Territoire des joueurs | |
| 6.2.4 | ⬜ Animation construction progressive | Bâtiments se construisant | |
| 6.2.5 | ⬜ Système audio | Sons manquants | |

---

## 📈 ORDRE D'EXÉCUTION OPTIMAL

```
SEMAINE 1-2 : Phase 1 (Bugs Critiques)
├── 1.1.1 → 1.1.4 (Bots)
├── 1.2.1 → 1.2.3 (Entités)
└── 1.3.1 → 1.3.2 (Sync)

SEMAINE 2-3 : Phase 4.1-4.2 (Nettoyage Code Mort)
├── Supprimer fichiers/code mort
└── Nettoyer debug prints

SEMAINE 3-4 : Phase 2.1 (Optim Critiques)
├── 2.1.1 Spatial hashing
├── 2.1.2 Cache is_under_attack
└── 2.1.3 Cache viewport

SEMAINE 4-6 : Phase 3.1-3.2 (Refactoring Majeur)
├── Découper game_state
└── Découper gros fichiers

SEMAINE 6-7 : Phase 2.2 + 3.3-3.4 (Optim + Factorisation)
├── Optimisations secondaires
└── Factoriser code dupliqué

SEMAINE 7-8 : Phase 4.3 (Modernisation)
├── Type hints
├── Dataclasses
└── Documentation

APRÈS STABILISATION : Phases 5-6 (Features)
├── Améliorations IA
├── Nouvelles features gameplay
└── Améliorations UI
```

---

## 🔧 OUTILS & COMMANDES UTILES

### Profiling
```bash
# Profiler le jeu
python -m cProfile -o profile.stats main.py
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(30)"

# Profiler en temps réel
pip install py-spy
py-spy top -- python main.py
```

### Linting & Type Checking
```bash
# Installation
pip install ruff mypy

# Linting
ruff check .

# Type checking
mypy Controller/ Entity/ Models/ --ignore-missing-imports
```

### Tests
```bash
pip install pytest pytest-cov
pytest tests/ -v --cov=.
```

---

## 📝 NOTES

- Toujours tester après chaque modification de la Phase 1
- Faire des commits atomiques par tâche
- Mettre à jour ce fichier au fur et à mesure (changer ⬜ → ✅)
- Si un bug bloque, documenter le workaround ici

---

*Dernière mise à jour : 28/11/2025*
