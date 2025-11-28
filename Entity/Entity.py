"""
Entity module - Base class for all game entities.

This module provides the base Entity class that all game objects
(units, buildings, resources) inherit from.
"""
from __future__ import annotations
import time
import math
from typing import Optional, Tuple, TYPE_CHECKING

from Models.Resources import Resources
from Settings.setup import HALF_TILE_SIZE, user_choices
from Controller.utils import tile_to_screen
from Controller.drawing import draw_healthBar, draw_hitbox
import pygame

if TYPE_CHECKING:
    from Controller.camera import Camera


class Entity:
    """
    Base class for all game entities.
    
    Attributes
    ----------
    x : float
        X position in tile coordinates.
    y : float
        Y position in tile coordinates.
    team : Optional[int]
        Team ID this entity belongs to, or None for neutral entities.
    acronym : str
        Single character identifier for the entity type.
    size : int
        Size of the entity in tiles.
    max_hp : int
        Maximum health points.
    hp : int
        Current health points.
    state : str
        Current state (idle, walk, attack, death, etc.).
    """
    
    id: int = 0
    HEALTH_BAR_DISPLAY_DURATION: float = 3.0
    
    def __init__(
        self, 
        x: float = 0, 
        y: float = 0, 
        team: Optional[int] = None, 
        acronym: str = '', 
        size: int = 1, 
        max_hp: int = 100, 
        cost: Resources = None,
        walkable: bool = False,
        hasResources: bool = False,
        hitbox: float = 0
    ) -> None:
        """
        Initialize a new Entity.
        
        Parameters
        ----------
        x : float
            Initial X position in tile coordinates.
        y : float
            Initial Y position in tile coordinates.
        team : Optional[int]
            Team ID, or None for neutral entities.
        acronym : str
            Single character identifier.
        size : int
            Size in tiles.
        max_hp : int
            Maximum health points.
        cost : Resources
            Resource cost to create this entity.
        walkable : bool
            Whether other entities can walk through this one.
        hasResources : bool
            Whether this entity provides resources.
        hitbox : float
            Custom hitbox size, defaults to size/2.
        """
        if cost is None:
            cost = Resources()
            
        self.x: float = x
        self.y: float = y
        self.team: Optional[int] = team
        self.acronym: str = acronym
        self.size: int = size
        self.max_hp: int = max_hp
        self.cost: Resources = cost
        self.walkable: bool = walkable
        self.hasResources: bool = hasResources
  
        self.hp: int = max_hp
        self.hitbox: float = hitbox if hitbox > 0 else size / 2
        self.last_damage_time: float = 0
        self.last_clicked_time: float = 0

        self.state: str = 'idle'
        self.current_frame: int = 0
        self.frame_duration: float = 0
        self.cooldown_frame: Optional[int] = None

        self.death_timer: float = 0
        self.death_duration: float = 5

        self.entity_id: int = Entity.id
        Entity.id += 1

        # DEBUG INSTRUCTIONS
        self.hitbox_color: Tuple[int, int, int] = (255, 255, 255)
        self.range_color: Tuple[int, int, int] = (255, 255, 255)

    def get_state(self) -> str:
        """Return the current state of the entity."""
        return self.state

    def isAlive(self) -> bool:
        """Check if the entity is still alive."""
        return self.hp > 0

    def isIdle(self) -> bool:
        """Check if the entity is in idle state."""
        return self.state == 'idle'

    def notify_damage(self) -> None:
        """Record the time when entity was last damaged."""
        self.last_damage_time = time.time()

    def notify_clicked(self) -> None:
        """Record the time when entity was last clicked."""
        self.last_clicked_time = time.time()

    def should_draw_health_bar(self) -> bool:
        """
        Determine if health bar should be displayed.
        
        Returns
        -------
        bool
            True if health bar should be shown based on recent damage or click.
        """
        if not hasattr(self, 'hp') or self.hp <= 0 or self.max_hp is None or self.max_hp <= 0:
            return False
        current_time = time.time()
        return ((current_time - self.last_damage_time) < self.HEALTH_BAR_DISPLAY_DURATION) or \
               ((current_time - self.last_clicked_time) < self.HEALTH_BAR_DISPLAY_DURATION)

    def get_health_ratio(self) -> float:
        """
        Calculate the ratio between current HP and max HP.
        
        Returns
        -------
        float
            Health ratio between 0.0 and 1.0.
        """
        if not self.max_hp:
            return 0.0
        return max(0.0, self.hp / self.max_hp)

    def display_hitbox(
        self, 
        screen: pygame.Surface, 
        screen_width: int, 
        screen_height: int, 
        camera: 'Camera'
    ) -> None:
        """Display the entity's hitbox for debugging purposes."""
        if user_choices["bot_level"] == "DEBUG":
            corner_distance = self.size / 2.0
            corners = [
                (self.x - corner_distance, self.y - corner_distance),
                (self.x - corner_distance, self.y + corner_distance),
                (self.x + corner_distance, self.y + corner_distance),
                (self.x + corner_distance, self.y - corner_distance)
            ]
            
            screen_corners = []
            for corner in corners:
                x_screen, y_screen = tile_to_screen(
                    corner[0], 
                    corner[1], 
                    HALF_TILE_SIZE, 
                    HALF_TILE_SIZE / 2, 
                    camera, 
                    screen_width, 
                    screen_height
                )
                screen_corners.append((x_screen, y_screen))
            
            draw_hitbox(screen, screen_corners, camera.zoom, self.hitbox_color)
            center = tile_to_screen(self.x, self.y, HALF_TILE_SIZE, HALF_TILE_SIZE / 2, camera, screen_width, screen_height)
            hitbox_iso = self.hitbox / math.cos(math.radians(45))
            width = hitbox_iso * camera.zoom * HALF_TILE_SIZE
            height = hitbox_iso * camera.zoom * HALF_TILE_SIZE / 2
            x = center[0] - width // 2
            y = center[1] - height // 2

    def display_range(
        self, 
        screen: pygame.Surface, 
        screen_width: int, 
        screen_height: int, 
        camera: 'Camera'
    ) -> None:
        """Display the entity's attack range for debugging purposes."""
        if hasattr(self, 'attack_range') and self.attack_range and user_choices["bot_level"] == "DEBUG":
            center = tile_to_screen(self.x, self.y, HALF_TILE_SIZE, HALF_TILE_SIZE / 2, camera, screen_width, screen_height)
            range_iso = self.attack_range / math.cos(math.radians(45))
            width = range_iso * camera.zoom * HALF_TILE_SIZE 
            height = range_iso * camera.zoom * HALF_TILE_SIZE / 2
            x = center[0] - width // 2
            y = center[1] - height // 2 
            pygame.draw.ellipse(screen, (255, 0, 0), (x, y, width, height), 1)
            pygame.draw.rect(screen, (255, 255, 0), (x, y, width, height), 1)

    def display_healthbar(
        self, 
        screen: pygame.Surface, 
        screen_width: int, 
        screen_height: int, 
        camera: 'Camera', 
        color: Tuple[int, int, int] = (0, 200, 0)
    ) -> None:
        """
        Display the entity's health bar above its position.
        
        Parameters
        ----------
        screen : pygame.Surface
            The surface to draw on.
        screen_width : int
            Width of the screen.
        screen_height : int
            Height of the screen.
        camera : Camera
            The game camera for coordinate conversion.
        color : Tuple[int, int, int]
            RGB color for the health bar.
        """
        if self.hp <= 0 or not self.max_hp:
            return
        
        ratio = self.get_health_ratio()
        if ratio <= 0.0:
            return
        
        sx, sy = tile_to_screen(
            self.x, 
            self.y, 
            HALF_TILE_SIZE, 
            HALF_TILE_SIZE / 2, 
            camera, 
            screen_width, 
            screen_height
        )

        draw_healthBar(screen, sx, sy, ratio, color)