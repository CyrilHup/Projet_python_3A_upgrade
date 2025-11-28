import heapq
import math
import time
from collections import OrderedDict
from Controller.utils import get_snapped_angle, get_angle

# Cache LRU pour les chemins A*
_path_cache = OrderedDict()
MAX_PATH_CACHE_SIZE = 500
PATH_CACHE_TTL = 2.0  # Durée de vie du cache en secondes

def get_path_cache_key(start, goal):
    """Génère une clé de cache pour un chemin."""
    return (round(start[0]), round(start[1]), round(goal[0]), round(goal[1]))

def get_cached_path(start, goal):
    """Récupère un chemin depuis le cache s'il existe et est valide."""
    key = get_path_cache_key(start, goal)
    if key in _path_cache:
        cached_path, timestamp = _path_cache[key]
        if time.time() - timestamp < PATH_CACHE_TTL:
            _path_cache.move_to_end(key)
            # Retourner une copie du chemin (pour éviter les modifications)
            return list(cached_path)
        else:
            # Cache expiré
            del _path_cache[key]
    return None

def cache_path(start, goal, path):
    """Met en cache un chemin."""
    if not path:
        return
    
    key = get_path_cache_key(start, goal)
    _path_cache[key] = (list(path), time.time())
    _path_cache.move_to_end(key)
    
    # Nettoyer le cache si trop grand
    while len(_path_cache) > MAX_PATH_CACHE_SIZE:
        _path_cache.popitem(last=False)

def invalidate_path_cache_near(x, y, radius=5):
    """Invalide les chemins qui passent près d'une position (quand un obstacle change)."""
    keys_to_remove = []
    for key in _path_cache:
        start_x, start_y, goal_x, goal_y = key
        # Si le départ ou l'arrivée est proche de la position modifiée
        if (abs(start_x - x) <= radius and abs(start_y - y) <= radius) or \
           (abs(goal_x - x) <= radius and abs(goal_y - y) <= radius):
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del _path_cache[key]

def clear_path_cache():
    """Vide complètement le cache des chemins."""
    _path_cache.clear()


def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def get_neighbors(game_map, position):
    directions = [
        (1, 0), (0, 1), (-1, 0), (0, -1),
        (1, 1), (1, -1), (-1, 1), (-1, -1)
    ]
    neighbors = []
    for dx, dy in directions:
        neighbor = (position[0] + dx, position[1] + dy)
        if game_map.walkable_position(neighbor):
            neighbors.append(neighbor)
    return neighbors

def find_nearest_walkable_tile(rounded_goal, game_map):
    open_set = [(0, rounded_goal)]
    visited = set()

    while open_set:
        _, current = heapq.heappop(open_set)

        if game_map.walkable_position(current):
            return current

        visited.add(current)
        for neighbor in get_neighbors(game_map, current):
            if neighbor not in visited:
                distance = heuristic(neighbor, rounded_goal)
                heapq.heappush(open_set, (distance, neighbor))

    return None

def walkable_goal(start, rounded_goal, game_map):
    entities = game_map.grid.get(rounded_goal, None)
    entity = list(entities)[0] if entities else None
    float_offset = None
    if entity:
        angle = get_angle((entity.x, entity.y), start)
        offset_x = ((entity.size - 1) / 2) * math.cos(math.radians(angle))
        offset_y = ((entity.size - 1) / 2) * math.sin(math.radians(angle))
        float_goal = (entity.x + offset_x, entity.y + offset_y)
        float_offset = float_goal
        rg = (round(float_goal[0]), round(float_goal[1]))
        if game_map.walkable_position(rg):
            return rg, float_offset
        tile = find_nearest_walkable_tile(rg, game_map)
        return tile, float_offset
    return rounded_goal, None

def a_star(start, float_goal, game_map):
    """
    Algorithme A* avec cache LRU.
    Le cache permet de réutiliser les chemins calculés récemment.
    """
    # Vérifier le cache d'abord
    cached = get_cached_path(start, float_goal)
    if cached is not None:
        return cached
    
    rounded_goal = (round(float_goal[0]), round(float_goal[1]))
    if not game_map.walkable_position(rounded_goal):
        rounded_goal, float_building_goal = walkable_goal(start, rounded_goal, game_map)
    else:
        float_building_goal = None

    if not rounded_goal or not game_map.walkable_position(rounded_goal):
        return []

    open_set = []
    rs = (round(start[0]), round(start[1]))
    heapq.heappush(open_set, (0, rs))
    came_from = {}
    g_score = {rs: 0}
    f_score = {rs: heuristic(rs, rounded_goal)}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == rounded_goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            if float_building_goal and game_map.walkable_position((round(float_building_goal[0]), round(float_building_goal[1]))):
                path.append(float_building_goal)
            elif game_map.walkable_position(float_goal):
                path.append(float_goal)
            
            # Mettre en cache le résultat
            cache_path(start, float_goal, path)
            return path

        for neighbor in get_neighbors(game_map, current):
            tentative_g_score = g_score[current] + 1
            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + heuristic(neighbor, rounded_goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return []

