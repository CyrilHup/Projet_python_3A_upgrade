
import pygame

# Medieval / Strategy Theme Colors
COLOR_BACKGROUND = (20, 15, 10)  # Very dark brown
COLOR_PANEL_BG = (60, 40, 20, 240)  # Dark Wood, semi-transparent
COLOR_BUTTON_NORMAL = (100, 60, 30) # Wood
COLOR_BUTTON_HOVER = (130, 80, 40)  # Lighter Wood
COLOR_BUTTON_CLICK = (80, 50, 20)   # Darker Wood
COLOR_TEXT = (255, 215, 0)          # Gold
COLOR_TEXT_DIM = (200, 180, 120)    # Pale Gold
COLOR_ACCENT = (255, 255, 255)      # White for titles
COLOR_BORDER = (180, 140, 60)       # Bronze/Gold border
COLOR_SUCCESS = (50, 150, 50)
COLOR_DANGER = (150, 50, 50)

# Fonts
FONT_MAIN = None
FONT_TITLE = None
FONT_SMALL = None

def init_theme():
    global FONT_MAIN, FONT_TITLE, FONT_SMALL
    pygame.font.init()
    
    # Prefer Serif fonts for medieval look
    available_fonts = pygame.font.get_fonts()
    preferred_fonts = ["times new roman", "georgia", "palatino linotype", "serif"]
    font_name = pygame.font.get_default_font()
    
    for f in preferred_fonts:
        if f in available_fonts:
            font_name = f
            break
            
    FONT_MAIN = pygame.font.SysFont(font_name, 24, bold=True)
    FONT_TITLE = pygame.font.SysFont(font_name, 56, bold=True)
    FONT_SMALL = pygame.font.SysFont(font_name, 18)

def draw_wood_rect(surface, rect, color, border_color=COLOR_BORDER, border_width=2):
    # Main body
    pygame.draw.rect(surface, color, rect)
    
    # Inner bevel (highlight top/left, shadow bottom/right)
    highlight = (min(color[0] + 30, 255), min(color[1] + 30, 255), min(color[2] + 30, 255))
    shadow = (max(color[0] - 30, 0), max(color[1] - 30, 0), max(color[2] - 30, 0))
    
    pygame.draw.line(surface, highlight, rect.topleft, rect.topright, 2)
    pygame.draw.line(surface, highlight, rect.topleft, rect.bottomleft, 2)
    pygame.draw.line(surface, shadow, rect.bottomleft, rect.bottomright, 2)
    pygame.draw.line(surface, shadow, rect.topright, rect.bottomright, 2)
    
    # Border
    pygame.draw.rect(surface, border_color, rect, border_width)
    
    # Corner accents (screws/nails)
    corner_color = (200, 180, 100)
    r = 3
    pygame.draw.circle(surface, corner_color, (rect.left + 5, rect.top + 5), r)
    pygame.draw.circle(surface, corner_color, (rect.right - 5, rect.top + 5), r)
    pygame.draw.circle(surface, corner_color, (rect.left + 5, rect.bottom - 5), r)
    pygame.draw.circle(surface, corner_color, (rect.right - 5, rect.bottom - 5), r)

def draw_button(screen, rect, text, is_hovered=False, is_active=False, color_normal=COLOR_BUTTON_NORMAL, color_hover=COLOR_BUTTON_HOVER, text_color=COLOR_TEXT):
    color = color_hover if is_hovered else color_normal
    if is_active:
        color = COLOR_BUTTON_CLICK
        
    # Shadow
    shadow_rect = rect.copy()
    shadow_rect.y += 4
    shadow_rect.x += 2
    pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect)
    
    # Draw wood button
    draw_wood_rect(screen, rect, color)
    
    # Text with shadow
    text_surf = FONT_MAIN.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)
    
    # Text Shadow
    shadow_surf = FONT_MAIN.render(text, True, (0, 0, 0))
    screen.blit(shadow_surf, (text_rect.x + 2, text_rect.y + 2))
    screen.blit(text_surf, text_rect)

def draw_panel(screen, rect):
    # Shadow
    shadow_rect = rect.copy()
    shadow_rect.y += 5
    shadow_rect.x += 5
    pygame.draw.rect(screen, (0, 0, 0, 120), shadow_rect)
    
    # Panel body
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    draw_wood_rect(s, s.get_rect(), (60, 40, 20), border_width=3)
    screen.blit(s, rect.topleft)

