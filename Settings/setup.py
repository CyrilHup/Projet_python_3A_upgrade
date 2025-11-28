# Chemin de C:/Users/cyril/OneDrive/Documents/INSA/3A/PYTHON_TEST/Projet_python\Settings\setup.py
# Path: Settings/setup.py
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional, List, FrozenSet
from Models.Resources import Resources
import os

# Get the base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define paths relative to the base directory
SAVE_DIRECTORY = os.path.join(BASE_DIR, 'saves')
ASSETS_DIRECTORY = os.path.join(BASE_DIR, 'assets')

# Create necessary directories
os.makedirs(SAVE_DIRECTORY, exist_ok=True)
os.makedirs(ASSETS_DIRECTORY, exist_ok=True)


# -------------------
# Dataclass Configurations
# -------------------

@dataclass(frozen=True)
class GameConstants:
    """Configuration globale du jeu (immutable)."""
    game_speed: int = 50
    fps_draw_limiter: int = 60
    building_time_reduction: float = 0.75
    building_zone_offset: int = 1
    resource_rate_per_sec: float = 25 / 60
    maximum_carry: int = 20
    dps: int = 2  # Decisions per second for bots


@dataclass(frozen=True)
class UnitConstants:
    """Constantes pour les unités (immutable)."""
    allowed_angles: Tuple[int, ...] = (0, 45, 90, 135, 180, 225, 270, 315)
    update_every_n_millisecond: int = 20
    one_second: int = 1000
    frames_per_unit: int = 10
    frames_per_building: int = 15
    frames_per_projectile: int = 11
    unit_hitbox: float = 0.3
    unit_attackrange: float = 0.6
    attack_range_epsilon: float = 0.5
    maximum_population: int = 200


@dataclass(frozen=True)
class MapConfig:
    """Configuration de la carte (immutable)."""
    tile_size: int = 200
    max_zoom: float = 3.0
    window_width: int = 1200
    window_height: int = 1200
    num_gold_tiles: int = 500
    num_wood_tiles: int = 500
    num_food_tiles: int = 500
    gold_spawn_middle: bool = False
    map_padding: int = 650
    
    @property
    def half_tile_size(self) -> float:
        return self.tile_size / 2
    
    @property
    def map_width(self) -> int:
        return 120 * self.tile_size
    
    @property
    def map_height(self) -> int:
        return 120 * self.tile_size


@dataclass(frozen=True)
class MinimapConfig:
    """Configuration de la minimap (immutable)."""
    width: int = 600
    height: int = 280
    margin: int = 20
    panel_ratio: float = 0.25
    bg_ratio: float = 0.20


@dataclass(frozen=True)
class HealthBarConfig:
    """Configuration des barres de vie (immutable)."""
    width: int = 40
    height: int = 5
    offset_y: int = 30


@dataclass(frozen=True)
class SpriteSheetConfig:
    """Configuration d'une sprite sheet."""
    columns: int
    rows: int


@dataclass
class DifficultyLevel:
    """Configuration d'un niveau de difficulté."""
    resources: Resources
    units: Dict[str, int]
    buildings: Dict[str, int]


# Instances globales des configurations (immutables)
GAME_CONSTANTS = GameConstants()
UNIT_CONSTANTS = UnitConstants()
MAP_CONFIG = MapConfig()
MINIMAP_CONFIG = MinimapConfig()
HEALTH_BAR_CONFIG = HealthBarConfig()

# -------------------
# Backward compatibility - expose old constants
# -------------------
GAME_SPEED = GAME_CONSTANTS.game_speed
FPS_DRAW_LIMITER = GAME_CONSTANTS.fps_draw_limiter
BUILDING_TIME_REDUCTION = GAME_CONSTANTS.building_time_reduction
BUILDING_ZONE_OFFSET = GAME_CONSTANTS.building_zone_offset
RESOURCE_RATE_PER_SEC = GAME_CONSTANTS.resource_rate_per_sec
MAXIMUM_CARRY = GAME_CONSTANTS.maximum_carry
DPS = GAME_CONSTANTS.dps

ALLOWED_ANGLES = list(UNIT_CONSTANTS.allowed_angles)
UPDATE_EVERY_N_MILLISECOND = UNIT_CONSTANTS.update_every_n_millisecond
ONE_SECOND = UNIT_CONSTANTS.one_second
FRAMES_PER_UNIT = UNIT_CONSTANTS.frames_per_unit
FRAMES_PER_BUILDING = UNIT_CONSTANTS.frames_per_building
FRAMES_PER_PROJECTILE = UNIT_CONSTANTS.frames_per_projectile
UNIT_HITBOX = UNIT_CONSTANTS.unit_hitbox
UNIT_ATTACKRANGE = UNIT_CONSTANTS.unit_attackrange
ATTACK_RANGE_EPSILON = UNIT_CONSTANTS.attack_range_epsilon
MAXIMUM_POPULATION = UNIT_CONSTANTS.maximum_population

