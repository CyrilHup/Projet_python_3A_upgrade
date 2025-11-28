import re
import pygame
import os
import time
import pickle
import hashlib
import io
from collections import OrderedDict
from Settings.setup import *

sprites = {}
zoom_cache = {}
MAX_ZOOM_CACHE_PER_SPRITE = 200  # Augmenté pour moins de recalculs
MAX_TOTAL_CACHE_SIZE = 2000  # Limite globale du cache

gui_elements = {}
gui_cache = {}

ASSETS_LOADED = False  # Indique si tout est chargé
# On ajoute deux variables pour le suivi de progression
ASSETS_TOTAL = 1
ASSETS_LOADED_COUNT = 0

# Cache directory for precomputed sprites
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.sprite_cache')
CACHE_VERSION = "v3"  # Increment when sprite processing changes

def ensure_cache_dir():
    """Crée le répertoire de cache s'il n'existe pas."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def get_cache_key(config_hash):
    """Génère un chemin de cache basé sur la configuration."""
    return os.path.join(CACHE_DIR, f"sprites_{config_hash}_{CACHE_VERSION}.cache")

def compute_config_hash():
    """Calcule un hash de la configuration des sprites pour détecter les changements."""
    # Hash basé sur sprite_config, gui_config et les mtimes des fichiers
    config_str = str(sprite_config) + str(gui_config) + str(TILE_SIZE)
    
    # Ajouter les timestamps de modification des fichiers assets
    assets_dir = resolve_asset_path('assets')
    if os.path.exists(assets_dir):
        for root, dirs, files in os.walk(assets_dir):
            for f in sorted(files):
                if f.lower().endswith('webp'):
                    filepath = os.path.join(root, f)
                    try:
                        mtime = os.path.getmtime(filepath)
                        config_str += f"{filepath}:{mtime}"
                    except:
                        pass
    
    return hashlib.md5(config_str.encode()).hexdigest()[:16]

def surface_to_bytes(surface):
    """Convertit une surface pygame en bytes pour la sérialisation."""
    return (pygame.image.tostring(surface, 'RGBA'), surface.get_size())

def bytes_to_surface(data):
    """Reconvertit des bytes en surface pygame."""
    raw_data, size = data
    return pygame.image.fromstring(raw_data, size, 'RGBA').convert_alpha()

def save_sprites_cache(sprites_data, gui_data, cache_path):
    """Sauvegarde les sprites dans le cache."""
    try:
        ensure_cache_dir()
        
        # Convertir les surfaces en bytes
        serializable_sprites = {}
        for category, cat_data in sprites_data.items():
            serializable_sprites[category] = {}
            for name, name_data in cat_data.items():
                if isinstance(name_data, list):
                    serializable_sprites[category][name] = [surface_to_bytes(s) for s in name_data]
                elif isinstance(name_data, dict):
                    serializable_sprites[category][name] = {}
                    for state, state_data in name_data.items():
                        if isinstance(state_data, list):
                            serializable_sprites[category][name][state] = [surface_to_bytes(s) for s in state_data]
                        elif isinstance(state_data, dict):
                            serializable_sprites[category][name][state] = {}
                            for dir_idx, frames in state_data.items():
                                serializable_sprites[category][name][state][dir_idx] = [surface_to_bytes(s) for s in frames]
        
        serializable_gui = {}
        for key, surfaces in gui_data.items():
            serializable_gui[key] = [surface_to_bytes(s) for s in surfaces]
        
        with open(cache_path, 'wb') as f:
            pickle.dump({'sprites': serializable_sprites, 'gui': serializable_gui}, f, pickle.HIGHEST_PROTOCOL)
        
        print(f"Cache saved to {cache_path}")
        return True
    except Exception as e:
        print(f"Failed to save cache: {e}")
        return False

def load_sprites_cache(cache_path):
    """Charge les sprites depuis le cache."""
    try:
        with open(cache_path, 'rb') as f:
            data = pickle.load(f)
        
        loaded_sprites = {}
        for category, cat_data in data['sprites'].items():
            loaded_sprites[category] = {}
            for name, name_data in cat_data.items():
                if isinstance(name_data, list):
                    loaded_sprites[category][name] = [bytes_to_surface(s) for s in name_data]
                elif isinstance(name_data, dict):
                    loaded_sprites[category][name] = {}
                    for state, state_data in name_data.items():
                        if isinstance(state_data, list):
                            loaded_sprites[category][name][state] = [bytes_to_surface(s) for s in state_data]
                        elif isinstance(state_data, dict):
                            loaded_sprites[category][name][state] = {}
                            for dir_idx, frames in state_data.items():
                                loaded_sprites[category][name][state][dir_idx] = [bytes_to_surface(s) for s in frames]
        
        loaded_gui = {}
        for key, surfaces in data['gui'].items():
            loaded_gui[key] = [bytes_to_surface(s) for s in surfaces]
        
        return loaded_sprites, loaded_gui
    except Exception as e:
        print(f"Failed to load cache: {e}")
        return None, None

def get_assets_progress():
    """
    Renvoie un float [0..1] indiquant l'avancement du chargement.
    """
    global ASSETS_LOADED_COUNT, ASSETS_TOTAL
    return min(1.0, ASSETS_LOADED_COUNT / float(ASSETS_TOTAL))

def is_assets_loaded():
    return ASSETS_LOADED

def get_cache_path(filepath, scale, adjust):
    """Génère un chemin de cache unique basé sur le fichier et les paramètres."""
    # Créer une clé unique basée sur le chemin, mtime et paramètres
    try:
        mtime = os.path.getmtime(filepath)
    except:
        mtime = 0
    key = f"{filepath}_{mtime}_{scale}_{adjust}_{CACHE_VERSION}"
    hash_key = hashlib.md5(key.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{hash_key}.cache")

def load_sprite(filepath=None, scale=None, adjust=None):
    if filepath:
        sprite = pygame.image.load(filepath).convert_alpha()
    if scale:
        # Utiliser scale au lieu de smoothscale pour plus de rapidité
        sprite = pygame.transform.scale(sprite, (int(scale[0]), int(scale[1])))
    if adjust:
        sprite = pygame.transform.scale(sprite, (
            int(sprite.get_width() * adjust),
            int(sprite.get_height() * adjust)
        ))
    sprite = sprite.convert_alpha()
    return sprite

def extract_Unitframes(sheet, rows, columns, frames_entity, scale=TILE_SIZE / 400):
    frames = []
    sheet_width, sheet_height = sheet.get_size()
    frame_width = sheet_width // columns
    frame_height = sheet_height // rows
    target_width = int(frame_width * scale)
    target_height = int(frame_height * scale)

    frame_step = columns // frames_entity
    for row in range(rows):
        if row % 2 != 0:
            continue
        for col in range(columns):
            if col % frame_step == 0:
                x = col * frame_width
                y = row * frame_height
                frame = sheet.subsurface(pygame.Rect(x, y, frame_width, frame_height))
                # Utiliser scale au lieu de smoothscale pour plus de rapidité
                frame = pygame.transform.scale(frame, (target_width, target_height))
                frames.append(frame)
    return frames

def extract_Projectileframes(sheet, rows, columns, frames_entity, scale=TILE_SIZE / 400):
    frames = []
    sheet_width, sheet_height = sheet.get_size()
    frame_width = sheet_width // columns
    frame_height = sheet_height // rows
    target_width = int(frame_width * scale)
    target_height = int(frame_height * scale)

    frame_step = columns // frames_entity
    for row in range(rows):
        for col in range(columns):
            if col % frame_step == 0:
                x = col * frame_width
                y = row * frame_height
                frame = sheet.subsurface(pygame.Rect(x, y, frame_width, frame_height))
                # Utiliser scale au lieu de smoothscale pour plus de rapidité
                frame = pygame.transform.scale(frame, (target_width, target_height))
                frames.append(frame)
    return frames

def extract_Buildingframes(sheet, rows, columns, frames_entity, scale=TILE_SIZE / 400):
    frames = []
    sheet_width, sheet_height = sheet.get_size()
    frame_width = sheet_width // columns
    frame_height = sheet_height // rows
    target_width = int(frame_width * scale)
    target_height = int(frame_height * scale)

    frame_step = columns * rows // frames_entity
    # print(f'step {frame_step}, cols : {columns}, frames_entity : {frames_entity}')
    for row in range(rows):
        for col in range(columns):
            index = row * columns + col
            if index % frame_step == 0:
                x = col * frame_width
                y = row * frame_height
                frame = sheet.subsurface(pygame.Rect(x, y, frame_width, frame_height))
                # Utiliser scale au lieu de smoothscale pour plus de rapidité
                frame = pygame.transform.scale(frame, (target_width, target_height))
                frames.append(frame)
    return frames


def draw_progress_bar(screen, progress, screen_width, screen_height, progress_text, loading_screen_image):
    """
    Fonction déjà existante pour dessiner la barre de progression.
    """
    screen.blit(loading_screen_image, (
        screen_width // 2 - loading_screen_image.get_width() // 2,
        screen_height // 2 - loading_screen_image.get_height() // 2
    ))

    bar_width = screen_width * PROGRESS_BAR_WIDTH_RATIO
    bar_x = (screen_width - bar_width) / 2
    bar_y = screen_height * PROGRESS_BAR_Y_RATIO

    pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, BAR_HEIGHT), 2, border_radius=BAR_BORDER_RADIUS)
    pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width * progress, BAR_HEIGHT), border_radius=BAR_BORDER_RADIUS)

    text_color = BLACK if progress >= 0.5 else WHITE

    font = pygame.font.Font(None, 36)
    percentage_text = font.render(f"{int(progress * 100)}%", True, text_color)

    percentage_text_rect = percentage_text.get_rect(center=(bar_x + bar_width / 2, bar_y + BAR_HEIGHT / 2))
    screen.blit(percentage_text, percentage_text_rect)

    progress_text_surface = font.render("Loading " + progress_text, True, WHITE)
    progress_text_rect = progress_text_surface.get_rect(centerx=(bar_x + bar_width / 2), top=(bar_y + BAR_HEIGHT))
    screen.blit(progress_text_surface, progress_text_rect)

    pygame.display.flip()

def resolve_asset_path(relative_path):
    """Helper function to resolve asset paths relative to project root"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, relative_path)

