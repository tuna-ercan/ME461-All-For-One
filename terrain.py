"""Map image + collision. The opaque pixels of foreground.png are solid ground."""
import math

import cv2
import numpy as np
import pygame

import config


class Terrain:
    """Holds the rendered map and a signed distance field for collisions.

    distance(p) > 0 in the air, < 0 inside rock; normal(p) points out of the rock.
    """

    def __init__(self, background, foreground):
        self.width, self.height = foreground.get_size()
        self.surface = pygame.Surface((self.width, self.height)).convert()
        self.surface.fill(config.SKY_COLOR)
        self.surface.blit(background, (0, 0))
        self.surface.blit(foreground, (0, 0))

        solid = pygame.surfarray.array_alpha(foreground).T > 127   # (h, w)
        solid[:, :2] = True      # invisible walls on the map's left/right edges
        solid[:, -2:] = True
        self.sdf = self._signed_distance(solid)

    @staticmethod
    def _signed_distance(solid):
        air = (~solid).astype(np.uint8)
        rock = solid.astype(np.uint8)
        out = cv2.distanceTransform(air, cv2.DIST_L2, 5)   # air px -> distance to rock
        inside = cv2.distanceTransform(rock, cv2.DIST_L2, 5)
        return (out - inside).astype(np.float32)

    # ----------------------------------------------------------- queries --
    def distance(self, x, y):
        """Bilinear sample of the SDF. Above the map the top row is extended
        upward: open sky, with the side walls continuing up forever."""
        outside = max(0.0, -x, x - (self.width - 1.001))   # past the side walls = deeper in rock
        x = min(max(x, 0.0), self.width - 1.001)
        y = min(max(y, 0.0), self.height - 1.001)
        x0, y0 = int(x), int(y)
        fx, fy = x - x0, y - y0
        s = self.sdf
        top = s[y0, x0] * (1 - fx) + s[y0, x0 + 1] * fx
        bot = s[y0 + 1, x0] * (1 - fx) + s[y0 + 1, x0 + 1] * fx
        return float(top * (1 - fy) + bot * fy) - outside

    def normal(self, x, y, h=2.0):
        dx = self.distance(x + h, y) - self.distance(x - h, y)
        dy = self.distance(x, y + h) - self.distance(x, y - h)
        n = math.hypot(dx, dy)
        if n < 1e-6:
            return pygame.Vector2(0, -1)
        return pygame.Vector2(dx / n, dy / n)

    def ground_y(self, x):
        """Topmost rock pixel in column x (used for spawning)."""
        col = self.sdf[:, int(min(max(x, 0), self.width - 1))]
        rock = np.nonzero(col < 0)[0]
        return int(rock[0]) if len(rock) else self.height
