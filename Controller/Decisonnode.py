# Chemin de C:/Users/cyril/OneDrive/Documents/INSA/3A/PYTHON_TEST/Projet_python\Controller\Decisonnode.py
from Controller.terminal_display_debug import debug_print

import time as _time

# Debug flag pour les décisions
DECISION_DEBUG = False  # Désactivé - le debug principal est dans Bot.py
_decision_debug_last = {}  # Dictionnaire pour throttle par message

def decision_debug(message, throttle_key=None, interval=5.0):
    """Affiche un message de debug avec throttling par clé"""
    if not DECISION_DEBUG:
        return
    
    if throttle_key is None:
        print(f"[DECISION] {message}")
        return
    
    current = _time.time()
    if throttle_key not in _decision_debug_last or current - _decision_debug_last[throttle_key] >= interval:
        _decision_debug_last[throttle_key] = current
        print(f"[DECISION] {message}")

class DecisionNode:
    def __init__(self, condition=None, true_branch=None, false_branch=None, action=None):
        self.condition = condition
        self.true_branch = true_branch
        self.false_branch = false_branch
        self.action = action

    def evaluate(self):
        if self.condition and self.condition():
            if self.true_branch:
                return self.true_branch.evaluate()
            elif self.action:
                return self.action()
        else:
            if self.false_branch:
                return self.false_branch.evaluate()
            elif self.action:
                return self.action()

# --- Conditions ---
def is_under_attack_condition(bot):
    result = bot.is_under_attack()
    if result:
        decision_debug(f"Team {bot.team.teamID}: UNDER ATTACK!")
    return result

def is_resource_shortage_condition(bot):
    result = bot.get_resource_shortage()
    if result:
        decision_debug(f"Team {bot.team.teamID}: Resource shortage: {result.__name__}", f"shortage_{bot.team.teamID}")
    return result

def are_buildings_needed_condition(bot):
    needed = bot.check_building_needs()
    result = len(needed) > 0
    if result:
        decision_debug(f"Team {bot.team.teamID}: Buildings needed: {needed[:3]}", f"buildings_{bot.team.teamID}")
    return result

def is_army_below_threshold_condition(bot):
    count = bot.get_military_unit_count(bot.team)
    result = count < 15
    if result:
        decision_debug(f"Team {bot.team.teamID}: Army too small ({count}/15)", f"army_{bot.team.teamID}")
    return result

def are_damaged_buildings_condition(bot):
    return len(bot.get_critical_points()) > 0

def is_military_count_low_condition(bot):
    return bot.get_military_unit_count(bot.team) < 10

def should_expand_condition(bot):
    """Vérifie si le bot devrait s'étendre"""
    return bot.is_ready_to_expand()

# --- Actions ---
def defend_action(bot):
    decision_debug(f"Team {bot.team.teamID}: ACTION -> defend", f"action_{bot.team.teamID}", 3.0)
    bot.priorty1()

def address_resource_shortage_action(bot):
    decision_debug(f"Team {bot.team.teamID}: ACTION -> address_resource_shortage", f"action_{bot.team.teamID}", 3.0)
    bot.priority7()

def build_needed_structure_action(bot):
    decision_debug(f"Team {bot.team.teamID}: ACTION -> build_structure", f"action_{bot.team.teamID}", 3.0)
    bot.build_structure()

def balance_army_action(bot):
    decision_debug(f"Team {bot.team.teamID}: ACTION -> balance_army", f"action_{bot.team.teamID}", 3.0)
    bot.balance_units()

def repair_buildings_action(bot):
    """Envoie des villageois réparer les bâtiments endommagés."""
    decision_debug(f"Team {bot.team.teamID}: ACTION -> repair_buildings", f"action_{bot.team.teamID}", 3.0)
    critical_buildings = bot.get_critical_points()
    if not critical_buildings:
        return False
    
    # Trouver des villageois disponibles (task est None quand idle)
    from Entity.Unit import Villager
    available_villagers = [
        unit for unit in bot.team.units 
        if isinstance(unit, Villager) and unit.isAlive()
        and (unit.task is None or unit.state == 'idle')
    ]
    
    if not available_villagers:
        return False
    
    # Assigner jusqu'à 2 villageois par bâtiment endommagé
    villagers_assigned = 0
    for building in critical_buildings[:3]:  # Max 3 bâtiments à la fois
        for villager in available_villagers[:2]:  # Max 2 villageois par bâtiment
            if villager not in building.builders:
                villager.set_task('repair', building)
                villagers_assigned += 1
                available_villagers.remove(villager)
                if not available_villagers:
                    break
        if not available_villagers:
            break
    
    return villagers_assigned > 0

