# Path: Controller/game_loop_optimized.py
# Version optimisée et nettoyée du game_loop

from Settings.setup import user_choices
import time
import pygame
import os
import Controller.ui_theme as theme

from Controller.Bot import Bot
from Models.Map import GameMap
from Entity.Building import *
from Entity.Unit import *
from Models.Team import Team
from Controller.camera import Camera
from Controller.terminal_display_debug import debug_print
from Controller.drawing import (
    draw_map,
    compute_map_bounds,
    create_minimap_background,
    display_fps,
    generate_team_colors,
    draw_pointer,
    draw_gui_elements,
    draw_minimap_viewport
)
from Controller.event_handler import handle_events
from Controller.update import update_game_state, handle_camera
from Controller.gui import (
    create_player_selection_surface,
    create_player_info_surface,
    get_scaled_gui,
    get_centered_rect_in_bottom_right,
    update_minimap_elements,
    draw_pause_menu,
    draw_options_menu
)
from Controller.utils import tile_to_screen
from Settings.setup import (
    HALF_TILE_SIZE,
    MINIMAP_MARGIN,
    GAME_SPEED,
    PANEL_RATIO,
    BG_RATIO,
    ONE_SECOND,
    FPS_DRAW_LIMITER,
    DPS,
    SAVE_DIRECTORY
)
from Settings.sync import TEMP_SAVE_PATH
from Controller.sync_manager import check_and_load_sync
from Controller.profiler import ProfileSection, tick_frame, print_report


def is_player_dead(player):
    """Vérifie si un joueur est éliminé."""
    if not player.units and not player.buildings:
        if player.resources.food <= 50 and player.resources.gold <= 225:
            return True
    return False