def count_asset_files_fast():
    """Compte rapidement le nombre de fichiers webp sans parcourir tout l'arbre."""
    count = 0
    # Compter les fichiers GUI
    for gui_key, gui_val in gui_config.items():
        directory = gui_val.get('directory')
        if directory:
            abs_dir = resolve_asset_path(directory)
            if os.path.isdir(abs_dir):
                count += len([f for f in os.listdir(abs_dir) if f.lower().endswith('webp')])
    
    # Compter les fichiers de sprites
    for category in sprite_config:
        for sprite_name, value in sprite_config[category].items():
            directory = value['directory']
            abs_dir = resolve_asset_path(directory)
            if os.path.isdir(abs_dir):
                if category in ['resources']:
                    count += len([f for f in os.listdir(abs_dir) if f.lower().endswith('webp')])
                else:
                    # Pour buildings, units, projectiles: compter les sous-dossiers
                    for state_dir in os.listdir(abs_dir):
                        state_path = os.path.join(abs_dir, state_dir)
                        if os.path.isdir(state_path):
                            count += len([f for f in os.listdir(state_path) if f.lower().endswith('webp')])
    return count

def load_sprites(screen, screen_width, screen_height, show_progress=False):
    """
    Chargement complet des sprites (GUI, ressources, unités, bâtiments).
    Utilise un cache sur disque pour accélérer les lancements suivants.
    show_progress=False => on ne dessine pas la barre de progression
                           (chargement en arrière-plan).
    """
    global ASSETS_LOADED, ASSETS_TOTAL, ASSETS_LOADED_COUNT, sprites, gui_elements
    if ASSETS_LOADED:
        return

    ASSETS_LOADED = False
    ASSETS_LOADED_COUNT = 0
    gui_elements.clear()

    # Vérifier si un cache valide existe
    config_hash = compute_config_hash()
    cache_path = get_cache_key(config_hash)
    
    if os.path.exists(cache_path):
        print("Loading sprites from cache...")
        start_time = time.time()
        cached_sprites, cached_gui = load_sprites_cache(cache_path)
        if cached_sprites is not None and cached_gui is not None:
            sprites.update(cached_sprites)
            gui_elements.update(cached_gui)
            ASSETS_LOADED = True
            print(f"Sprites loaded from cache in {time.time() - start_time:.2f}s")
            return
        else:
            print("Cache invalid, reloading sprites...")

    # Comptage rapide des fichiers (évite os.walk complet)
    total_files = count_asset_files_fast()
    ASSETS_TOTAL = max(1, total_files)

    loading_screen = None
    if show_progress:
        try:
            from Controller.init_assets import get_scaled_gui
            pass
        except:
            pass

    # --- CHARGEMENT GUI ---
    for gui_key, gui_val in gui_config.items():
        directory = gui_val.get('directory')
        gui_scale = gui_val.get('scale')
        gui_adjust_scale = gui_val.get('adjust_scale')
        if not directory:
            continue
        gui_elements[gui_key] = []
        
        # Use absolute path for directory
        abs_directory = resolve_asset_path(directory)
        try:
            dir_content = os.listdir(abs_directory)
        except FileNotFoundError:
            print(f"Directory not found: {abs_directory}")
            continue

        for filename in dir_content:
            if filename.lower().endswith("webp"):
                filepath = os.path.join(abs_directory, filename)
                loaded_sprite = load_sprite(filepath, gui_scale, gui_adjust_scale)
                gui_elements[gui_key].append(loaded_sprite)

                ASSETS_LOADED_COUNT += 1
                if show_progress:
                    from Controller.init_assets import draw_progress_bar
                    progress = get_assets_progress()
                    # On récupère l'écran de chargement (scalé) pour l'affichage
                    from Controller.init_assets import get_scaled_gui
                    loading_screen = get_scaled_gui('loading_screen', variant=0, target_height=screen_height)
                    draw_progress_bar(screen, progress, screen_width, screen_height, gui_key, loading_screen)

    # --- CHARGEMENT SPRITES ---
    for category in sprite_config:
        sprites[category] = {}
        for sprite_name, value in sprite_config[category].items():
            directory = value['directory']
            abs_directory = resolve_asset_path(directory)
            scale = value.get('scale')
            adjust = value.get('adjust_scale')
            if 'sheet_config' in value:
                sheet_cols = value['sheet_config'].get('columns', 0)
                sheet_rows = value['sheet_config'].get('rows', 0)

            if category in ['resources']:
                sprites[category][sprite_name] = []
                try:
                    dir_content = os.listdir(abs_directory)
                except FileNotFoundError:
                    print(f"Directory not found: {abs_directory}")
                    continue
                for filename in dir_content:
                    if filename.lower().endswith("webp"):
                        filepath = os.path.join(abs_directory, filename)
                        sprite = load_sprite(filepath, scale, adjust)
                        sprites[category][sprite_name].append(sprite)

                        ASSETS_LOADED_COUNT += 1
                        if show_progress:
                            from Controller.init_assets import draw_progress_bar
                            progress = get_assets_progress()
                            from Controller.init_assets import get_scaled_gui
                            loading_screen = get_scaled_gui('loading_screen', variant=0, target_height=screen_height)
                            draw_progress_bar(screen, progress, screen_width, screen_height, sprite_name, loading_screen)

            elif category == 'buildings':
                sprites[category][sprite_name] = {}
                sprite_path = abs_directory
                if os.path.isdir(sprite_path):
                    state_dirs = os.listdir(sprite_path)
                    for state_dir in state_dirs:
                        state_path = os.path.join(sprite_path, state_dir)
                        if not os.path.isdir(state_path):
                            continue
                        sprites[category][sprite_name].setdefault(state_dir, {})
                        sheets = os.listdir(state_path)
                        for sheetname in sheets:
                            if sheetname.lower().endswith("webp"):
                                filepath = os.path.join(state_path, sheetname)
                                try:
                                    sprite_sheet = load_sprite(filepath, scale, adjust)
                                    if state_dir == 'death':
                                        frames = extract_Buildingframes(
                                            sprite_sheet, sheet_rows, sheet_cols, FRAMES_PER_BUILDING
                                        )
                                    else:
                                        frames = extract_Buildingframes(sprite_sheet, 1, 1, 1)
                                    sprites[category][sprite_name][state_dir] = frames
                                except Exception as e:
                                    print(f"Error loading sprite sheet {filepath}: {e}")

                                ASSETS_LOADED_COUNT += 1
                                if show_progress:
                                    from Controller.init_assets import draw_progress_bar
                                    progress = get_assets_progress()
                                    from Controller.init_assets import get_scaled_gui
                                    loading_screen = get_scaled_gui('loading_screen', variant=0, target_height=screen_height)
                                    draw_progress_bar(screen, progress, screen_width, screen_height, sprite_name, loading_screen)

            elif category == 'units':
                sprites[category][sprite_name] = {}
                sprite_path = abs_directory
                if os.path.isdir(sprite_path):
                    state_dirs = os.listdir(sprite_path)
                    for state_dir in state_dirs:
                        state_path = os.path.join(sprite_path, state_dir)
                        if not os.path.isdir(state_path):
                            continue
                        sprites[category][sprite_name].setdefault(state_dir, {})
                        sheets = os.listdir(state_path)
                        for sheetname in sheets:
                            if sheetname.lower().endswith("webp"):
                                filepath = os.path.join(state_path, sheetname)
                                try:
                                    sprite_sheet = load_sprite(filepath, scale, adjust)
                                    frames = extract_Unitframes(sprite_sheet, sheet_rows, sheet_cols, FRAMES_PER_UNIT)
                                    for direction_index in range(len(frames) // FRAMES_PER_UNIT):
                                        direction_frames = frames[
                                            direction_index * FRAMES_PER_UNIT:
                                            (direction_index + 1) * FRAMES_PER_UNIT
                                        ]
                                        sprites[category][sprite_name][state_dir][direction_index] = direction_frames
                                except Exception as e:
                                    print(f"Error loading sprite sheet {filepath}: {e}")

                                ASSETS_LOADED_COUNT += 1
                                if show_progress:
                                    from Controller.init_assets import draw_progress_bar
                                    progress = get_assets_progress()
                                    from Controller.init_assets import get_scaled_gui
                                    loading_screen = get_scaled_gui('loading_screen', variant=0, target_height=screen_height)
                                    draw_progress_bar(screen, progress, screen_width, screen_height, sprite_name, loading_screen)
            elif category == 'projectiles':
                sprites[category][sprite_name] = {}
                sprite_path = abs_directory
                if os.path.isdir(sprite_path):
                    state_dirs = os.listdir(sprite_path)
                    for state_dir in state_dirs:
                        state_path = os.path.join(sprite_path, state_dir)
                        if not os.path.isdir(state_path):
                            continue
                        sprites[category][sprite_name].setdefault(state_dir, {})
                        sheets = os.listdir(state_path)
                        for sheetname in sheets:
                            if sheetname.lower().endswith("webp"):
                                filepath = os.path.join(state_path, sheetname)
                                try:
                                    sprite_sheet = load_sprite(filepath, scale, adjust)
                                    frames = extract_Projectileframes(sprite_sheet, sheet_rows, sheet_cols, FRAMES_PER_PROJECTILE)
                                    for direction_index in range(len(frames) // FRAMES_PER_PROJECTILE):
                                        direction_frames = frames[
                                            direction_index * FRAMES_PER_PROJECTILE:
                                            (direction_index + 1) * FRAMES_PER_PROJECTILE
                                        ]
                                        sprites[category][sprite_name][state_dir][direction_index] = direction_frames
                                except Exception as e:
                                    print(f"Error loading sprite sheet {filepath}: {e}")

                                ASSETS_LOADED_COUNT += 1
                                if show_progress:
                                    from Controller.init_assets import draw_progress_bar
                                    progress = get_assets_progress()
                                    from Controller.init_assets import get_scaled_gui
                                    loading_screen = get_scaled_gui('loading_screen', variant=0, target_height=screen_height)
                                    draw_progress_bar(screen, progress, screen_width, screen_height, sprite_name, loading_screen)

    ASSETS_LOADED = True
    print("Sprites loaded successfully.")
    
    # Sauvegarder dans le cache pour les prochains lancements
    save_sprites_cache(sprites, gui_elements, cache_path)
    
def get_scaled_sprite(name, category, zoom, state, direction, frame_id, variant):
    # Quantifier le zoom pour réduire les variations de cache (par pas de 0.05)
    quantized_zoom = round(zoom * 20) / 20
    
    if name not in zoom_cache:
        zoom_cache[name] = OrderedDict()
    
    cache_key = (quantized_zoom, state, frame_id, variant, direction)
    if cache_key in zoom_cache[name]:
        zoom_cache[name].move_to_end(cache_key)
        return zoom_cache[name][cache_key]

    if state not in sprites[category][name]:
        state = 'idle'
    try:
        if category == 'buildings':
            frame_id = frame_id % len(sprites[category][name][state])
            original_image = sprites[category][name][state][frame_id]
        elif category == 'units' or category == 'projectiles':
            frame_id = frame_id % len(sprites[category][name][state][direction])
            original_image = sprites[category][name][state][direction][frame_id]
        else:
            original_image = sprites[category][name][variant]
    except IndexError as e:
        raise ValueError(f"Error accessing sprite: {e}")
    
    scaled_width = max(1, int(original_image.get_width() * quantized_zoom))
    scaled_height = max(1, int(original_image.get_height() * quantized_zoom))

    # Utiliser scale au lieu de smoothscale pour plus de rapidité (moins lisse mais plus rapide)
    scaled_image = pygame.transform.scale(original_image, (scaled_width, scaled_height))
    zoom_cache[name][cache_key] = scaled_image
    zoom_cache[name].move_to_end(cache_key)

    if len(zoom_cache[name]) > MAX_ZOOM_CACHE_PER_SPRITE:
        zoom_cache[name].popitem(last=False)
    return scaled_image


def get_scaled_gui(ui_name, variant=0, target_width=None, target_height=None):
    global gui_cache
    key = (ui_name, variant, target_width, target_height)
    if key in gui_cache:
        return gui_cache[key]


    original = gui_elements[ui_name][variant]
    ow, oh = original.get_width(), original.get_height()

    if target_width and not target_height:
        ratio = target_width / ow
        target_height = int(oh * ratio)
    elif target_height and not target_width:
        ratio = target_height / oh
        target_width = int(ow * ratio)
    elif not target_width and not target_height:
        gui_cache[key] = original
        return original  # Add this return statement for consistency

    scaled = pygame.transform.smoothscale(original, (target_width, target_height))
    gui_cache[key] = scaled
    return scaled
