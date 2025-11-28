# Chemin de C:/Users/cyril/OneDrive/Documents/INSA/3A/PYTHON_TEST/Projet_python\Controller\gui.py
import pygame
import os
import sys
import time
from collections import OrderedDict, Counter
from Settings.setup import *
from Controller.init_assets import *
from Settings.setup import *
from Controller.utils import to_isometric, get_color_for_terrain
from Entity.Building import Building
import Controller.ui_theme as theme  # Import the theme

pygame.init()
theme.init_theme() # Initialize theme
font = theme.FONT_MAIN # Use theme font as default

#user_choices["index_terminal_display"] = 2

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
        # Pas de mise à l'échelle
        gui_cache[key] = original
        return original

    scaled = pygame.transform.smoothscale(original, (target_width, target_height))
    gui_cache[key] = scaled
    return scaled

def get_centered_rect_in_bottom_right(width, height, screen_width, screen_height, margin=10):
    rect = pygame.Rect(0, 0, width, height)
    center_x = screen_width - margin - (width // 2)
    center_y = screen_height - margin - (height // 2)
    rect.center = (center_x, center_y)
    return rect

def update_minimap_elements(game_state):
    from Entity.Building import Building
    from Entity.Resource.Gold import Gold

    camera = game_state['camera']
    game_map = game_state['game_map']
    team_colors = game_state['team_colors']
    scale_factor = game_state['minimap_scale']
    offset_x = game_state['minimap_offset_x']
    offset_y = game_state['minimap_offset_y']
    min_iso_x = game_state['minimap_min_iso_x']
    min_iso_y = game_state['minimap_min_iso_y']
    minimap_surface = game_state['minimap_entities_surface']

    minimap_surface.fill((0, 0, 0, 0))

    tile_width = HALF_TILE_SIZE
    tile_height = HALF_TILE_SIZE / 2

    entity_set = set()
    for pos, active_entities in game_map.grid.items():
        for ent in active_entities:
            entity_set.add(ent)

    MIN_BUILDING_SIZE = 3
    MIN_UNIT_RADIUS = 2

    for ent in entity_set:
        x_val, y_val = ent.x, ent.y
        iso_x, iso_y = to_isometric(x_val, y_val, tile_width, tile_height)
        mini_x = (iso_x - min_iso_x) * scale_factor + offset_x
        mini_y = (iso_y - min_iso_y) * scale_factor + offset_y

        if ent.team is not None:
            color_draw = team_colors[ent.team % len(team_colors)]
            if isinstance(ent, Building):
                half_dim = max(MIN_BUILDING_SIZE, ent.size)
                rect_building = pygame.Rect(
                    mini_x - half_dim,
                    mini_y - half_dim,
                    half_dim * 2,
                    half_dim * 2
                )
                pygame.draw.rect(minimap_surface, (*color_draw, 150), rect_building)
            else:
                radius_val = max(MIN_UNIT_RADIUS, ent.size)
                pygame.draw.circle(minimap_surface, (*color_draw, 150), (mini_x, mini_y), radius_val)
        else:
            if isinstance(ent, Gold):
                gold_color = get_color_for_terrain('gold')
                radius_val = max(MIN_UNIT_RADIUS, ent.size)
                pygame.draw.circle(minimap_surface, (*gold_color, 150), (mini_x, mini_y), radius_val)

def run_gui_menu(screen, sw, sh):
    """
    Menu GUI bloquant : boucle Pygame jusqu'à ce que user_choices["validated"] == True
    ou fermeture de la fenêtre.

    Par défaut, toggle_button["index"] = 2 => Both (Terminal + GUI).
    """
    clock = pygame.time.Clock()
    show_main_menu   = True
    show_config_menu = False
    show_load_menu   = False
    item_height = ITEM_HEIGHT  # Définir item_height au début de la fonction

    main_buttons = [
        {"text": "Nouvelle Partie", "rect": pygame.Rect(0,0,200,50)},
        {"text": "Charger Partie",  "rect": pygame.Rect(0,0,200,50)},
        {"text": "Quitter",         "rect": pygame.Rect(0,0,200,50)},
    ]

    back_button = {"text": "Retour", "rect": pygame.Rect(20, 20, 100, 40)}
    toggle_button = {
        "rect": pygame.Rect(sw // 2 - 200, 430, 400, 50),
        "texts": ["Gui ONLY", "Terminal Display ONLY", "Terminal and Gui Display"],
        "index": user_choices["index_terminal_display"]
    }

    save_files = []
    if os.path.isdir(SAVE_DIRECTORY):
        save_files = [f for f in os.listdir(SAVE_DIRECTORY) if f.endswith('.pkl')]

    idx_width = VALID_GRID_SIZES.index(user_choices["grid_width"]) # Initialisation pour la largeur
    idx_height = VALID_GRID_SIZES.index(user_choices["grid_height"]) # Initialisation pour la hauteur
    idx_nbot = VALID_BOTS_COUNT.index(user_choices["num_bots"])
    idx_lvl  = VALID_LEVELS.index(user_choices["bot_level"])
    idx_bot_mode = VALID_BOT_MODES.index(user_choices.get("bot_mode", "economique")) # Initialize bot_mode index here!

    gold_checked = user_choices["gold_at_center"]
    combo_open = None

    # Initial call with dummy mouse coordinates
    valid_rect, _ = draw_config_menu(screen, sw, sh, idx_width, idx_height, idx_nbot, idx_lvl, gold_checked, combo_open, idx_bot_mode, 0, 0)

    running = True
    while running:
        clock.tick(60)
        screen.fill((30,30,30))

        if user_choices["validated"]:
            running = False

        mx, my = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEWHEEL:
                if combo_open == "width": # Pour la largeur
                    if event.y < 0:
                        if combo_scroll_positions["width"] < len(VALID_GRID_SIZES) - MAX_VISIBLE_ITEMS:
                            combo_scroll_positions["width"] += 1
                    else:
                        if combo_scroll_positions["width"] > 0:
                            combo_scroll_positions["width"] -= 1
                elif combo_open == "height": # Pour la hauteur
                    if event.y < 0:
                        if combo_scroll_positions["height"] < len(VALID_GRID_SIZES) - MAX_VISIBLE_ITEMS:
                            combo_scroll_positions["height"] += 1
                    else:
                        if combo_scroll_positions["height"] > 0:
                            combo_scroll_positions["height"] -= 1
                elif combo_open == "nbot":
                    if event.y < 0:
                        if combo_scroll_positions["nbot"] < len(VALID_BOTS_COUNT) - MAX_VISIBLE_ITEMS:
                            combo_scroll_positions["nbot"] += 1
                    else:
                        if combo_scroll_positions["nbot"] > 0:
                            combo_scroll_positions["nbot"] -= 1
                elif combo_open == "lvl":
                    if event.y < 0:
                        if combo_scroll_positions["lvl"] < len(VALID_LEVELS) - MAX_VISIBLE_ITEMS:
                            combo_scroll_positions["lvl"] += 1
                    else:
                        if combo_scroll_positions["lvl"] > 0:
                            combo_scroll_positions["lvl"] -= 1
                elif combo_open == "bot_mode": # Pour le mode IA - AJOUT
                    if event.y < 0:
                        if combo_scroll_positions["bot_mode"] < len(VALID_BOT_MODES) - MAX_VISIBLE_ITEMS:
                            combo_scroll_positions["bot_mode"] += 1
                    else:
                        if combo_scroll_positions["bot_mode"] > 0:
                            combo_scroll_positions["bot_mode"] -= 1

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Bouton "Retour"
                if (show_config_menu or show_load_menu) and back_button["rect"].collidepoint(mx, my):
                    show_main_menu = True
                    show_config_menu = False
                    show_load_menu = False
                    continue

                if combo_open == "width": # Width combo box
                    start_idx = combo_scroll_positions["width"]
                    visible_items = VALID_GRID_SIZES[start_idx:start_idx + MAX_VISIBLE_ITEMS]
                    expanded_rect = pygame.Rect(sw//2 - 100, 100 + item_height, 200, item_height * len(visible_items))
                    if expanded_rect.collidepoint(mx,my):
                        relative_y = my - (100 + item_height)
                        item_index = relative_y // item_height
                        if 0 <= item_index < len(visible_items):
                            new_val = visible_items[item_index]
                            idx_width = VALID_GRID_SIZES.index(new_val)
                            user_choices["grid_width"] = new_val # Update width
                        combo_open = None
                        continue
                elif combo_open == "height": # Height combo box
                    start_idx = combo_scroll_positions["height"]
                    visible_items = VALID_GRID_SIZES[start_idx:start_idx + MAX_VISIBLE_ITEMS]
                    expanded_rect = pygame.Rect(sw//2 - 100, 160 + ITEM_HEIGHT, 200, ITEM_HEIGHT * len(visible_items))
                    if expanded_rect.collidepoint(mx,my):
                        relative_y = my - (160 + item_height)
                        item_index = relative_y // ITEM_HEIGHT
                        if 0 <= item_index < len(visible_items):
                            new_val = visible_items[item_index]
                            idx_height = VALID_GRID_SIZES.index(new_val)
                            user_choices["grid_height"] = new_val # Update height
                        combo_open = None
                        continue
                elif combo_open == "nbot":
                    start_idx = combo_scroll_positions["nbot"]
                    visible_items = VALID_BOTS_COUNT[start_idx:start_idx + MAX_VISIBLE_ITEMS]
                    expanded_rect = pygame.Rect(sw//2 - 100, 220 + ITEM_HEIGHT, 200, ITEM_HEIGHT * len(visible_items))
                    if expanded_rect.collidepoint(mx,my):
                        relative_y = my - (220 + ITEM_HEIGHT)
                        item_index = relative_y // ITEM_HEIGHT
                        if 0 <= item_index < len(visible_items):
                            new_val = visible_items[item_index]
                            idx_nbot = VALID_BOTS_COUNT.index(new_val)
                            user_choices["num_bots"] = new_val
                        combo_open = None
                        continue
                elif combo_open == "lvl":
                    start_idx = combo_scroll_positions["lvl"]
                    visible_items = VALID_LEVELS[start_idx:start_idx + MAX_VISIBLE_ITEMS]
                    expanded_rect = pygame.Rect(sw//2 - 100, 280 + ITEM_HEIGHT, 200, ITEM_HEIGHT * len(visible_items))
                    if expanded_rect.collidepoint(mx,my):
                        relative_y = my - (280 + ITEM_HEIGHT)
                        item_index = relative_y // ITEM_HEIGHT
                        if 0 <= item_index < len(visible_items):
                            new_val = visible_items[item_index]
                            idx_lvl = VALID_LEVELS.index(new_val)
                            user_choices["bot_level"] = new_val
                        combo_open = None
                        continue
                elif combo_open == "bot_mode": # Bot Mode combo box - AJOUT
                    start_idx = combo_scroll_positions["bot_mode"]
                    visible_items = VALID_BOT_MODES[start_idx:start_idx + MAX_VISIBLE_ITEMS]
                    expanded_rect = pygame.Rect(sw//2 - 100, 340 + ITEM_HEIGHT, 200, ITEM_HEIGHT * len(visible_items))
                    if expanded_rect.collidepoint(mx,my):
                        relative_y = my - (340 + ITEM_HEIGHT)
                        item_index = relative_y // ITEM_HEIGHT
                        if 0 <= item_index < len(visible_items):
                            new_val = visible_items[item_index]
                            idx_bot_mode = VALID_BOT_MODES.index(new_val)
                            user_choices["bot_mode"] = new_val # Update bot_mode
                        combo_open = None
                        continue

                if combo_open:
                    combo_rect_width = pygame.Rect(sw//2 - 100, 100, 200, 30) # Rect for width combo
                    combo_rect_height = pygame.Rect(sw//2 - 100, 160, 200, 30) # Rect for height combo
                    combo_rect_nbot = pygame.Rect(sw//2 - 100, 220, 200, 30)
                    combo_rect_lvl  = pygame.Rect(sw//2 - 100, 280, 200, 30)
                    combo_rect_bot_mode = pygame.Rect(sw//2 - 100, 340, 200, 30) # Rect for bot_mode combo - AJOUT

                    # Si on clique en dehors, on referme TOUS les combos ouverts
                    if not (combo_rect_width.collidepoint(mx,my) or # Check width combo rect
                            combo_rect_height.collidepoint(mx,my) or # Check height combo rect
                            combo_rect_nbot.collidepoint(mx,my) or
                            combo_rect_lvl.collidepoint(mx,my) or
                            combo_rect_bot_mode.collidepoint(mx, my)): # Check bot_mode combo rect - AJOUT
                        combo_open = None

                if show_main_menu:
                    for i, btn in enumerate(main_buttons):
                        if btn["rect"].collidepoint(mx,my):
                            if i == 0:
                                user_choices["load_game"] = False
                                show_main_menu = False
                                show_config_menu = True
                            elif i == 1:
                                user_choices["load_game"] = True
                                show_main_menu = False
                                show_load_menu = True
                            else:
                                pygame.quit()
                                sys.exit()

                elif show_config_menu:
                    combo_rect_width = pygame.Rect(sw//2 - 100, 100, 200, 30) # Rect for width combo
                    combo_rect_height = pygame.Rect(sw//2 - 100, 160, 200, 30) # Rect for height combo
                    combo_rect_nbot = pygame.Rect(sw//2 - 100, 220, 200, 30)
                    combo_rect_lvl  = pygame.Rect(sw//2 - 100, 280, 200, 30)
                    combo_rect_bot_mode = pygame.Rect(sw//2 - 100, 340, 200, 30) # Rect for bot_mode combo - AJOUT

                    if combo_rect_width.collidepoint(mx,my): # Open/close width combo
                        combo_open = ("width" if combo_open != "width" else None)
                    elif combo_rect_height.collidepoint(mx,my): # Open/close height combo
                        combo_open = ("height" if combo_open != "height" else None)
                    elif combo_rect_nbot.collidepoint(mx,my):
                        combo_open = ("nbot" if combo_open != "nbot" else None)
                    elif combo_rect_lvl.collidepoint(mx,my):
                        combo_open = ("lvl" if combo_open != "lvl" else None)
                    elif combo_rect_bot_mode.collidepoint(mx, my): # Open/close bot_mode combo - AJOUT
                        combo_open = ("bot_mode" if combo_open != "bot_mode" else None)


                    chk_rect = pygame.Rect(sw//2 - 100, 380, 30, 30) # Checkbox rect moved up
                    if chk_rect.collidepoint(mx,my):
                        gold_checked = not gold_checked
                        user_choices["gold_at_center"] = gold_checked

                    # Toggle display mode button
                    if toggle_button["rect"].collidepoint(mx, my):
                        toggle_button["index"] = (toggle_button["index"] + 1) % len(toggle_button["texts"])
                        user_choices["index_terminal_display"] = toggle_button["index"]

                    # Bouton Valider (validation_rect est défini avant la boucle)
                    if valid_rect.collidepoint(mx,my):
                        # Créer une liste de niveaux identiques pour tous les bots
                        user_choices["bot_modes"] = [user_choices.get("bot_mode", "economique")] * user_choices["num_bots"]
                        user_choices["validated_by"] = "gui"
                        user_choices["validated"] = True
                        running = False

                elif show_load_menu:
                    start_y = 100
                    gap = 5
                    block_h = 30
                    for i, sf in enumerate(save_files):
                        rect = pygame.Rect(sw//2 - 150, start_y + i*(block_h+gap), 300, block_h)
                        if rect.collidepoint(mx,my):
                            user_choices["chosen_save"] = os.path.join(SAVE_DIRECTORY, sf)
                            user_choices["load_game"] = True
                            user_choices["validated"] = True
                            running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    combo_open = None

        if show_main_menu:
            draw_main_menu(screen, sw, sh, main_buttons, mx, my)
        elif show_config_menu:
            # Draw toggle button and back button first
            draw_choose_display(screen, toggle_button, mx, my)
            
            is_back_hovered = back_button["rect"].collidepoint(mx, my)
            theme.draw_button(screen, back_button["rect"], back_button["text"], is_hovered=is_back_hovered, color_normal=theme.COLOR_DANGER, color_hover=(220, 100, 100))

            # Finally draw config menu so expanded combo appears on top
            valid_rect, expanded_rect = draw_config_menu(screen, sw, sh,
                idx_width, idx_height, idx_nbot, idx_lvl, gold_checked, combo_open, idx_bot_mode, mx, my)
        elif show_load_menu:
            draw_load_menu(screen, sw, sh, save_files, mx, my)
            
            is_back_hovered = back_button["rect"].collidepoint(mx, my)
            theme.draw_button(screen, back_button["rect"], back_button["text"], is_hovered=is_back_hovered, color_normal=theme.COLOR_DANGER, color_hover=(220, 100, 100))

        pygame.display.flip()

        # Met à jour la variable globale index_terminal_display
        # d'après l'état du bouton toggle_button
        user_choices["index_terminal_display"] = toggle_button["index"]

def draw_choose_display(screen, toggle_button, mx, my):
    is_hovered = toggle_button["rect"].collidepoint(mx, my)
    theme.draw_button(screen, toggle_button["rect"], toggle_button["texts"][toggle_button["index"]], is_hovered=is_hovered, color_normal=(0, 100, 200))

def draw_main_menu(screen, sw, sh, buttons, mx, my):
    # Draw background (optional, if not covered by screen fill)
    # screen.fill(theme.COLOR_BACKGROUND)
    
    # Title
    title_surf = theme.FONT_TITLE.render("Age of Strategy", True, theme.COLOR_ACCENT)
    title_rect = title_surf.get_rect(center=(sw//2, sh//4))
    screen.blit(title_surf, title_rect)

    gap = 20
    start_y = (sh - (len(buttons)*60 + gap*(len(buttons)-1))) // 2 + 50 # Shifted down a bit
    
    for i, btn in enumerate(buttons):
        btn["rect"].width = 300
        btn["rect"].height = 60
        btn["rect"].centerx = sw//2
        btn["rect"].y = start_y + i*(60+gap)
        
        is_hovered = btn["rect"].collidepoint(mx, my)
        theme.draw_button(screen, btn["rect"], btn["text"], is_hovered=is_hovered)

VALID_BOT_MODES = ["economique", "defensif", "offensif"] # Added valid bot modes

def draw_config_menu(screen, sw, sh, idx_width, idx_height, idx_nbot, idx_lvl, gold_checked, combo_open, idx_mode, mx, my): # Added idx_bot_mode
    # Dessiner d'abord tous les éléments de base
    if combo_open != "width":
        draw_combo_box(screen, sw//2 - 100, 100, 200, 30, f"Largeur: {VALID_GRID_SIZES[idx_width]}", None, idx_width, combo_type="width", mx=mx, my=my)
    if combo_open != "height":
        draw_combo_box(screen, sw//2 - 100, 160, 200, 30, f"Hauteur: {VALID_GRID_SIZES[idx_height]}", None, idx_height, combo_type="height", mx=mx, my=my)
    if combo_open != "nbot":
        draw_combo_box(screen, sw//2 - 100, 220, 200, 30, f"Bots: {VALID_BOTS_COUNT[idx_nbot]}", None, idx_nbot, combo_type="nbot", mx=mx, my=my)
    if combo_open != "lvl":
        draw_combo_box(screen, sw//2 - 100, 280, 200, 30, f"Niveau: {VALID_LEVELS[idx_lvl]}", None, idx_lvl, combo_type="lvl", mx=mx, my=my)
    if combo_open != "bot_mode":
        draw_combo_box(screen, sw//2 - 100, 340, 200, 30, f"Mode IA: {VALID_BOT_MODES[idx_mode]}", None, idx_mode, combo_type="bot_mode", mx=mx, my=my)

    # Dessiner la checkbox et le bouton de validation
    chk_rect = pygame.Rect(sw//2 - 100, 380, 30, 30)  # Moved up to avoid overlap
    
    # Checkbox style
    # Draw a small wood panel for the checkbox
    theme.draw_wood_rect(screen, chk_rect, theme.COLOR_BUTTON_NORMAL, border_width=1)
    
    if gold_checked:
        # Draw a checkmark or filled square
        inner_rect = chk_rect.inflate(-8, -8)
        pygame.draw.rect(screen, theme.COLOR_SUCCESS, inner_rect)
        # Add a small highlight to the checkmark
        pygame.draw.rect(screen, (100, 200, 100), inner_rect, 1)
        
    txt = theme.FONT_MAIN.render("Or au centre ?", True, theme.COLOR_TEXT)
    screen.blit(txt, (chk_rect.right+10, chk_rect.y + 2))

    valid_rect = pygame.Rect(sw//2 - 75, 500, 150, 50)  # Adjusted to keep spacing
    is_valid_hovered = valid_rect.collidepoint(mx, my)
    theme.draw_button(screen, valid_rect, "Valider", is_hovered=is_valid_hovered, color_normal=theme.COLOR_SUCCESS, color_hover=(100, 220, 100))

    # Dessiner le menu déroulant actif EN DERNIER pour qu'il soit au-dessus
    expanded_rect = None
    if combo_open == "width":
        draw_combo_box(screen, sw//2 - 100, 100, 200, 30, f"Largeur: {VALID_GRID_SIZES[idx_width]}", VALID_GRID_SIZES, idx_width, combo_type="width", mx=mx, my=my)
        expanded_rect = pygame.Rect(sw//2 - 100, 100 + 30, 200, ITEM_HEIGHT * min(len(VALID_GRID_SIZES), MAX_VISIBLE_ITEMS))
    elif combo_open == "height":
        draw_combo_box(screen, sw//2 - 100, 160, 200, 30, f"Hauteur: {VALID_GRID_SIZES[idx_height]}", VALID_GRID_SIZES, idx_height, combo_type="height", mx=mx, my=my)
        expanded_rect = pygame.Rect(sw//2 - 100, 160 + 30, 200, ITEM_HEIGHT * min(len(VALID_GRID_SIZES), MAX_VISIBLE_ITEMS))
    elif combo_open == "nbot":
        draw_combo_box(screen, sw//2 - 100, 220, 200, 30, f"Bots: {VALID_BOTS_COUNT[idx_nbot]}", VALID_BOTS_COUNT, idx_nbot, combo_type="nbot", mx=mx, my=my)
        expanded_rect = pygame.Rect(sw//2 - 100, 220 + 30, 200, ITEM_HEIGHT * min(len(VALID_BOTS_COUNT), MAX_VISIBLE_ITEMS))
    elif combo_open == "lvl":
        draw_combo_box(screen, sw//2 - 100, 280, 200, 30, f"Niveau: {VALID_LEVELS[idx_lvl]}", VALID_LEVELS, idx_lvl, combo_type="lvl", mx=mx, my=my)
        expanded_rect = pygame.Rect(sw//2 - 100, 280 + 30, 200, ITEM_HEIGHT * min(len(VALID_LEVELS), MAX_VISIBLE_ITEMS))
    elif combo_open == "bot_mode":
        draw_combo_box(screen, sw//2 - 100, 340, 200, 30, f"Mode IA: {VALID_BOT_MODES[idx_mode]}", VALID_BOT_MODES, idx_mode, combo_type="bot_mode", mx=mx, my=my)
        expanded_rect = pygame.Rect(sw//2 - 100, 340 + 30, 200, ITEM_HEIGHT * min(len(VALID_BOT_MODES), MAX_VISIBLE_ITEMS))

    return valid_rect, expanded_rect


def draw_load_menu(screen, sw, sh, save_files, mx, my):
    start_y = 100
    gap = 5
    block_h = 40
    
    txt = theme.FONT_TITLE.render("Choisissez la sauvegarde :", True, theme.COLOR_TEXT)
    screen.blit(txt, (sw//2 - txt.get_width()//2, 40))
    
    for i, sf in enumerate(save_files):
        rect = pygame.Rect(sw//2 - 200, start_y + i*(block_h+gap), 400, block_h)
        is_hovered = rect.collidepoint(mx, my)
        theme.draw_button(screen, rect, sf, is_hovered=is_hovered, color_normal=(80, 60, 60), color_hover=(120, 80, 80))

def draw_combo_box(screen, x, y, w, h, text, items_list, selected_idx, combo_type=None, mx=0, my=0):
    # Dessiner d'abord le bouton du combo box
    box_rect = pygame.Rect(x, y, w, h)
    is_hovered = box_rect.collidepoint(mx, my)
    theme.draw_button(screen, box_rect, text, is_hovered=is_hovered)

    # Si on a une liste d'éléments, dessiner le menu déroulant
    if items_list:
        start_idx = combo_scroll_positions[combo_type]
        visible_items = items_list[start_idx:start_idx + MAX_VISIBLE_ITEMS]

        # Créer une surface distincte pour le menu déroulant
        dropdown_height = len(visible_items) * ITEM_HEIGHT
        dropdown_surf = pygame.Surface((w, dropdown_height), pygame.SRCALPHA)

        # Remplir avec un fond semi-transparent
        dropdown_surf.fill(theme.COLOR_PANEL_BG)
        pygame.draw.rect(dropdown_surf, theme.COLOR_BORDER, dropdown_surf.get_rect(), 1)

        # Dessiner chaque élément de la liste
        for i, val in enumerate(visible_items):
            item_rect = pygame.Rect(0, i*ITEM_HEIGHT, w, ITEM_HEIGHT)
            
            # Check hover relative to screen
            screen_item_rect = pygame.Rect(x, y + h + i*ITEM_HEIGHT, w, ITEM_HEIGHT)
            is_item_hovered = screen_item_rect.collidepoint(mx, my)
            
            bg_color = theme.COLOR_BUTTON_HOVER if is_item_hovered else ((60,60,80) if i % 2 == 0 else (50,50,70))
            
            pygame.draw.rect(dropdown_surf, bg_color, item_rect)
            
            txt = theme.FONT_MAIN.render(str(val), True, theme.COLOR_TEXT)
            txt_rect = txt.get_rect(center=item_rect.center)
            dropdown_surf.blit(txt, txt_rect)

        # Dessiner le menu déroulant sur l'écran
        screen.blit(dropdown_surf, (x, y + h))

def create_player_selection_surface(players, selected_player, minimap_rect, team_colors):
    from Settings.setup import user_choices
    if user_choices["index_terminal_display"] == 1:  # Terminal only mode
        return None

    selection_height = 30
    padding = 5

    screen = pygame.display.get_surface()
    screen_height = screen.get_height() if screen else 600  # Default height if no screen
    max_height = screen_height / 3

    columns = 1
    while (columns <= 4):
        rows = (len(players) + columns - 1) // columns
        total_height = selection_height * rows + padding * (rows - 1)
        if (total_height <= max_height or columns == 4):
            break
        columns += 1

    button_width = (minimap_rect.width - padding * (columns - 1)) // columns
    rows = (len(players) + columns - 1) // columns
    total_height = selection_height * rows + padding * (rows - 1)

    surface = pygame.Surface((minimap_rect.width, total_height), pygame.SRCALPHA)
    font_sel = pygame.font.Font(None, 24)

    for index, player in enumerate(reversed(players)):
        col = index % columns
        row = index // columns
        rect_x = col * (button_width + padding)
        rect_y = row * (selection_height + padding)
        rect = pygame.Rect(rect_x, rect_y, button_width, selection_height)

        if player == selected_player:
            color = (255, 255, 255)
        else:
            color = team_colors[player.teamID % len(team_colors)]

        pygame.draw.rect(surface, color, rect)
        player_text = font_sel.render(f'Player {player.teamID}', True, (0, 0, 0))
        text_rect = player_text.get_rect(center=rect.center)
        surface.blit(player_text, text_rect)

    return surface

def create_player_info_surface(selected_player, screen_width, screen_height, team_colors):
    from Settings.setup import user_choices
    if user_choices["index_terminal_display"] == 1:  # Terminal only mode
        return None

    # Create a panel surface
    panel_height = 220
    surface = pygame.Surface((screen_width, panel_height), pygame.SRCALPHA)
    
    # Draw panel background
    theme.draw_panel(surface, pygame.Rect(10, 10, screen_width - 20, panel_height - 20))

    padding_x = 30
    padding_y = 30
    spacing_y = 25

    # Resources
    gold_str = f"Gold: {selected_player.resources.gold}"
    wood_str = f"Wood: {selected_player.resources.wood}"
    food_str = f"Food: {selected_player.resources.food}"
    
    # Use a slightly larger font for resources
    res_font = theme.FONT_MAIN
    
    # Draw resources in a row
    x_offset = padding_x
    for res_str, color in [(gold_str, (255, 215, 0)), (wood_str, (160, 82, 45)), (food_str, (255, 100, 100))]:
        surf = res_font.render(res_str, True, color)
        surface.blit(surf, (x_offset, padding_y))
        x_offset += surf.get_width() + 40

    y_cursor = padding_y + 40

    # Player name
    team_color = team_colors[selected_player.teamID % len(team_colors)]
    player_name_surface = theme.FONT_TITLE.render(f"Player {selected_player.teamID}", True, team_color)
    # Align right
    surface.blit(player_name_surface, (screen_width - player_name_surface.get_width() - 30, padding_y))

    # Units
    unit_counts = Counter(unit.acronym for unit in selected_player.units)
    units_text = "Units: " + ", ".join([f"{acronym}: {count}" for acronym, count in unit_counts.items()])
    units_surface = theme.FONT_SMALL.render(units_text, True, theme.COLOR_TEXT)
    surface.blit(units_surface, (padding_x, y_cursor))
    y_cursor += spacing_y

    # Buildings
    building_counts = Counter(building.acronym for building in selected_player.buildings)
    buildings_text = "Buildings: " + ", ".join([f"{acronym}: {count}" for acronym, count in building_counts.items()])
    buildings_surface = theme.FONT_SMALL.render(buildings_text, True, theme.COLOR_TEXT)
    surface.blit(buildings_surface, (padding_x, y_cursor))
    y_cursor += spacing_y

    # Population
    population_text = f"Population: {selected_player.population} / {selected_player.maximum_population}"
    population_surface = theme.FONT_SMALL.render(population_text, True, theme.COLOR_TEXT_DIM)
    surface.blit(population_surface, (padding_x, y_cursor))

    return surface

def draw_game_over_overlay(screen, game_state):
    overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    
    winner_id = game_state.get('winner_id', '?')
    text_surf = theme.FONT_TITLE.render(f"Bravo ! Joueur {winner_id} a gagné", True, theme.COLOR_ACCENT)
    text_rect = text_surf.get_rect(center=(screen.get_width()//2, screen.get_height()//3))
    overlay.blit(text_surf, text_rect)

    mx, my = pygame.mouse.get_pos()

    button_rect = pygame.Rect(0, 0, 250, 50)
    button_rect.center = (screen.get_width() // 2, screen.get_height() // 2)
    is_hovered = button_rect.collidepoint(mx, my)
    theme.draw_button(overlay, button_rect, "Quitter le jeu", is_hovered=is_hovered, color_normal=theme.COLOR_DANGER, color_hover=(220, 100, 100))

    game_state['game_over_button_rect'] = button_rect
    screen.blit(overlay, (0, 0))

def draw_pause_menu(screen, game_state, mx=0, my=0):
    screen_width = game_state['screen_width']
    screen_height = game_state['screen_height']

    # Overlay
    overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    pause_text = theme.FONT_TITLE.render("Pause Menu", True, theme.COLOR_TEXT)
    text_rect = pause_text.get_rect(center=(screen_width // 2, screen_height // 4))
    screen.blit(pause_text, text_rect)

    labels = ["Resume", "Options", "Load Game", "Save Game", "Exit"]
    y_start = text_rect.bottom + 60
    button_rects = {}
    
    button_width = 300
    button_height = 50
    gap = 20

    for label in labels:
        rect = pygame.Rect(0, 0, button_width, button_height)
        rect.centerx = screen_width // 2
        rect.y = y_start
        
        is_hovered = rect.collidepoint(mx, my)
        theme.draw_button(screen, rect, label, is_hovered=is_hovered)
        
        button_rects[label] = rect
        y_start += button_height + gap

    game_state['pause_menu_button_rects'] = button_rects


def draw_options_menu(screen, game_state, mx=0, my=0):
    """Dessine le menu d'options avec les keybindings."""
    from Settings.keybindings import (
        current_keybindings, ACTION_NAMES, ACTION_CATEGORIES, 
        get_key_name, set_keybinding, reset_keybindings
    )
    
    screen_width = game_state['screen_width']
    screen_height = game_state['screen_height']
    
    # Fond semi-transparent
    overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    overlay.fill((30, 30, 30, 240))
    screen.blit(overlay, (0, 0))
    
    # Titre
    title_text = theme.FONT_TITLE.render("Options - Configuration des Touches", True, theme.COLOR_TEXT)
    title_rect = title_text.get_rect(center=(screen_width // 2, 50))
    screen.blit(title_text, title_rect)
    
    # Initialiser les variables de state si nécessaire
    if 'options_scroll_offset' not in game_state:
        game_state['options_scroll_offset'] = 0
    if 'waiting_for_key' not in game_state:
        game_state['waiting_for_key'] = None
    
    # Zone de contenu scrollable
    content_y_start = 100
    content_height = screen_height - 200
    item_height = 40
    category_height = 50
    
    # Calculer la hauteur totale du contenu
    total_height = 0
    for category, actions in ACTION_CATEGORIES.items():
        total_height += category_height
        total_height += len(actions) * item_height
    
    # Limiter le scroll
    max_scroll = max(0, total_height - content_height)
    game_state['options_scroll_offset'] = max(0, min(game_state['options_scroll_offset'], max_scroll))
    
    # Zone de clipping pour le contenu scrollable
    # On dessine tout sur une surface séparée puis on blit la partie visible
    content_surf = pygame.Surface((screen_width - 100, total_height), pygame.SRCALPHA)
    
    # Dessiner les keybindings sur la surface de contenu
    button_rects = {}
    current_y = 0
    
    for category, actions in ACTION_CATEGORIES.items():
        # Catégorie
        cat_text = theme.FONT_MAIN.render(f"── {category} ──", True, theme.COLOR_ACCENT)
        content_surf.blit(cat_text, (10, current_y + 10))
        current_y += category_height
        
        for action in actions:
            # Nom de l'action
            action_name = ACTION_NAMES.get(action, action)
            action_text = theme.FONT_SMALL.render(action_name, True, theme.COLOR_TEXT)
            content_surf.blit(action_text, (30, current_y + 10))
            
            # Bouton de la touche
            key_code = current_keybindings.get(action)
            if game_state['waiting_for_key'] == action:
                key_name = "Appuyez sur une touche..."
                color_normal = theme.COLOR_BUTTON_CLICK
            else:
                key_name = get_key_name(key_code)
                color_normal = theme.COLOR_BUTTON_NORMAL
            
            button_rect_local = pygame.Rect(screen_width - 350, current_y + 5, 200, 30)
            
            # Calculer la position absolue pour le hover
            abs_y = content_y_start + current_y - game_state['options_scroll_offset']
            button_rect_abs = pygame.Rect(button_rect_local.x + 50, abs_y, button_rect_local.width, button_rect_local.height)
            
            is_hovered = button_rect_abs.collidepoint(mx, my)
            
            # Dessiner le bouton sur la surface locale
            theme.draw_button(content_surf, button_rect_local, key_name, is_hovered=is_hovered, color_normal=color_normal)
            
            # Stocker le rect absolu pour la gestion des clics
            if abs_y + item_height > content_y_start and abs_y < content_y_start + content_height:
                button_rects[action] = button_rect_abs
            
            current_y += item_height
            
    # Blit la partie visible
    visible_rect = pygame.Rect(0, game_state['options_scroll_offset'], screen_width - 100, content_height)
    screen.blit(content_surf, (50, content_y_start), visible_rect)
    
    game_state['options_keybind_rects'] = button_rects
    
    # Boutons du bas
    bottom_y = screen_height - 80
    
    # Bouton Retour
    back_rect = pygame.Rect(screen_width // 2 - 200, bottom_y, 150, 40)
    is_back_hovered = back_rect.collidepoint(mx, my)
    theme.draw_button(screen, back_rect, "Retour", is_hovered=is_back_hovered)
    game_state['options_back_rect'] = back_rect
    
    # Bouton Reset
    reset_rect = pygame.Rect(screen_width // 2 + 50, bottom_y, 150, 40)
    is_reset_hovered = reset_rect.collidepoint(mx, my)
    theme.draw_button(screen, reset_rect, "Réinitialiser", is_hovered=is_reset_hovered, color_normal=theme.COLOR_DANGER, color_hover=(220, 100, 100))
    game_state['options_reset_rect'] = reset_rect
    
    # Instructions
    if game_state['waiting_for_key']:
        hint_text = theme.FONT_SMALL.render("Appuyez sur ESC pour annuler", True, theme.COLOR_TEXT_DIM)
    else:
        hint_text = theme.FONT_SMALL.render("Cliquez sur une touche pour la modifier • Molette pour défiler", True, theme.COLOR_TEXT_DIM)
    hint_rect = hint_text.get_rect(center=(screen_width // 2, bottom_y + 55))
    screen.blit(hint_text, hint_rect)


def handle_options_menu_event(event, game_state):
    """Gère les événements du menu d'options."""
    from Settings.keybindings import set_keybinding, reset_keybindings, current_keybindings
    
    if event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1:  # Clic gauche
            mx, my = event.pos
            
            # Vérifier le bouton Retour
            if game_state.get('options_back_rect') and game_state['options_back_rect'].collidepoint(mx, my):
                game_state['options_menu_active'] = False
                game_state['waiting_for_key'] = None
                return True
            
            # Vérifier le bouton Reset
            if game_state.get('options_reset_rect') and game_state['options_reset_rect'].collidepoint(mx, my):
                reset_keybindings()
                game_state['waiting_for_key'] = None
                return True
            
            # Vérifier les boutons de keybind
            keybind_rects = game_state.get('options_keybind_rects', {})
            for action, rect in keybind_rects.items():
                if rect.collidepoint(mx, my):
                    game_state['waiting_for_key'] = action
                    return True
            
            # Clic ailleurs annule l'attente
            game_state['waiting_for_key'] = None
            
        elif event.button == 4:  # Molette haut
            game_state['options_scroll_offset'] = max(0, game_state.get('options_scroll_offset', 0) - 30)
            return True
        elif event.button == 5:  # Molette bas
            game_state['options_scroll_offset'] = game_state.get('options_scroll_offset', 0) + 30
            return True
    
    elif event.type == pygame.KEYDOWN:
        if game_state.get('waiting_for_key'):
            action = game_state['waiting_for_key']
            if event.key == pygame.K_ESCAPE:
                # Annuler
                game_state['waiting_for_key'] = None
            else:
                # Assigner la nouvelle touche
                set_keybinding(action, event.key)
                game_state['waiting_for_key'] = None
            return True
        elif event.key == pygame.K_ESCAPE:
            game_state['options_menu_active'] = False
            return True
    
    return False