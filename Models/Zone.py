from Controller.terminal_display_debug import debug_print

class Zone:
    def __init__(self):
        self.zone = set()  # Utiliser un set au lieu d'une liste pour O(1) lookup
        self._cached_sorted = None  # Cache pour éviter de re-trier

    def _ensure_set(self):
        """Convertit self.zone en set si c'est une liste (compatibilité anciennes sauvegardes)."""
        if isinstance(self.zone, list):
            self.zone = set(self.zone)

    def reset(self):
        self._ensure_set()
        self.zone.clear()
        self._cached_sorted = None

    def _invalidate_cache(self):
        """Invalide le cache de façon sécurisée."""
        self._cached_sorted = None

    def set_zone(self, start, end):
        self._ensure_set()
        self.zone.clear()
        self._invalidate_cache()
        x1, y1 = start
        x2, y2 = end
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                self.zone.add((x, y))

    def add_zone(self, start, end):
        self._ensure_set()
        self._invalidate_cache()
        x1, y1 = start
        x2, y2 = end
        to_add = []
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                tile = (x, y)
                to_add.append(tile)
                self.zone.add(tile)
        return to_add

    def remove_zone(self, start, end):
        self._ensure_set()
        self._invalidate_cache()
        x1, y1 = start
        x2, y2 = end
        to_remove = []
        for x in range(int(min(x1, x2)), int(max(x1, x2) + 1)):
            for y in range(int(min(y1, y2)), int(max(y1, y2) + 1)):
                tile = (x, y)
                if tile in self.zone:
                    to_remove.append(tile)
        for tile in to_remove:
            self.zone.discard(tile)
        return to_remove

    def add_tile(self, position):
        self._ensure_set()
        self._invalidate_cache()
        self.zone.add(position)

    def remove_tile(self, position):
        self._ensure_set()
        self._invalidate_cache()
        self.zone.discard(position)

    def inZone(self, zone=None, tile=None):
        self._ensure_set()
        if tile is not None:
            return tile in self.zone
        if zone is not None and isinstance(zone, Zone):
            zone._ensure_set()
            return bool(self.zone & zone.zone)  # Intersection de sets
        return False

    def get_zone(self):
        self._ensure_set()
        # Cache le résultat trié pour éviter de re-trier à chaque appel
        # Gère aussi les objets désérialisés qui n'ont pas l'attribut
        if not hasattr(self, '_cached_sorted') or self._cached_sorted is None:
            self._cached_sorted = sorted(self.zone)
        return self._cached_sorted

    def __eq__(self, other):
        return isinstance(other, Zone) and self.zone == other.zone

    def __repr__(self):
        return f"Zone({sorted(self.zone)})"