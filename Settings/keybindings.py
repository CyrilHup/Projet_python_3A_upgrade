# Settings/keybindings.py
"""
Système de configuration des touches du jeu.
Ce fichier gère les raccourcis clavier et leur personnalisation.
"""

import pygame
import json
import os

# Chemin du fichier de configuration des touches
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYBINDINGS_FILE = os.path.join(BASE_DIR, 'saves', 'keybindings.json')

# Touches par défaut
DEFAULT_KEYBINDINGS = {
    # Navigation caméra
    "camera_up": pygame.K_z,
    "camera_down": pygame.K_s,
    "camera_left": pygame.K_q,
    "camera_right": pygame.K_d,
    "camera_up_alt": pygame.K_UP,
    "camera_down_alt": pygame.K_DOWN,
    "camera_left_alt": pygame.K_LEFT,
    "camera_right_alt": pygame.K_RIGHT,
    
    # Zoom
    "zoom_in": pygame.K_PLUS,
    "zoom_out": pygame.K_MINUS,
    "zoom_global": pygame.K_m,
    
    # Interface
    "pause_menu": pygame.K_ESCAPE,
    "pause_game": pygame.K_p,
    "toggle_gui": pygame.K_F1,
    "toggle_player_info": pygame.K_F2,
    "toggle_health_bars": pygame.K_F3,
    "toggle_all_health_bars": pygame.K_F4,
    "switch_display": pygame.K_F9,
    "toggle_fullscreen": pygame.K_j,
    "cycle_selected_player": pygame.K_TAB,
    
    # Sauvegarde/Chargement
    "save_game": pygame.K_k,
    "save_game_alt": pygame.K_F11,
    "load_game": pygame.K_l,
    "load_game_alt": pygame.K_F12,
    
    # Construction (avec CTRL)
    "build_towncenter": pygame.K_1,
    "build_house": pygame.K_2,
    "build_archeryrange": pygame.K_3,
    "build_barracks": pygame.K_4,
    "build_camp": pygame.K_5,
    "build_keep": pygame.K_7,
    "build_stable": pygame.K_8,
}

# Noms lisibles des actions pour l'interface
ACTION_NAMES = {
    "camera_up": "Caméra Haut",
    "camera_down": "Caméra Bas",
    "camera_left": "Caméra Gauche",
    "camera_right": "Caméra Droite",
    "camera_up_alt": "Caméra Haut (Alt)",
    "camera_down_alt": "Caméra Bas (Alt)",
    "camera_left_alt": "Caméra Gauche (Alt)",
    "camera_right_alt": "Caméra Droite (Alt)",
    "zoom_in": "Zoom +",
    "zoom_out": "Zoom -",
    "zoom_global": "Vue Globale",
    "pause_menu": "Menu Pause",
    "pause_game": "Pause Jeu",
    "toggle_gui": "Afficher/Cacher GUI",
    "toggle_player_info": "Infos Joueur",
    "toggle_health_bars": "Barres de Vie",
    "toggle_all_health_bars": "Toutes Barres de Vie",
    "switch_display": "Changer Affichage",
    "toggle_fullscreen": "Plein Écran",
    "cycle_selected_player": "Changer Joueur (TAB)",
    "save_game": "Sauvegarder",
    "save_game_alt": "Sauvegarder (Alt)",
    "load_game": "Charger",
    "load_game_alt": "Charger (Alt)",
    "build_towncenter": "Construire Centre-Ville",
    "build_house": "Construire Maison",
    "build_archeryrange": "Construire Tir à l'Arc",
    "build_barracks": "Construire Caserne",
    "build_camp": "Construire Camp",
    "build_keep": "Construire Donjon",
    "build_stable": "Construire Écurie",
}

# Catégories d'actions pour l'affichage
ACTION_CATEGORIES = {
    "Navigation": ["camera_up", "camera_down", "camera_left", "camera_right"],
    "Navigation (Alt)": ["camera_up_alt", "camera_down_alt", "camera_left_alt", "camera_right_alt"],
    "Zoom": ["zoom_in", "zoom_out", "zoom_global"],
    "Interface": ["pause_menu", "pause_game", "toggle_gui", "toggle_player_info", 
                  "toggle_health_bars", "toggle_all_health_bars", "toggle_fullscreen", "cycle_selected_player"],
    "Fichiers": ["save_game", "load_game"],
    "Construction": ["build_towncenter", "build_house", "build_archeryrange", 
                     "build_barracks", "build_camp", "build_keep", "build_stable"],
}

# Instance globale des keybindings actuels
current_keybindings = dict(DEFAULT_KEYBINDINGS)


def load_keybindings():
    """Charge les keybindings depuis le fichier JSON."""
    global current_keybindings
    try:
        if os.path.exists(KEYBINDINGS_FILE):
            with open(KEYBINDINGS_FILE, 'r') as f:
                saved_bindings = json.load(f)
                # Mettre à jour avec les valeurs sauvegardées
                for action, key_code in saved_bindings.items():
                    if action in current_keybindings:
                        current_keybindings[action] = key_code
    except Exception as e:
        print(f"Erreur lors du chargement des keybindings: {e}")
        current_keybindings = dict(DEFAULT_KEYBINDINGS)


def save_keybindings():
    """Sauvegarde les keybindings dans le fichier JSON."""
    try:
        os.makedirs(os.path.dirname(KEYBINDINGS_FILE), exist_ok=True)
        with open(KEYBINDINGS_FILE, 'w') as f:
            json.dump(current_keybindings, f, indent=2)
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des keybindings: {e}")
        return False


def reset_keybindings():
    """Réinitialise les keybindings aux valeurs par défaut."""
    global current_keybindings
    current_keybindings = dict(DEFAULT_KEYBINDINGS)
    save_keybindings()


def set_keybinding(action, key_code):
    """Change le keybinding pour une action donnée."""
    global current_keybindings
    if action in current_keybindings:
        current_keybindings[action] = key_code
        save_keybindings()
        return True
    return False


def get_key(action):
    """Retourne le code de touche pour une action."""
    return current_keybindings.get(action, None)


def get_key_name(key_code):
    """Retourne le nom lisible d'une touche."""
    if key_code is None:
        return "Non défini"
    return pygame.key.name(key_code).upper()


def is_key_pressed(action, event_key):
    """Vérifie si la touche pressée correspond à l'action."""
    key = get_key(action)
    if key is None:
        return False
    return event_key == key


# Charger les keybindings au démarrage
load_keybindings()
