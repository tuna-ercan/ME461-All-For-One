"""Game camera: a window onto the map that smoothly follows the character."""
import pygame

import config


class Viewport:
    def __init__(self, map_w, map_h):
        self.map_w, self.map_h = map_w, map_h
        self.w = round(map_w * config.VIEW_FRACTION)
        self.h = round(map_h * config.VIEW_FRACTION)
        self.pos = pygame.Vector2()   # top-left corner in map pixels

    def _clamped(self, p):
        return pygame.Vector2(min(max(p.x, 0), self.map_w - self.w),
                              min(max(p.y, 0), self.map_h - self.h))

    def snap(self, target):
        self.pos = self._clamped(target - pygame.Vector2(self.w, self.h) / 2)

    def follow(self, target, dt):
        goal = self._clamped(target - pygame.Vector2(self.w, self.h) / 2)
        self.pos += (goal - self.pos) * min(1.0, config.CAMERA_LERP * dt)

    @property
    def rect(self):
        return pygame.Rect(int(self.pos.x), int(self.pos.y), self.w, self.h)
