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
        """Bilinear sample of the SDF. Above the map the top row continues upward:
        where it is sky, open sky; where it is rock (side walls, a solid top
        border like the cave's), rock that gets deeper going up, so anything
        poking through is pushed back down into the map instead of escaping."""
        outside = max(0.0, -x, x - (self.width - 1.001))   # past the side walls = deeper in rock
        above = max(0.0, -y)
        x = min(max(x, 0.0), self.width - 1.001)
        y = min(max(y, 0.0), self.height - 1.001)
        x0, y0 = int(x), int(y)
        fx, fy = x - x0, y - y0
        s = self.sdf
        top = s[y0, x0] * (1 - fx) + s[y0, x0 + 1] * fx
        bot = s[y0 + 1, x0] * (1 - fx) + s[y0 + 1, x0 + 1] * fx
        d = float(top * (1 - fy) + bot * fy) - outside
        return d - above if d < 0 else d

    def normal(self, x, y, h=2.0):
        dx = self.distance(x + h, y) - self.distance(x - h, y)
        dy = self.distance(x, y + h) - self.distance(x, y - h)
        n = math.hypot(dx, dy)
        if n < 1e-6:
            return pygame.Vector2(0, -1)
        return pygame.Vector2(dx / n, dy / n)

    def ground_y(self, x):
        """Top of the ground under the open sky in column x: the first rock below the
        first air from the top (skips a solid border along the map's top edge).
        0 if the column is rock from the top down (no sky)."""
        col = self.sdf[:, int(min(max(x, 0), self.width - 1))]
        air = np.nonzero(col > 0)[0]
        if not len(air) or air[0] > self.height * 0.02:
            return 0
        rock = np.nonzero(col[air[0]:] < 0)[0]
        return int(air[0] + rock[0]) if len(rock) else self.height