TILE_SIZE = MAP_CONFIG.tile_size
HALF_TILE_SIZE = MAP_CONFIG.half_tile_size
MAP_WIDTH = MAP_CONFIG.map_width
MAP_HEIGHT = MAP_CONFIG.map_height
MAX_ZOOM = MAP_CONFIG.max_zoom
WINDOW_WIDTH = MAP_CONFIG.window_width
WINDOW_HEIGHT = MAP_CONFIG.window_height
NUM_GOLD_TILES = MAP_CONFIG.num_gold_tiles
NUM_WOOD_TILES = MAP_CONFIG.num_wood_tiles
NUM_FOOD_TILES = MAP_CONFIG.num_food_tiles
GOLD_SPAWN_MIDDLE = MAP_CONFIG.gold_spawn_middle
MAP_PADDING = MAP_CONFIG.map_padding

MINIMAP_WIDTH = MINIMAP_CONFIG.width
MINIMAP_HEIGHT = MINIMAP_CONFIG.height
MINIMAP_MARGIN = MINIMAP_CONFIG.margin
PANEL_RATIO = MINIMAP_CONFIG.panel_ratio
BG_RATIO = MINIMAP_CONFIG.bg_ratio

HEALTH_BAR_WIDTH = HEALTH_BAR_CONFIG.width
HEALTH_BAR_HEIGHT = HEALTH_BAR_CONFIG.height
HEALTH_BAR_OFFSET_Y = HEALTH_BAR_CONFIG.offset_y

# -------------------
# Config For Teams (using dataclass instances)
# -------------------
difficulty_config = {
    'lean': {
        'Resources': Resources(food=50, gold=150, wood=50),
        'Units': {'Villager': 3},
        'Buildings': {'TownCenter': 1}
    },
    'mean': {
        'Resources': Resources(food=2000, gold=2000, wood=2000),
        'Units': {'Villager': 3},
        'Buildings': {'TownCenter': 1}
    },
    'marines': {
        'Resources': Resources(food=20000, gold=20000, wood=20000),
        'Units': {'Villager': 15},
        'Buildings': {
            'TownCenter': 3,
            'Barracks': 2,
            'Stable': 2,
            'ArcheryRange': 2,
        }
    },
    'DEBUG': {
        'Resources': Resources(food=100, gold=80, wood=80),
        'Units': {
            'Villager': 5,
            'Archer': 0,
            'Horseman': 0,
            'Swordsman': 0
        },
        'Buildings': {
            'TownCenter': 1,
            'House': 0,
            'Barracks': 0,
            'Stable': 0,
            'ArcheryRange': 0,
            'Farm': 0,
            'Keep': 0,
            'Camp': 0,
        }
    }
}

# -------------------
# Sprites Configuration
# -------------------
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

MAX_VISIBLE_ITEMS = 5
ITEM_HEIGHT = 25

BAR_HEIGHT = 30
BAR_BORDER_RADIUS = 30
PROGRESS_BAR_WIDTH_RATIO = 0.8
PROGRESS_BAR_Y_RATIO = 0.9

BUILDING_RATIO = 100
UNIT_RATIO = 100
PROJECTILE_RATIO = 75

gui_config = {
    'loading_screen': {
        'directory': 'assets/launcher/',
        'scale': None
    },
    'ResourcesPanel': {
        'directory': 'assets/UI/Panels/resourcesPan',
    },
    'minimapPanel': {
        'directory': 'assets/UI/Panels/minimapPan',
    },
    'gold': {
        'directory': 'assets/UI/Resources/gold',
    },
    'wood': {
        'directory': 'assets/UI/Resources/wood',
    },
    'food': {
        'directory': 'assets/UI/Resources/food',
    },
    'pointer': {
        'directory': 'assets/UI/Pointer/',
    },
}

# Acronyms mapping (using frozenset for immutable keys would break dict access)
Acronym: Dict[str, Dict[str, str]] = {
    'resources': {
        ' ': 'grass',
        'W': 'tree',
        'G': 'gold',
        'F': 'food'
    },
    'buildings': {
        'A': 'archeryrange',
        'B': 'barracks',
        'C': 'camp',
        'F': 'farm',
        'H': 'house',
        'K': 'keep',
        'S': 'stable',
        'T': 'towncenter'
    },
    'units': {
        'a': 'archer',
        'h': 'horseman',
        's': 'swordsman',
        'v': 'villager'
    },
    'projectiles': {
        'a': 'arrow'
    }
}

# State mapping
states: Dict[int, str] = {
    0: 'idle',
    1: 'walk',
    2: 'attack',
    3: 'death',
    4: 'decay',
    5: 'task',
    7: 'inactive'
}

