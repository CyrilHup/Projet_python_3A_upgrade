"""
Resources module - Manages game resources (food, gold, wood).

This module provides the Resources class for tracking and manipulating
the three main resource types in the game.
"""
from __future__ import annotations
from typing import Tuple, Union
from dataclasses import dataclass

from Controller.terminal_display_debug import debug_print


@dataclass
class Resources:
    """
    Represents a collection of game resources.
    
    Attributes
    ----------
    food : int
        Amount of food resources.
    gold : int
        Amount of gold resources.
    wood : int
        Amount of wood resources.
    
    Examples
    --------
    >>> res = Resources(food=100, gold=50, wood=75)
    >>> res.total()
    225
    >>> res.has_enough((50, 25, 30))
    True
    """
    
    food: int = 0
    gold: int = 0
    wood: int = 0

    def reset(self) -> None:
        """Reset all resources to zero."""
        self.food = 0
        self.gold = 0
        self.wood = 0
        
    def set_resources(self, food: int = 0, gold: int = 0, wood: int = 0) -> None:
        """
        Set all resource values at once.
        
        Parameters
        ----------
        food : int
            New food amount.
        gold : int
            New gold amount.
        wood : int
            New wood amount.
        """
        self.food = food
        self.gold = gold
        self.wood = wood

    def add_food(self, amount: int) -> int:
        """Add food and return the amount added."""
        self.food += amount
        return amount

    def remove_food(self, amount: int) -> int:
        """Remove food (up to available) and return amount removed."""
        removed = min(self.food, amount)
        self.food -= removed
        return removed

    def add_gold(self, amount: int) -> int:
        """Add gold and return the amount added."""
        self.gold += amount
        return amount

    def remove_gold(self, amount: int) -> int:
        """Remove gold (up to available) and return amount removed."""
        removed = min(self.gold, amount)
        self.gold -= removed
        return removed

    def add_wood(self, amount: int) -> int:
        """Add wood and return the amount added."""
        self.wood += amount
        return amount

    def remove_wood(self, amount: int) -> int:
        """Remove wood (up to available) and return amount removed."""
        removed = min(self.wood, amount)
        self.wood -= removed
        return removed

    def increase_resources(self, resources: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """
        Add multiple resources at once.
        
        Parameters
        ----------
        resources : Tuple[int, int, int]
            Tuple of (food, gold, wood) to add.
            
        Returns
        -------
        Tuple[int, int, int]
            The amounts added.
        """
        food, gold, wood = resources
        self.food += food
        self.gold += gold
        self.wood += wood
        return (food, gold, wood)

    def decrease_resources(self, resources: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """
        Remove multiple resources at once (up to available).
        
        Parameters
        ----------
        resources : Tuple[int, int, int]
            Tuple of (food, gold, wood) to remove.
            
        Returns
        -------
        Tuple[int, int, int]
            The amounts actually removed.
        """
        food, gold, wood = resources
        removed_food = min(self.food, food)
        removed_gold = min(self.gold, gold)
        removed_wood = min(self.wood, wood)
        self.food -= removed_food
        self.gold -= removed_gold
        self.wood -= removed_wood
        return (removed_food, removed_gold, removed_wood)

    def has_enough(self, resources: Tuple[int, int, int] = (0, 0, 0)) -> bool:
        """
        Check if there are enough resources available.
        
        Parameters
        ----------
        resources : Tuple[int, int, int]
            Required amounts of (food, gold, wood).
            
        Returns
        -------
        bool
            True if all required resources are available.
        """
        food, gold, wood = resources
        return not (
            (food > 0 and self.food < food) or
            (gold > 0 and self.gold < gold) or
            (wood > 0 and self.wood < wood)
        )

    def min_resource(self) -> str:
        """
        Find which resource type has the lowest amount.
        
        Returns
        -------
        str
            Name of the resource with lowest amount ("food", "gold", or "wood").
        """
        min_value = min(self.food, self.gold, self.wood)
        
        if min_value == self.wood:
            return "wood"
        elif min_value == self.gold:
            return "gold"
        else:
            return "food"

    def get(self) -> Tuple[int, int, int]:
        """
        Get all resources as a tuple.
        
        Returns
        -------
        Tuple[int, int, int]
            Tuple of (food, gold, wood).
        """
        return (self.food, self.gold, self.wood)

    def total(self) -> int:
        """
        Calculate total resources.
        
        Returns
        -------
        int
            Sum of all resource types.
        """
        return self.food + self.gold + self.wood

    def copy(self) -> 'Resources':
        """
        Create a copy of this Resources object.
        
        Returns
        -------
        Resources
            A new Resources instance with the same values.
        """
        return Resources(self.food, self.gold, self.wood)

    def __eq__(self, other: object) -> bool:
        """Check equality with another Resources object."""
        if isinstance(other, Resources):
            return self.food == other.food and self.gold == other.gold and self.wood == other.wood
        return False

    def __repr__(self) -> str:
        """Return string representation."""
        return f"Resources(food={self.food}, wood={self.wood}, gold={self.gold})"