def draw_game_over_overlay(screen, game_state):
    """Affiche l'écran de game over."""
    # Overlay
    overlay = pygame.Surface((game_state['screen_width'], game_state['screen_height']), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))

    text = theme.FONT_TITLE.render(f"Joueur {game_state['winner_id']} est gagnant!", True, theme.COLOR_ACCENT)
    text_rect = text.get_rect(center=(game_state['screen_width'] // 2, game_state['screen_height'] // 2 - 80))
    screen.blit(text, text_rect)

    mx, my = pygame.mouse.get_pos()

    # Bouton Quitter
    button_rect = pygame.Rect(0, 0, 250, 50)
    button_rect.center = (game_state['screen_width'] // 2, game_state['screen_height'] // 2 + 20)
    is_quit_hovered = button_rect.collidepoint(mx, my)
    theme.draw_button(screen, button_rect, "Quitter le jeu", is_hovered=is_quit_hovered, color_normal=theme.COLOR_DANGER, color_hover=(220, 100, 100))
    game_state['game_over_button_rect'] = button_rect

    # Bouton Menu Principal
    main_menu_rect = pygame.Rect(0, 0, 250, 50)
    main_menu_rect.center = (game_state['screen_width'] // 2, game_state['screen_height'] // 2 + 90)
    is_menu_hovered = main_menu_rect.collidepoint(mx, my)
    theme.draw_button(screen, main_menu_rect, "Menu Principal", is_hovered=is_menu_hovered)
    game_state['main_menu_button_rect'] = main_menu_rect


def initialize_gui_elements(screen_width, screen_height, game_map):
    """Initialise tous les éléments GUI (minimap, panels, etc.)."""
    panel_width = int(screen_width * PANEL_RATIO)
    panel_height = int(screen_height * PANEL_RATIO)
    
    minimap_panel_sprite = get_scaled_gui('minimapPanel', 0, target_width=panel_width)
    minimap_panel_rect = get_centered_rect_in_bottom_right(
        panel_width, panel_height, screen_width, screen_height, MINIMAP_MARGIN
    )

    bg_width = int(screen_width * BG_RATIO)
    bg_height = int(screen_height * BG_RATIO)
    
    (minimap_background_surface, minimap_scale, minimap_offset_x, 
     minimap_offset_y, minimap_min_iso_x, minimap_min_iso_y) = create_minimap_background(
        game_map, bg_width, bg_height
    )

    minimap_background_rect = minimap_background_surface.get_rect()
    minimap_background_rect.center = minimap_panel_rect.center
    minimap_background_rect.y -= panel_height / 50
    minimap_background_rect.x += panel_width / 18
    
    minimap_entities_surface = pygame.Surface(
        (minimap_background_rect.width, minimap_background_rect.height),
        pygame.SRCALPHA
    )
    minimap_entities_surface.fill((0, 0, 0, 0))

    return {
        'minimap_panel_sprite': minimap_panel_sprite,
        'minimap_panel_rect': minimap_panel_rect,
        'minimap_background': minimap_background_surface,
        'minimap_background_rect': minimap_background_rect,
        'minimap_entities_surface': minimap_entities_surface,
        'minimap_scale': minimap_scale,
        'minimap_offset_x': minimap_offset_x,
        'minimap_offset_y': minimap_offset_y,
        'minimap_min_iso_x': minimap_min_iso_x,
        'minimap_min_iso_y': minimap_min_iso_y,
    }


def create_game_state(screen, screen_width, screen_height, game_map, players, camera, team_colors, gui_elements):
    """Crée le dictionnaire game_state initial."""
    return {
        'camera': camera,
        'players': players,
        'selected_player': players[0] if players else None,
        'team_colors': team_colors,
        'game_map': game_map,
        'screen_width': screen_width,
        'screen_height': screen_height,
        'screen': screen,
        'fullscreen': False,
        'minimap_dragging': False,
        'player_selection_updated': True,
        'player_info_updated': True,
        'selected_entities': [],
        'selecting_entities': False,
        'selection_start': None,
        'selection_end': None,
        'rectangle_additive': False,
        'paused': False,
        'force_full_redraw': True,
        'show_all_health_bars': False,
        'show_player_info': True,
        'show_gui_elements': True,
        'return_to_menu': False,
        'pause_menu_active': False,
        'options_menu_active': False,
        'notification_message': "",
        'notification_start_time': 0.0,
        'players_target': [None for _ in range(len(players))],
        'old_resources': {p.teamID: p.resources.copy() for p in players},
        'switch_display': False,
        'force_sync': False,
        **gui_elements  # Ajoute tous les éléments GUI
    }


def create_bots(players, game_map, bot_modes=None):
    """Crée les bots pour chaque joueur."""
    if bot_modes is None:
        bot_modes = ['economique'] * len(players)
    
    # S'assurer que bot_modes a la bonne taille
    while len(bot_modes) < len(players):
        bot_modes.append('economique')
    bot_modes = bot_modes[:len(players)]
    
    bots = []
    for i, (player, mode) in enumerate(zip(players, bot_modes)):
        player.teamID = i
        for unit in player.units:
            unit.team = i
        for building in player.buildings:
            building.team = i
        bot = Bot(player, game_map, players, mode, difficulty='medium')
        bots.append(bot)
    
    return bots, bot_modes


def load_temp_save_if_exists(game_map, game_state):
    """Charge une sauvegarde temporaire si elle existe."""
    if not os.path.exists(TEMP_SAVE_PATH):
        return False
    
    try:
        # Sauvegarder l'état GUI actuel
        old_gui_state = {
            'screen': game_state.get('screen'),
            'screen_width': game_state.get('screen_width'),
            'screen_height': game_state.get('screen_height'),
        }
        
        game_map.load_map(TEMP_SAVE_PATH)
        
        # Mettre à jour game_state
        players = game_map.players
        game_state['players'] = players
        game_state['selected_player'] = players[0] if players else None
        
        # Restaurer players_target depuis la sauvegarde (déjà converti par Map.load_map)
        saved_players_target = game_map.game_state.get('players_target')
        if saved_players_target and len(saved_players_target) == len(players):
            game_state['players_target'] = saved_players_target
        else:
            game_state['players_target'] = [None for _ in range(len(players))]
        
        game_state['team_colors'] = generate_team_colors(len(players))
        game_state['old_resources'] = {p.teamID: p.resources.copy() for p in players}
        game_state['force_full_redraw'] = True
        game_state['player_selection_updated'] = True
        game_state['player_info_updated'] = True
        
        # Restaurer l'état GUI
        game_state.update(old_gui_state)
        
        os.remove(TEMP_SAVE_PATH)
        return True
    except Exception as e:
        debug_print(f"Erreur chargement temp save: {e}")
        if os.path.exists(TEMP_SAVE_PATH):
            os.remove(TEMP_SAVE_PATH)
        return False


def game_loop(screen, game_map, screen_width, screen_height, players):
    """Boucle de jeu principale optimisée."""
    
    # Configuration initiale
    current_mode = user_choices.get("index_terminal_display", 2)
    is_terminal_only = current_mode == 1
    is_switching = user_choices.get("menu_result") == "switch_display"
    
    # Protection dimensions
    if screen_width <= 0 or screen_height <= 0:
        screen_width, screen_height = 800, 600

    # Initialisation pygame si nécessaire
    if is_switching and not is_terminal_only:
        if not pygame.display.get_init():
            pygame.init()
            screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
        pygame.mouse.set_visible(False)
        pygame.font.init()
        from Controller.init_assets import load_sprites, is_assets_loaded
        if not is_assets_loaded():
            load_sprites(screen, screen_width, screen_height, show_progress=True)

    # Initialisation clock et font
    clock = None
    font = None
    if not is_terminal_only:
        clock = pygame.time.Clock()
        pygame.key.set_repeat(0, 0)
        pygame.mouse.set_visible(False)
        pygame.font.init()
        font = pygame.font.SysFont(None, 24)

    # Initialisation caméra
    camera = Camera(screen_width, screen_height)
    team_colors = generate_team_colors(len(players))
    
    min_iso_x, max_iso_x, min_iso_y, max_iso_y = compute_map_bounds(game_map)
    camera.set_bounds(min_iso_x, max_iso_x, min_iso_y, max_iso_y)
    
    map_width = max_iso_x - min_iso_x
    map_height = max_iso_y - min_iso_y
    camera.min_zoom = min(screen_width / float(map_width), screen_height / float(map_height))
    camera.zoom_out_to_global()

    # Initialisation GUI
    gui_elements = initialize_gui_elements(screen_width, screen_height, game_map)
    
    # Création game_state
    game_state = create_game_state(
        screen, screen_width, screen_height, game_map, 
        players, camera, team_colors, gui_elements
    )
    game_map.set_game_state(game_state)

    # Chargement sauvegarde temporaire (une seule fois!)
    if os.path.exists(TEMP_SAVE_PATH) and not is_switching:
        load_temp_save_if_exists(game_map, game_state)
        players = game_state['players']

    # Création des bots
    bot_modes = game_map.game_state.get('bot_modes', ['economique'] * len(players))
    bots, bot_modes = create_bots(players, game_map, bot_modes)
    game_map.game_state['bot_modes'] = bot_modes

    # Variables de timing
    player_selection_surface = None
    player_info_surface = None
    running = True
    update_counter = 0
    draw_timer = 0
    bot_update_timer = 0
    bot_update_interval = 1.0 / DPS
    last_time = time.time()
    
    # Pré-calcul du target FPS
    target_fps = min(120, FPS_DRAW_LIMITER * 2)  # Cap à 120 FPS max

    # ==================== BOUCLE PRINCIPALE ====================
    while running:
        # with ProfileSection('frame_total'):
        if True:
            current_time = time.time()
            
            # Calcul delta time
            if not is_terminal_only:
                raw_dt = clock.tick(target_fps) / ONE_SECOND
            else:
                raw_dt = current_time - last_time
                last_time = current_time
                time.sleep(0.01)

            dt = 0 if game_state['paused'] else raw_dt * GAME_SPEED

            # Mise à jour des bots (avec timer)
            if not game_state['paused']:
                bot_update_timer += dt
                if bot_update_timer >= bot_update_interval:
                    # with ProfileSection('bot_update'):
                    if True:
                        for bot in bots:
                            bot.update(game_map, bot_update_interval)
                    bot_update_timer = 0

            # Gestion caméra et événements (mode GUI uniquement)
            if not is_terminal_only:
                # with ProfileSection('handle_camera'):
                if True:
                    handle_camera(camera, raw_dt * GAME_SPEED)
                
                # with ProfileSection('handle_events'):
                if True:
                    for event in pygame.event.get():
                        handle_events(event, game_state)
                        
                        if event.type == pygame.QUIT:
                            running = False
                        
                        # Gestion game over
                        if game_state.get('game_over', False):
                            pygame.mouse.set_visible(True)
                            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                                mx, my = pygame.mouse.get_pos()
                                if game_state.get('game_over_button_rect') and game_state['game_over_button_rect'].collidepoint(mx, my):
                                    user_choices["menu_result"] = "quit"
                                    running = False
                                if game_state.get('main_menu_button_rect') and game_state['main_menu_button_rect'].collidepoint(mx, my):
                                    user_choices["menu_result"] = "main_menu"
                                    game_state['game_over'] = False
                                    game_state['return_to_menu'] = True

        # Vérification retour menu
        if game_state.get('return_to_menu'):
            break

        # Gestion switch display
        if game_state.get('switch_display'):
            game_map.save_map(TEMP_SAVE_PATH)
            if screen and pygame.display.get_init():
                pygame.display.quit()
                pygame.quit()
            user_choices["menu_result"] = "switch_display"
            break

        # Mise à jour références depuis game_state
        screen = game_state['screen']
        screen_width = game_state['screen_width']
        screen_height = game_state['screen_height']
        selected_player = game_state['selected_player']
        players = game_state['players']
        camera = game_state['camera']

        # Mise à jour minimap
        if not game_state.get('paused', False):
            update_counter += dt
            if update_counter > 1:
                update_counter = 0
                # with ProfileSection('update_minimap'):
                if True:
                    update_minimap_elements(game_state)

        # Mise à jour surfaces joueur
        if not game_state.get('paused', False):
            if game_state.get('player_selection_updated', False):
                player_selection_surface = create_player_selection_surface(
                    players, selected_player,
                    game_state['minimap_background_rect'],
                    game_state['team_colors']
                )
                game_state['player_selection_surface'] = player_selection_surface
                game_state['player_selection_updated'] = False

            if game_state.get('player_info_updated', False):
                player_info_surface = create_player_info_surface(
                    selected_player, screen_width, screen_height,
                    game_state['team_colors']
                )
                game_state['player_info_updated'] = False

            # with ProfileSection('update_game_state'):
            if True:
                update_game_state(game_state, dt)

        # Vérification joueurs éliminés
        for p in players[:]:
            if is_player_dead(p):
                if p.teamID in game_state['old_resources']:
                    del game_state['old_resources'][p.teamID]
                players.remove(p)

        # Vérification victoire
        if len(players) == 1 and not game_state.get('game_over', False):
            game_state['winner_id'] = players[0].teamID
            game_state['game_over'] = True
            game_state['paused'] = True

        # Mise à jour ressources
        if selected_player and selected_player in players:
            if selected_player.teamID in game_state['old_resources']:
                previous_res = game_state['old_resources'][selected_player.teamID]
                current_res = selected_player.resources
                if current_res != previous_res:
                    game_state['player_info_updated'] = True
                    game_state['old_resources'][selected_player.teamID] = current_res.copy()

        # ==================== RENDU ====================
        draw_timer += raw_dt
        if screen is not None and draw_timer >= 1 / FPS_DRAW_LIMITER:
            draw_timer = 0
            
            # with ProfileSection('screen_fill'):
            if True:
                screen.fill((0, 0, 0))
            
            # with ProfileSection('draw_map'):
            if True:
                draw_map(screen, screen_width, screen_height, game_map, camera,
                        players, game_state['team_colors'], game_state, dt)

            if game_state['show_gui_elements']:
                # with ProfileSection('draw_gui'):
                if True:
                    draw_gui_elements(screen, screen_width, screen_height)
                    screen.blit(game_state['minimap_background'], game_state['minimap_background_rect'].topleft)
                    screen.blit(game_state['minimap_entities_surface'], game_state['minimap_background_rect'].topleft)
                    draw_minimap_viewport(screen, camera, game_state['minimap_background_rect'],
                                         game_state['minimap_scale'], game_state['minimap_offset_x'],
                                         game_state['minimap_offset_y'], game_state['minimap_min_iso_x'],
                                         game_state['minimap_min_iso_y'])

                    if player_selection_surface:
                        sel_h = player_selection_surface.get_height()
                        bg_rect = game_state['minimap_background_rect']
                        screen.blit(player_selection_surface, (bg_rect.x, bg_rect.y - sel_h - 20))

                    if player_info_surface and game_state['show_player_info']:
                        x_offset = int(screen_width * 0.03)
                        screen.blit(player_info_surface, (x_offset, 0))

            draw_pointer(screen)

            # Affichage FPS
            if font and clock:
                display_fps(screen, screen_width, clock, font)

            # Notification
            if game_state['notification_message']:
                if time.time() - game_state['notification_start_time'] < 3:
                    notif_font = pygame.font.SysFont(None, 28)
                    notif_surf = notif_font.render(game_state['notification_message'], True, (255, 255, 0))
                    screen.blit(notif_surf, (screen_width - notif_surf.get_width() - 10, 40))
                else:
                    game_state['notification_message'] = ""

            # Overlays (game over, pause, options)
            if game_state.get('game_over', False):
                draw_game_over_overlay(screen, game_state)
            
            mx, my = pygame.mouse.get_pos()

            if game_state.get('options_menu_active'):
                draw_options_menu(screen, game_state, mx, my)
                draw_pointer(screen)
                pygame.display.flip()
                continue
                
            if game_state.get('pause_menu_active'):
                draw_pause_menu(screen, game_state, mx, my)
                draw_pointer(screen)
                pygame.display.flip()
                continue

            # with ProfileSection('display_flip'):
            if True:
                pygame.display.flip()
            
            # Tick du profiler
            # tick_frame()

        # Synchronisation (vérification moins fréquente)
        if check_and_load_sync(game_map):
            players = game_map.players
            game_state['players'] = players
            game_state['selected_player'] = players[0] if players else None
            game_state['team_colors'] = generate_team_colors(len(players))
            game_state['force_full_redraw'] = True
            game_state['player_selection_updated'] = True
            
            # Restaurer players_target depuis la sauvegarde ou réinitialiser
            saved_players_target = game_map.game_state.get('players_target')
            if saved_players_target and len(saved_players_target) == len(players):
                game_state['players_target'] = saved_players_target
            else:
                game_state['players_target'] = [None for _ in range(len(players))]
            
            # Restaurer bot_modes depuis la sauvegarde
            bot_modes = game_map.game_state.get('bot_modes', ['economique'] * len(players))
            bots, bot_modes = create_bots(players, game_map, bot_modes)
            game_map.game_state['bot_modes'] = bot_modes

    return "done"
