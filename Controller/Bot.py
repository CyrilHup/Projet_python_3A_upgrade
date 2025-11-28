# Chemin de C:/Users/cyril/OneDrive/Documents/INSA/3A/PYTHON_TEST/Projet_python\Controller\Bot.py
import math
import time
from Models.Team import *
from Settings.setup import RESOURCE_THRESHOLDS, TILE_SIZE
from Entity.Unit import Villager, Archer, Swordsman, Horseman
from Entity.Building import Building, Keep, Barracks, TownCentre, Camp, House, Farm, Stable, ArcheryRange
from Settings.setup import *
from Settings.entity_mapping import *
from Entity.Entity import *
from Entity.Unit import *
from Entity.Resource import *
from Models.Map import GameMap
from random import *
from AiUtils.aStar import a_star
from Controller.Decisonnode import * # Import DecisionNode and trees
from Controller.terminal_display_debug import debug_print

# Debug flag pour le Bot - mettre à True pour activer les logs détaillés
BOT_DEBUG = True
_bot_debug_last = {}  # Dictionnaire pour throttle par message

def bot_debug(message, throttle_key=None, interval=5.0):
    """Affiche un message de debug avec throttling par clé
    
    Args:
        message: Le message à afficher
        throttle_key: Clé unique pour le throttling (si None, affiche toujours)
        interval: Intervalle minimum entre les messages de même clé (secondes)
    """
    if not BOT_DEBUG:
        return
    
    if throttle_key is None:
        print(f"[BOT] {message}")
        return
    
    current = time.time()
    if throttle_key not in _bot_debug_last or current - _bot_debug_last[throttle_key] >= interval:
        _bot_debug_last[throttle_key] = current
        print(f"[BOT] {message}")