# Villager task mapping
villager_tasks: Dict[str, str] = {
    "attack": "attack_target",
    "collect": "collect_target",
    "build": "build_target",
    "stock": "stock_target",
    "repair": "build_target"  # repair utilise build_target comme cible
}

sprite_config = {
    'projectiles': {
        'arrow': {
            'directory': 'assets/projectiles/arrow/',
            'states': 1,
            'adjust_scale': TILE_SIZE / PROJECTILE_RATIO,
            'sheet_config': {'columns': 11, 'rows': 8},
        }
    },
    'buildings': {
        'towncenter': {
            'directory': 'assets/buildings/towncenter/',
            'states': 2,
            'adjust_scale': TILE_SIZE / BUILDING_RATIO,
            'sheet_config': {'columns': 10, 'rows': 10},
        },
        'barracks': {
            'directory': 'assets/buildings/barracks/',
            'states': 2,
            'adjust_scale': TILE_SIZE / BUILDING_RATIO,
            'sheet_config': {'columns': 10, 'rows': 10},
        },
        'stable': {
            'directory': 'assets/buildings/stable/',
            'states': 2,
            'adjust_scale': TILE_SIZE / BUILDING_RATIO,
            'sheet_config': {'columns': 10, 'rows': 10},
        },
        'archeryrange': {
            'directory': 'assets/buildings/archeryrange/',
            'states': 2,
            'adjust_scale': TILE_SIZE / BUILDING_RATIO,
            'sheet_config': {'columns': 10, 'rows': 10},
        },
        'keep': {
            'directory': 'assets/buildings/keep/',
            'states': 2,
            'adjust_scale': TILE_SIZE / BUILDING_RATIO,
            'sheet_config': {'columns': 10, 'rows': 10},
        },
        'camp': {
            'directory': 'assets/buildings/camp/',
            'states': 2,
            'adjust_scale': TILE_SIZE / BUILDING_RATIO,
            'sheet_config': {'columns': 10, 'rows': 10},
        },
        'house': {
            'directory': 'assets/buildings/house/',
            'states': 2,
            'adjust_scale': TILE_SIZE / BUILDING_RATIO,
            'sheet_config': {'columns': 10, 'rows': 10},
        },
        'farm': {
            'directory': 'assets/buildings/farm/',
            'states': 2,
            'adjust_scale': TILE_SIZE / 120,
            'sheet_config': {'columns': 10, 'rows': 10},
        },
    },
    'resources': {
        'grass': {
            'directory': 'assets/resources/grass/',
            'scale': (10 * TILE_SIZE // 2, 10 * TILE_SIZE // 4)
        },
        'gold': {
            'directory': 'assets/resources/gold/',
            'scale': (TILE_SIZE, TILE_SIZE),
            'variant': 6
        },
        'tree': {
            'directory': 'assets/resources/tree/',
            'scale': (TILE_SIZE, TILE_SIZE),
            'variant': 4
        }
    },
    'units': {
        'swordsman': {
            'directory': 'assets/units/swordsman/',
            'states': 5,
            'adjust_scale': TILE_SIZE / UNIT_RATIO,
            'sheet_config': {'columns': 30, 'rows': 16},
        },
        'villager': {
            'directory': 'assets/units/villager/',
            'states': 6,
            'adjust_scale': TILE_SIZE / UNIT_RATIO,
            'sheet_config': {'columns': 30, 'rows': 16},
        },
        'archer': {
            'directory': 'assets/units/archer/',
            'states': 5,
            'adjust_scale': TILE_SIZE / UNIT_RATIO,
            'sheet_config': {'columns': 30, 'rows': 16},
        },
        'horseman': {
            'directory': 'assets/units/horseman/',
            'states': 5,
            'adjust_scale': TILE_SIZE / UNIT_RATIO,
            'sheet_config': {'columns': 30, 'rows': 16},
        },
    },
}

# ----
# Menu Configuration
# ----
user_choices: Dict[str, any] = {
    "grid_width": 120,
    "grid_height": 120,
    "num_bots": 2,
    "bot_level": "lean",
    "gold_at_center": False,
    "load_game": False,
    "chosen_save": None,
    "validated": False,
    "index_terminal_display": 0,  # 0: GUI, 1: Terminal, 2: Both
    "bot_mode": "economique"
}

combo_scroll_positions: Dict[str, int] = {
    "width": 0,
    "height": 0,
    "nbot": 0,
    "lvl": 0,
    "bot_mode": 0
}

# Valid options (using tuples for immutability where appropriate)
VALID_GRID_SIZES: List[int] = list(range(100, 1000, 10))
VALID_BOTS_COUNT: List[int] = list(range(1, 56))
VALID_LEVELS: Tuple[str, ...] = ("lean", "mean", "marines", "DEBUG")
VALID_BOT_MODES: Tuple[str, ...] = ("economique", "defensif", "offensif")

RESOURCE_THRESHOLDS = Resources(food=150, gold=150, wood=100)