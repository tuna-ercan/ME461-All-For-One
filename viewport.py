"""Game camera: a window onto the map that smoothly follows the character."""
import pygame

import config


def view_size():
    """Size of the game view in map pixels (the same for every map, see config.MAP_HEIGHT)."""
    h = round(config.MAP_HEIGHT * config.VIEW_FRACTION)
    return round(h * config.VIEW_ASPECT), h


class Viewport:
    def __init__(self, map_w, map_h, w, h):
        self.map_w, self.map_h = map_w, map_h
        self.w, self.h = w, h
        self.pos = pygame.Vector2()   # top-left corner in map pixels

    def _clamped(self, p):
        """Keep the view inside the map (centred if the map is smaller than the view)."""
        def clamp(v, size, view):
            return (size - view) / 2 if size <= view else min(max(v, 0), size - view)
        return pygame.Vector2(clamp(p.x, self.map_w, self.w), clamp(p.y, self.map_h, self.h))

    def snap(self, target):
        self.pos = self._clamped(target - pygame.Vector2(self.w, self.h) / 2)

    def follow(self, target, dt):
        goal = self._clamped(target - pygame.Vector2(self.w, self.h) / 2)
        self.pos += (goal - self.pos) * min(1.0, config.CAMERA_LERP * dt)

    @property
    def rect(self):
        return pygame.Rect(int(self.pos.x), int(self.pos.y), self.w, self.h)