class Bot:
    # Cache TTL for is_under_attack() in seconds
    UNDER_ATTACK_CACHE_TTL = 0.5
    
    def __init__(self, team, game_map, players, mode, difficulty='medium'):
        self.team = team
        self.game_map = game_map
        self.difficulty = difficulty
        self.mode = mode

        self.enemies = [team for team in game_map.players if team.teamID != self.team.teamID]
        self.players_target = game_map.game_state.get('players_target') if game_map.game_state else [None] * len(players)

        self.attacking_enemies = None
        
        # Cache for is_under_attack()
        self._under_attack_cache = None
        self._under_attack_cache_time = 0

        self.priority = None
        self.ATTACK_RADIUS = 5  # Rayon d'attaque pour détecter les ennemis
        self.PRIORITY_UNITS = {
            'a': 3,  # Archers
            's': 2,  # Swordsmen
            'h': 1   # Horsemen
        }
        
        # Créer l'arbre de décision UNE SEULE FOIS à l'initialisation
        self.decision_tree = self.create_mode_decision_tree()
        
        # Debug counters
        self._last_debug_time = 0
        self._debug_interval = 5.0  # Afficher le debug toutes les 5 secondes
        
        # Cooldown pour éviter la réallocation trop fréquente
        self._last_reallocation_time = 0
        self._reallocation_cooldown = 2.0  # Attendre 2 secondes entre les réallocations

    def update(self, game_map, dt):
        # Mettre à jour la référence à game_map au cas où elle change
        self.game_map = game_map
        
        # Debug périodique de l'état du bot
        current_time = time.time()
        if current_time - self._last_debug_time > self._debug_interval:
            self._debug_bot_state()
            self._last_debug_time = current_time
        
        # PRIORITÉ 1: Assigner les villagers IDLE - c'est le plus important!
        self._assign_idle_villagers()
        
        # PRIORITÉ 2: Évaluer l'arbre de décision pour les actions stratégiques
        if self.decision_tree:
            self.decision_tree.evaluate()
    
    def _assign_idle_villagers(self):
        """Assigne une tâche aux villagers qui n'en ont pas - LOGIQUE SIMPLE"""
        idle_villagers = [
            u for u in self.team.units 
            if isinstance(u, Villager) and u.isAlive() 
            and u.task is None  # Seulement ceux sans tâche
        ]
        
        if not idle_villagers:
            return
        
        for villager in idle_villagers:
            # 1. S'il porte des ressources, aller les déposer
            if villager.carry and villager.carry.total() > 0:
                drop_point = self._find_nearest_drop_point(villager)
                if drop_point:
                    villager.set_task('stock', drop_point)
                    continue
            
            # 2. Chercher une ressource à collecter
            resource = self._find_nearest_resource(villager)
            if not resource:
                resource = self._find_any_resource(villager)
            
            if resource:
                villager.set_target(resource)
                continue
            
            # 3. Si vraiment rien à faire, essayer de trouver un chantier de construction
            construction_site = self._find_nearest_construction_site(villager)
            if construction_site:
                villager.set_task('build', construction_site)
                continue

            # 4. Si toujours rien, aller vers le TownCentre (point de ralliement)
            town_centre = next((b for b in self.team.buildings if isinstance(b, TownCentre)), None)
            if town_centre and math.dist((villager.x, villager.y), (town_centre.x, town_centre.y)) > 10:
                villager.set_destination((town_centre.x, town_centre.y), self.game_map)
                continue

            bot_debug(f"Team {self.team.teamID}: Villager sans ressource à collecter!", f"no_resource_{self.team.teamID}", 10.0)
    
    def _find_any_resource(self, villager):
        """Trouve une ressource n'importe où sur la carte (fallback)"""
        # 1. D'abord chercher les Farms construites de notre équipe
        for building in self.team.buildings:
            if isinstance(building, Farm) and building.isBuilt() and building.isAlive():
                return building
        
        # 2. Sinon chercher la ressource la plus proche sur toute la map
        vx, vy = villager.x, villager.y
        best_resource = None
        best_distance = float('inf')
        
        # Optimisation: ne pas scanner toute la map si possible, mais ici c'est un fallback
        # On parcourt toutes les ressources connues de la map
        for pos, entities in self.game_map.resources.items():
            for entity in entities:
                if entity.isAlive() and (isinstance(entity, Tree) or isinstance(entity, Gold)):
                    dist = abs(vx - entity.x) + abs(vy - entity.y)
                    if dist < best_distance:
                        best_distance = dist
                        best_resource = entity
        
        return best_resource

    def _find_nearest_construction_site(self, villager):
        """Trouve le chantier de construction le plus proche"""
        sites = [b for b in self.team.buildings if not b.isBuilt() and b.isAlive()]
        if not sites:
            return None
        return min(sites, key=lambda b: abs(villager.x - b.x) + abs(villager.y - b.y))

    def _find_nearest_drop_point(self, villager):
        """Trouve le point de dépôt le plus proche"""
        drop_points = [b for b in self.team.buildings if b.resourceDropPoint and b.isBuilt()]
        if not drop_points:
            return None
        return min(drop_points, key=lambda dp: abs(villager.x - dp.x) + abs(villager.y - dp.y))
    
    def _find_nearest_resource(self, villager):
        """Trouve la ressource la plus proche (Tree, Gold, ou Farm construite)"""
        vx, vy = villager.x, villager.y
        best_resource = None
        best_distance = float('inf')
        
        # 1. D'abord chercher les Farms construites de notre équipe (priorité)
        for building in self.team.buildings:
            if isinstance(building, Farm) and building.isBuilt() and building.isAlive():
                dist = abs(vx - building.x) + abs(vy - building.y)
                if dist < best_distance:
                    best_distance = dist
                    best_resource = building
        
        # Si on a une Farm proche, l'utiliser
        if best_resource and best_distance < 20:
            return best_resource
        
        # 2. Sinon chercher Tree ou Gold sur la map
        for radius in range(1, 30):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) != radius and abs(dy) != radius:
                        continue  # Seulement le périmètre
                    
                    pos = (int(vx) + dx, int(vy) + dy)
                    entities = self.game_map.resources.get(pos)
                    if entities:
                        for entity in entities:
                            if entity.isAlive() and (isinstance(entity, Tree) or isinstance(entity, Gold)):
                                dist = abs(dx) + abs(dy)
                                if dist < best_distance:
                                    best_distance = dist
                                    best_resource = entity
            
            if best_resource:
                break
        
        return best_resource
    
    def _debug_bot_state(self):
        """Affiche l'état actuel du bot pour le debug"""
        team_id = self.team.teamID
        villagers = [u for u in self.team.units if isinstance(u, Villager)]
        military = [u for u in self.team.units if not isinstance(u, Villager)]
        
        # Compter les états des villagers
        villager_states = {}
        villager_tasks = {}
        for v in villagers:
            state = v.state or 'none'
            task = v.task or 'none'
            villager_states[state] = villager_states.get(state, 0) + 1
            villager_tasks[task] = villager_tasks.get(task, 0) + 1
        
        # Compter les états des unités militaires
        military_states = {}
        for m in military:
            has_target = 'with_target' if m.attack_target else 'no_target'
            has_path = 'moving' if m.path else 'static'
            key = f"{has_target}/{has_path}"
            military_states[key] = military_states.get(key, 0) + 1
        
        bot_debug(f"=== Team {team_id} ({self.mode}) ===")
        bot_debug(f"  Resources: F={self.team.resources.food} W={self.team.resources.wood} G={self.team.resources.gold}")
        bot_debug(f"  Pop: {self.team.population}/{self.team.maximum_population}")
        bot_debug(f"  Villagers ({len(villagers)}): states={villager_states} tasks={villager_tasks}")
        bot_debug(f"  Military ({len(military)}): {military_states}")
        
        # Détail des villagers bloqués (idle sans tâche)
        blocked_villagers = [v for v in villagers if v.state == 'idle' and v.task is None]
        if blocked_villagers:
            bot_debug(f"  ⚠ {len(blocked_villagers)} villagers IDLE sans tâche!")

    def set_priority(self, priority):
        self.priority = priority

    def get_resource_shortage(self):
        """Détermine quelle ressource récolter en priorité"""
        resources = self.team.resources
        
        # 1. Vérifier les ressources pour les bâtiments nécessaires
        needed_buildings = self.check_building_needs()
        if needed_buildings:
            # On regarde le premier bâtiment nécessaire
            first_needed = needed_buildings[0]
            if first_needed in building_class_map:
                building_class = building_class_map[first_needed]
                temp_b = building_class(team=self.team.teamID)
                cost = temp_b.cost
                
                if resources.wood < cost.wood:
                    return Tree
                if resources.food < cost.food:
                    return Farm
                if resources.gold < cost.gold:
                    return Gold

        # 2. Si on n'a pas assez de bois pour construire une ferme (60 wood), prioriser le bois
        if resources.wood < 60:
            return Tree
        
        # 3. Sinon, vérifier les pénuries dans l'ordre de priorité
        RESOURCE_MAPPING = {
            "food": Farm,
            "wood": Tree,
            "gold": Gold,
        }
        
        for resource in ["food", "wood", "gold"]:
            if getattr(resources, resource) < getattr(RESOURCE_THRESHOLDS, resource):
                return RESOURCE_MAPPING[resource]
        
        return None  # Aucune pénurie détectée



    def reallocate_villagers(self, resource_type):
        """VERSION OPTIMISÉE - resource_type est Farm, Tree, ou Gold (classes)"""
        # Cooldown pour éviter la réallocation trop fréquente
        current_time = time.time()
        if current_time - self._last_reallocation_time < self._reallocation_cooldown:
            return
        
        # Debug: montrer l'état de tous les villagers
        all_villagers = [u for u in self.team.units if isinstance(u, Villager) and u.isAlive()]
        villager_states = {}
        for v in all_villagers:
            key = f"{v.state}/{v.task}"
            villager_states[key] = villager_states.get(key, 0) + 1
        bot_debug(f"Team {self.team.teamID}: {len(all_villagers)} villagers - états: {villager_states}", f"villager_states_{self.team.teamID}", 5.0)
        
        # Prendre les villagers disponibles pour réallocation
        available_villagers = []
        for unit in self.team.units:
            if not isinstance(unit, Villager):
                continue
            if not unit.isAlive():
                continue
            
            # Villager idle (state == 'idle') ou sans tâche ou disponible
            if unit.state == 'idle' or unit.task is None or unit.isAvailable():
                available_villagers.append(unit)
                continue
            
            # Villager qui collecte une ressource différente de celle demandée
            if unit.task == 'collect' and unit.collect_target:
                current_resource_type = type(unit.collect_target)
                # Si le villager collecte une ressource différente, on peut le réallouer
                if current_resource_type != resource_type and resource_type != Farm:
                    available_villagers.append(unit)
        
        if not available_villagers:
            bot_debug(f"Team {self.team.teamID}: Aucun villager disponible (besoin: {resource_type.__name__})", f"no_villager_{self.team.teamID}", 5.0)
            return
            
        # Traiter jusqu'à 3 villagers à la fois
        villagers_to_process = available_villagers[:3]
        
        drop_points = [b for b in self.team.buildings if b.resourceDropPoint]
        if not drop_points:
            bot_debug(f"Team {self.team.teamID}: Aucun point de dépôt!")
            return
        
        resource_name = resource_type.__name__ if resource_type else "None"
        bot_debug(f"Team {self.team.teamID}: Réallocation de {len(villagers_to_process)} villagers vers {resource_name}")
        
        # Marquer qu'une réallocation a eu lieu
        self._last_reallocation_time = current_time
        
        for villager in villagers_to_process:
            nearest_drop_point = min(
                drop_points,
                key=lambda dp: abs(villager.x - dp.x) + abs(villager.y - dp.y)
            )

            # Si on a besoin de nourriture (Farm)
            if resource_type is Farm:
                # Ne prendre que les fermes construites (pas en construction)
                available_farms = [farm for farm in self.team.buildings 
                                   if isinstance(farm, Farm) and farm.isBuilt() and farm.isAlive()]
                if available_farms:
                    villager.set_target(available_farms[0])
                    bot_debug(f"Team {self.team.teamID}: Villager assigné à ferme existante")
                    continue
                else:
                    # Pas de ferme disponible - rediriger vers le bois
                    # La construction de Farm sera gérée par build_structure()
                    bot_debug(f"Team {self.team.teamID}: Pas de Farm, villager assigné à Tree", f"no_farm_{self.team.teamID}", 5.0)
                    self._assign_villager_to_resource(villager, Tree, nearest_drop_point)
                    continue

            # Chercher des ressources proches du drop point (Tree pour wood, Gold pour gold)
            self._assign_villager_to_resource(villager, resource_type, nearest_drop_point)
    
    def _assign_villager_to_resource(self, villager, resource_type, nearest_drop_point):
        """Assigne un villager à une ressource proche du drop point"""
        nx, ny = int(nearest_drop_point.x), int(nearest_drop_point.y)
        best_resource = None
        best_distance = float('inf')
        
        for radius in range(1, 20):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) == radius or abs(dy) == radius:
                        pos = (nx + dx, ny + dy)
                        entities = self.game_map.resources.get(pos)
                        if entities:
                            for entity in entities:
                                if isinstance(entity, resource_type) and entity.isAlive():
                                    dist = abs(dx) + abs(dy)
                                    if dist < best_distance:
                                        best_distance = dist
                                        best_resource = entity
            if best_resource:
                break
        
        if best_resource:
            villager.set_target(best_resource)
            bot_debug(f"Team {self.team.teamID}: Villager assigné à {resource_type.__name__} à ({best_resource.x:.0f},{best_resource.y:.0f})")
        else:
            bot_debug(f"Team {self.team.teamID}: Aucune ressource {resource_type.__name__} trouvée!")

    def priority7(self):
        resource_shortage = self.get_resource_shortage()
        if resource_shortage is None:
            return  # Aucune pénurie, ne rien faire
        self.reallocate_villagers(resource_shortage)


    def search_for_target(self, unit, enemy_team, attack_mode=True):
        """Cherche une cible pour l'unité parmi l'équipe ennemie.
        
        Returns:
            bool: True si une cible a été trouvée et assignée, False sinon
        """
        if enemy_team is None:
            return False
        if not enemy_team.units and not enemy_team.buildings:
            return False
            
        closest_distance = float("inf")
        closest_entity = None
        keeps = [keep for keep in enemy_team.buildings if isinstance(keep, Keep) and keep.isAlive()]
        
        # Chercher d'abord parmi les unités militaires ennemies (exclure les villageois)
        military_targets = [enemy for enemy in enemy_team.units 
                          if not isinstance(enemy, Villager) and enemy.isAlive()]

        for enemy in military_targets:
            dist = math.dist((unit.x, unit.y), (enemy.x, enemy.y))
            if dist < closest_distance:
                closest_distance = dist
                closest_entity = enemy
        
        # Si pas de cible militaire et en mode attaque, chercher villageois et bâtiments
        if attack_mode and closest_entity is None:
            villager_targets = [enemy for enemy in enemy_team.units 
                               if isinstance(enemy, Villager) and enemy.isAlive()]
            for enemy in villager_targets:
                dist = math.dist((unit.x, unit.y), (enemy.x, enemy.y))
                if dist < closest_distance:
                    closest_distance = dist
                    closest_entity = enemy
            
            for enemy_building in enemy_team.buildings:
                if enemy_building.isAlive():
                    dist = math.dist((unit.x, unit.y), (enemy_building.x, enemy_building.y))
                    if dist < closest_distance:
                        closest_distance = dist
                        closest_entity = enemy_building

        # En mode attaque, prioriser les Keeps
        if attack_mode and keeps:
            for keep in keeps:
                dist = math.dist((unit.x, unit.y), (keep.x, keep.y))
                if dist < closest_distance:
                    closest_distance = dist
                    closest_entity = keep
        
        # Si la cible est proche d'un keep ennemi, cibler le keep d'abord
        if closest_entity is not None and keeps and attack_mode:
            for keep in keeps:
                dist = math.dist((keep.x, keep.y), (closest_entity.x, closest_entity.y))
                if dist < keep.attack_range:
                    closest_entity = keep
                    break

        unit.set_target(closest_entity)
        return unit.attack_target is not None

    def modify_target(self, player, target, players_target):
        players_target[player.teamID] = target
        for unit in player.units:
            unit.set_target(None)

    def choose_target(self, players, selected_player, players_target):
        count_max = 300
        target = None
        for enemy_team in players:
            if enemy_team != selected_player:
                count = sum(1 for unit in enemy_team.units if not isinstance(unit, Villager))
                count += sum(1 for building in enemy_team.buildings if not isinstance(building, Keep))
                if count < count_max:
                    target = enemy_team
                    count_max = count
        if target != None:
            self.modify_target(selected_player, target, players_target)
        return target != None

    def priority_2(self, players, selected_player, players_target):
        if players_target[selected_player.teamID] != None:
            return False
        return self.choose_target(players, selected_player, players_target)

    def manage_battle(self, selected_player, players_target, players, game_map, dt):
        """Gère le combat pour un joueur sélectionné."""
        enemy = players_target[selected_player.teamID]
        attack_mode = True
        
        # Vérifier si on est ciblé par un autre joueur
        for i in range(len(players_target)):
            if players_target[i] == selected_player:
                for team in players:
                    if team.teamID == i:
                        players_target[selected_player.teamID] = None
                        enemy = team
                        attack_mode = False
                        break
                break
        
        # Assigner des cibles aux unités si l'ennemi existe et a des unités/bâtiments
        if enemy is not None and (len(enemy.units) != 0 or len(enemy.buildings) != 0):
            for unit in selected_player.units:
                if not isinstance(unit, Villager) or (len(selected_player.units) == 0 and not attack_mode):
                    if unit.attack_target is None or not unit.attack_target.isAlive():
                        self.search_for_target(unit, enemy, attack_mode)
        else:
            self.modify_target(selected_player, None, players_target)
        
        # Reset si plus d'unités militaires
        if self.get_military_unit_count(selected_player) == 0:
            self.modify_target(selected_player, None, players_target)

    def get_military_unit_count(self, player):
        return len(self.get_military_units(player))

    def create_mode_decision_tree(self): 
        if self.mode == 'offensif':
            return create_offensive_decision_tree(self)
        elif self.mode == 'defensif':
            return create_defensive_decision_tree(self)
        elif self.mode == 'economic':
            return create_economic_decision_tree(self)
        else:
            return create_default_decision_tree(self)

    def get_military_units(self, player=None): # Modified to accept player, default to self
        player_to_check = player if player else self.team
        return [unit for unit in player_to_check.units if not isinstance(unit, Villager)]

    def can_train_unit(self, unit_type):
        """Vérifie si on peut former une unité (ressources et bâtiment disponible)"""
        unit_instance = unit_type(team=self.team.teamID)
        if not self.team.resources.has_enough(unit_instance.cost.get()):
            return False, "resources"
            
        BUILDING_FOR_UNIT = {
            Villager: 'T',    # TownCentre
            Archer: 'A',      # ArcheryRange
            Swordsman: 'B',   # Barracks
            Horseman: 'S'     # Stable
        }
        
        required_building = BUILDING_FOR_UNIT.get(unit_type)
        # Vérifier que le bâtiment existe ET est construit
        has_building = any(b.acronym == required_building and b.isBuilt() for b in self.team.buildings)
        
        return has_building, "building"

    def needs_population_buildings(self):
        """Vérifie si on a besoin d'augmenter la population maximum"""
        # Si proche de la limite de population
        if self.team.population >= self.team.maximum_population - 5:
            # Si on n'a pas atteint la limite absolue
            if self.team.maximum_population < MAXIMUM_POPULATION:
                return True
        return False

    def train_units(self, unit_type):
        can_train, reason = self.can_train_unit(unit_type)
        
        # Vérifier si on est proche de la limite de population
        if self.needs_population_buildings():
            bot_debug(f"Team {self.team.teamID}: Needs pop buildings (pop={self.team.population}/{self.team.maximum_population})")
            # Priorité aux bâtiments qui augmentent la population
            for building_type in ["House", "TownCentre"]:
                if building_type in self.check_building_needs():
                    self.build_structure(1)
                    return False

        if not can_train:
            bot_debug(f"Team {self.team.teamID}: Cannot train {unit_type.__name__}, reason={reason}", f"train_{self.team.teamID}_{unit_type.__name__}", 10.0)
            if reason == "resources":
                # Allouer des villageois à la récolte des ressources manquantes
                unit_instance = unit_type(team=self.team.teamID)
                if unit_instance.cost.wood > self.team.resources.wood:
                    self.reallocate_villagers(Tree)
                elif unit_instance.cost.gold > self.team.resources.gold:
                    self.reallocate_villagers(Gold)
                elif unit_instance.cost.food > self.team.resources.food:
                    self.reallocate_villagers(Farm)
            elif reason == "building":
                # Ajouter le bâtiment requis aux besoins
                UNIT_TO_BUILDING = {
                    Villager: "TownCentre",
                    Archer: "ArcheryRange",
                    Swordsman: "Barracks",
                    Horseman: "Stable"
                }
                needed_building = UNIT_TO_BUILDING.get(unit_type)
                if needed_building:
                    if needed_building not in self.check_building_needs():
                        self.build_structure(1)  # Construire le bâtiment nécessaire
            return False

        # Si on peut former l'unité, on la forme
        UNIT_TO_BUILDING_MAP = {
            Villager: 'T',
            Archer: 'A', 
            Swordsman: 'B',
            Horseman: 'S'
        }
        
        building_acronym = UNIT_TO_BUILDING_MAP.get(unit_type)
        if building_acronym:
            for building in self.team.buildings:
                if building.acronym == building_acronym:
                    if hasattr(building, 'add_to_training_queue'):
                        return building.add_to_training_queue(self.team)
        return False

    def balance_units(self):
        villager_count = sum(1 for unit in self.team.units if isinstance(unit, Villager))
        military_units = self.get_military_units()
        military_count = len(military_units)

        # Priorité à la formation de villageois si peu nombreux
        if villager_count < 20:
            success = self.train_units(Villager)
            if success:
                bot_debug(f"Team {self.team.teamID}: Training villager (have {villager_count})", f"training_{self.team.teamID}", 5.0)
                return True
            else:
                bot_debug(f"Team {self.team.teamID}: Failed to train villager (have {villager_count})", f"train_fail_{self.team.teamID}", 10.0)

        # Formation d'unités militaires si ressources suffisantes
        if military_count < 30:
            unit_priorities = [
                (self.PRIORITY_UNITS.get('a', 0), Archer),
                (self.PRIORITY_UNITS.get('s', 0), Swordsman),
                (self.PRIORITY_UNITS.get('h', 0), Horseman)
            ]
            
            # Trier par priorité
            unit_priorities.sort(reverse=True)
            
            # Essayer de former l'unité avec la plus haute priorité
            for priority, unit_type in unit_priorities:
                if self.train_units(unit_type):
                    bot_debug(f"Team {self.team.teamID}: Training {unit_type.__name__}")
                    return True

        return False

    def is_under_attack(self):
        """Vérifie si l'équipe est attaquée - VERSION OPTIMISÉE AVEC CACHE TTL
        
        Returns:
            bool: True si des ennemis sont détectés près des bâtiments, False sinon
        """
        current_time = time.time()
        
        # Vérifier si le cache est encore valide
        if (self._under_attack_cache is not None and 
            current_time - self._under_attack_cache_time < Bot.UNDER_ATTACK_CACHE_TTL):
            return self._under_attack_cache
        
        my_team_id = self.team.teamID
        
        # Utiliser le spatial hash si disponible
        if hasattr(self.game_map, 'spatial_hash'):
            for building in self.team.buildings:
                # Chercher les entités proches de chaque bâtiment
                nearby = self.game_map.get_entities_in_area(building.x, building.y, 5)
                for entity in nearby:
                    if isinstance(entity, Unit) and entity.team != my_team_id:
                        self.attacking_enemies = self._get_attacking_enemies_optimized(my_team_id)
                        self._under_attack_cache = True
                        self._under_attack_cache_time = current_time
                        return True
        else:
            # Fallback: méthode originale
            check_positions = set()
            for building in self.team.buildings:
                bx, by = int(building.x), int(building.y)
                for dx in range(-5, 6):
                    for dy in range(-5, 6):
                        check_positions.add((bx + dx, by + dy))
            
            for tile in check_positions:
                entities = self.game_map.grid.get(tile)
                if entities:
                    for entity in entities:
                        if isinstance(entity, Unit) and entity.team != my_team_id:
                            self.attacking_enemies = self._get_attacking_enemies(check_positions, my_team_id)
                            self._under_attack_cache = True
                            self._under_attack_cache_time = current_time
                            return True
        
        self.attacking_enemies = []
        self._under_attack_cache = False
        self._under_attack_cache_time = current_time
        return False
    
    def _get_attacking_enemies_optimized(self, my_team_id):
        """Récupère la liste des ennemis attaquant en utilisant spatial hash."""
        attacking_enemies = []
        for building in self.team.buildings:
            nearby = self.game_map.get_entities_in_area(building.x, building.y, 5)
            for entity in nearby:
                if isinstance(entity, Unit) and entity.team != my_team_id:
                    attacking_enemies.append(entity)
                    if len(attacking_enemies) >= 10:
                        return attacking_enemies
        return attacking_enemies
    
    def _get_attacking_enemies(self, check_positions, my_team_id):
        """Récupère la liste des ennemis attaquant (appelé après is_under_attack)"""
        attacking_enemies = []
        for tile in check_positions:
            entities = self.game_map.grid.get(tile)
            if entities:
                for entity in entities:
                    if isinstance(entity, Unit) and entity.team != my_team_id:
                        attacking_enemies.append(entity)
                        if len(attacking_enemies) >= 10:
                            return attacking_enemies
        return attacking_enemies
        
    def get_critical_points(self):
        if not self.team.buildings:
            return []
        critical_points = [building for building in self.team.buildings if building.hp / building.max_hp < 0.3]
        critical_points.sort(key=lambda b: b.hp / b.max_hp)
        return critical_points

    def build_defensive_structure(self, building_type, num_builders):
        point = self.find_building_location(building_type)  # Fix: Changed from find_build_location to find_building_location
        if point:  # Add check for None return value
            x, y = point
            return self.team.build(building_type, x, y, num_builders, self.game_map)
        return False  # Return False if no suitable location found

    def gather_units_for_defense(self, units_per_target=2):
        """Rassemble les unités militaires pour défendre contre les ennemis détectés"""
        # Utiliser la liste des ennemis mise en cache par is_under_attack()
        attacking_enemies = getattr(self, 'attacking_enemies', [])
        if not attacking_enemies:
            return

        # Filtrer les ennemis morts
        attacking_enemies = [e for e in attacking_enemies if e.isAlive()]
        if not attacking_enemies:
            return

        # Dictionary to track the number of units assigned to each target
        target_counts = {}
        
        # Récupérer uniquement les unités militaires disponibles
        available_units = [unit for unit in self.team.units 
                         if not isinstance(unit, Villager) 
                         and (not unit.attack_target or not unit.attack_target.isAlive())]

        # Assigner les unités aux cibles
        for unit in available_units:
            # Trouver la cible la plus proche qui n'a pas assez d'unités assignées
            closest_enemy = None
            min_distance = float('inf')
            
            for enemy in attacking_enemies:
                if enemy not in target_counts:
                    target_counts[enemy] = 0
                
                if target_counts[enemy] < units_per_target:
                    dist = math.dist((unit.x, unit.y), (enemy.x, enemy.y))
                    if dist < min_distance:
                        min_distance = dist
                        closest_enemy = enemy
            
            if closest_enemy:
                unit.set_target(closest_enemy)
                target_counts[closest_enemy] = target_counts.get(closest_enemy, 0) + 1

    def defend_under_attack(self):
        #self.modify_target( None, players_target) # players_target is not used in defend_under_attack
        self.gather_units_for_defense()
        self.balance_units()
        self.build_defensive_structure("Keep", 3)
        #self.manage_battle(self.team,None,enemy_team,self.game_map, dt) # players_target is None here

    def priorty1(self):
        self.defend_under_attack()

    def adjust_priorities(self, enemy_teams):
        if not isinstance(enemy_teams, list):
            enemy_teams = [enemy_teams]

        enemy_horsemen = 0
        enemy_archers = 0
        enemy_swordsmen = 0

        for enemy_team in enemy_teams:
            enemy_horsemen += sum(1 for unit in enemy_team.units if isinstance(unit, Horseman))
            enemy_archers += sum(1 for unit in enemy_team.units if isinstance(unit, Archer))
            enemy_swordsmen += sum(1 for unit in enemy_team.units if isinstance(unit, Swordsman))

        HORSEMEN_THRESHOLD = 5
        ARCHERS_THRESHOLD = 7
        SWORDSMEN_THRESHOLD = 6

        if enemy_horsemen > HORSEMEN_THRESHOLD:
            self.PRIORITY_UNITS['a'] = 4

        if enemy_archers > ARCHERS_THRESHOLD:
            self.PRIORITY_UNITS['s'] = 3

        if enemy_swordsmen > SWORDSMEN_THRESHOLD:
            self.PRIORITY_UNITS['h'] = 2

    def choose_attack_composition(self):
        units_by_type = {
            Archer: 3,
            Swordsman: 1,
            Horseman: 1
        }

        selected_units = []

        for unit_type, limit in units_by_type.items():
            available_units = [unit for unit in self.team.units if isinstance(unit, unit_type)]

            selected_units.extend(available_units[:limit])

            if len(selected_units) >= sum(units_by_type.values()):
                break

        return selected_units

    def maintain_army(self):
        military_count = len(self.get_military_units())

        if military_count < 20:
            self.balance_units()
        else:
            attack_composition = self.choose_attack_composition()

            for unit in attack_composition:
                if not isinstance(unit, Villager):
                    # Vérifier si l'unité est idle (pas de cible d'attaque et pas de path)
                    is_idle = (not unit.attack_target or not unit.attack_target.isAlive()) and not unit.path
                    if is_idle:
                        # Chercher une cible parmi les ennemis
                        for enemy_team in self.enemies:
                            if self.search_for_target(unit, enemy_team, True):
                                break

    def check_building_needs(self):
        """VERSION OPTIMISÉE - Vérifie quels bâtiments sont nécessaires"""
        # Compter les types de bâtiments une seule fois
        building_counts = {}
        for building in self.team.buildings:
            btype = type(building)
            building_counts[btype] = building_counts.get(btype, 0) + 1
        
        needed_buildings = []
        
        # Vérifier les bâtiments de base manquants
        essential_buildings = [
            (TownCentre, "TownCenter"),
            (House, "House"),
            (Camp, "Camp"),
            (Barracks, "Barracks"),
        ]
        
        for building_class, building_name in essential_buildings:
            if building_class not in building_counts:
                needed_buildings.append(building_name)

        # Logique dynamique pour les fermes (1 ferme pour 4 villageois)
        num_villagers = sum(1 for u in self.team.units if isinstance(u, Villager))
        num_farms = building_counts.get(Farm, 0)
        desired_farms = max(1, num_villagers // 3)
        
        if num_farms < desired_farms:
            needed_buildings.append("Farm")
        
        # Ajouter des maisons si proche de la limite de population
        if self.needs_population_buildings():
            if "House" not in needed_buildings:
                needed_buildings.append("House")
        
        # Bâtiments avancés seulement si prêt à l'expansion
        if self.is_ready_to_expand():
            advanced_buildings = [
                (ArcheryRange, "ArcheryRange"),
                (Stable, "Stable"),
                (Keep, "Keep"),
            ]
            for building_class, building_name in advanced_buildings:
                if building_class not in building_counts:
                    needed_buildings.append(building_name)
        
        return needed_buildings

    # Cache pour les tailles de bâtiments
    _building_size_cache = {}
    
    def find_building_location(self, building_type):
        # Utiliser le cache pour la taille du bâtiment
        if building_type not in Bot._building_size_cache:
            building_class = building_class_map[building_type]
            temp_instance = building_class(team=0)
            Bot._building_size_cache[building_type] = temp_instance.size
        
        building_size = Bot._building_size_cache[building_type]

        # Chercher autour d'un bâtiment existant au lieu de toute la zone
        if self.team.buildings:
            ref_building = next(iter(self.team.buildings))  # Prendre le premier élément du set
            ref_x, ref_y = int(ref_building.x), int(ref_building.y)
            
            # Chercher dans un rayon de 15
            for radius in range(1, 16):
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        if abs(dx) == radius or abs(dy) == radius:  # Seulement le périmètre
                            x, y = ref_x + dx, ref_y + dy
                            if self.game_map.buildable_position(x, y, building_size):
                                return (x, y)
        
        return None

    def can_build_building(self, building_class):
        """Check if resources are sufficient to build a building."""
        building_cost = building_class.cost
        return (self.team.resources["wood"] >= building_cost.wood and
                self.team.resources["gold"] >= building_cost.gold and
                self.team.resources["food"] >= building_cost.food)

    # def buildBuilding(self, building, clock, nb, game_map):
    #     """Build a building if resources are sufficient."""
    #     if not self.can_build_building(building.__class__):
    #         return False

    #     location = self.find_building_location(building.__class__.__name__)  # Find location based on building type name
    #     if location:
    #         x, y = location
    #         building.x, building.y = x, y # Set building position before adding to game map
    #         return self.team.buildBuilding(building, clock, nb, game_map) # Delegate to team's buildBuilding

    def build_structure(self, num_builders=1):
        needed_buildings = self.check_building_needs()
        if not needed_buildings:
            return False

        for building_type in needed_buildings:
            if building_type in building_class_map:
                building_class = building_class_map[building_type]

                # Créer une instance temporaire pour accéder à `cost`
                building_instance = building_class(team=self.team.teamID)
                building_cost = building_instance.cost

                # Accès aux ressources via les attributs de l'instance `cost`
                if (self.team.resources.food >= building_cost.food and
                    self.team.resources.wood >= building_cost.wood and
                    self.team.resources.gold >= building_cost.gold):

                    location = self.find_building_location(building_type)
                    if location:
                        x, y = location

                        # Vérifier que self.game_map est un objet de type GameMap
                        if not isinstance(self.game_map, GameMap):
                            return False

                        # Construire le bâtiment
                        building = building_class(team=self.team.teamID, x=x, y=y)
                        if self.team.build(building_type, x, y, num_builders, self.game_map):  # Passez le nom du type de bâtiment ici
                            return True
        return False

    def is_ready_to_expand(self):
        """Vérifie si le bot est prêt à s'étendre"""
        # Vérifier qu'on a une économie stable
        # Ne pas utiliser get_resource_shortage() pour éviter la récursion infinie
        resources = self.team.resources
        for resource in ["food", "wood", "gold"]:
            if getattr(resources, resource) < getattr(RESOURCE_THRESHOLDS, resource):
                return False
            
        # Vérifier qu'on a une armée suffisante
        military_count = self.get_military_unit_count(self.team)
        if military_count < 15:  # Minimum d'unités pour attaquer
            return False
            
        # Vérifier qu'on a des bâtiments de base
        has_essential_buildings = all(
            any(isinstance(b, building_type) for b in self.team.buildings)
            for building_type in [TownCentre, Keep, Barracks]
        )
        if not has_essential_buildings:
            return False
            
        return True

    def manage_expansion(self):
        """Gère l'expansion du territoire via l'attaque"""
        # Trouver l'ennemi le plus faible
        weakest_enemy = None
        min_military = float('inf')
        
        for enemy in self.enemies:
            enemy_military = self.get_military_unit_count(enemy)
            if enemy_military < min_military:
                min_military = enemy_military
                weakest_enemy = enemy
                
        if weakest_enemy:
            # Organiser les troupes pour l'attaque
            military_units = self.get_military_units()
            # Envoyer 70% des unités militaires à l'attaque
            attack_force = military_units[:int(len(military_units) * 0.7)]
            
            for unit in attack_force:
                # Chercher en priorité les bâtiments qui augmentent la population
                target = None
                for building in weakest_enemy.buildings:
                    if isinstance(building, (TownCentre, House)):
                        target = building
                        break
                        
                if not target:  # Si pas de bâtiment prioritaire, prendre n'importe quelle cible
                    self.search_for_target(unit, weakest_enemy, True)
                else:
                    unit.set_target(target)
            
            return True
        return False