def manage_offense_action(bot):
    """Version simplifiée de manage_offense pour l'arbre de décision économique"""
    decision_debug(f"Team {bot.team.teamID}: ACTION -> manage_offense")
    # On cible simplement le premier ennemi trouvé
    if bot.enemies:
        enemy_team = bot.enemies[0]
        military_units = bot.get_military_units()
        targets_assigned = 0
        for unit in military_units:
            if not unit.attack_target or not unit.attack_target.isAlive():
                if bot.search_for_target(unit, enemy_team, True):
                    targets_assigned += 1
        decision_debug(f"Team {bot.team.teamID}: Assigned {targets_assigned} targets to military units")
    return True

def expansion_action(bot):
    """Action d'expansion"""
    decision_debug(f"Team {bot.team.teamID}: ACTION -> expansion")
    return bot.manage_expansion()

# --- Decision Trees ---

def create_economic_decision_tree(bot):
    """Decision tree for Economic mode - now includes expansion"""
    return DecisionNode(
        condition = lambda: is_under_attack_condition(bot),
        true_branch = DecisionNode(
            action = lambda: defend_action(bot)
        ),
        false_branch = DecisionNode(
            # IMPORTANT: Vérifier les ressources AVANT les bâtiments
            # get_resource_shortage prend maintenant en compte le coût des bâtiments
            condition = lambda: is_resource_shortage_condition(bot),
            true_branch = DecisionNode(
                action = lambda: address_resource_shortage_action(bot)
            ),
            false_branch = DecisionNode(
                condition = lambda: are_buildings_needed_condition(bot),
                true_branch = DecisionNode(
                    action = lambda: build_needed_structure_action(bot)
                ),
                false_branch = DecisionNode(
                    condition = lambda: should_expand_condition(bot),
                    true_branch = DecisionNode(
                        action = lambda: expansion_action(bot)
                    ),
                    false_branch = DecisionNode(
                        action = lambda: balance_army_action(bot)
                    )
                )
            )
        )
    )

def create_defensive_decision_tree(bot):
    """Decision tree for Defensive mode - focuses on defense and strong economy."""
    return DecisionNode(
        condition=lambda: is_under_attack_condition(bot),
        true_branch=DecisionNode(
            action=lambda: defend_action(bot) # Prioritize defense
        ),
        false_branch=DecisionNode(
            condition=lambda: are_damaged_buildings_condition(bot),
            true_branch=DecisionNode(
                action=lambda: repair_buildings_action(bot) # Repair buildings if damaged
            ),
            false_branch=DecisionNode(
                # IMPORTANT: Vérifier les ressources AVANT les bâtiments
                condition=lambda: is_resource_shortage_condition(bot),
                true_branch=DecisionNode(
                    action=lambda: address_resource_shortage_action(bot) # Ensure good economy
                ),
                false_branch=DecisionNode(
                    condition=lambda: are_buildings_needed_condition(bot),
                    true_branch=DecisionNode(
                        action=lambda: build_needed_structure_action(bot)
                    ),
                    false_branch=DecisionNode( # If base is secure and economy good, then balance army
                        action=lambda: balance_army_action(bot)
                    )
                )
            )
        )
    )

def create_offensive_decision_tree(bot):
    """Decision tree for Offensive mode - focuses on aggressive military actions."""
    return DecisionNode(
        condition=lambda: is_under_attack_condition(bot),
        true_branch=DecisionNode(
            action=lambda: defend_action(bot) # Défend si attaqué en premier
        ),
        false_branch=DecisionNode(
            condition=lambda: is_army_below_threshold_condition(bot),
            true_branch=DecisionNode(
                action=lambda: balance_army_action(bot) # Build army if small
            ),
            false_branch=DecisionNode( # If army is decent size, attack!
                action=lambda: manage_offense_action(bot) # Manage offensive battle
            )
        )
    )

def create_default_decision_tree(bot):
    """Fallback decision tree - a balanced approach."""
    return DecisionNode(
        condition=lambda: is_under_attack_condition(bot),
        true_branch=DecisionNode(
            action=lambda: defend_action(bot)
        ),
        false_branch=DecisionNode(
            # IMPORTANT: Vérifier les ressources AVANT les bâtiments
            condition=lambda: is_resource_shortage_condition(bot),
            true_branch=DecisionNode(
                action=lambda: address_resource_shortage_action(bot)
            ),
            false_branch=DecisionNode(
                condition=lambda: are_buildings_needed_condition(bot),
                true_branch=DecisionNode(
                    action=lambda: build_needed_structure_action(bot)
                ),
                false_branch=DecisionNode(
                    condition=lambda: is_military_count_low_condition(bot),
                    true_branch=DecisionNode(
                        action=lambda: balance_army_action(bot)
                    ),
                    false_branch=DecisionNode(
                        action=lambda: manage_offense_action(bot) # Balanced approach: manage offense if nothing else needed
                    )
                )
            )
        )
    )