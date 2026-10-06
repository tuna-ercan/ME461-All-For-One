"""Windmill: a decorative tower (no collision) and a spinning rotor that is solid.

The rotor's collision works like the terrain's (a signed distance field, see
terrain.py), but the table is made once for the rotor standing still. To ask
"how far is point p from the rotor right now?", p is turned back by the
rotor's current angle around the hub and looked up in that still table.

Feet glued to the rotor (or gripping it by friction) ride along: carry() turns
their glue point with the rotor every physics step, so the rotor can lift the
character and fling it when the foot lets go.

Angles: degrees, clockwise on screen (pygame.Vector2.rotate turns that way
because y points down).
"""
import math

import numpy as np
import pygame

import config
from terrain import Terrain

V = pygame.Vector2
PAD = 48            # px of empty border around the rotor in its distance table
HUB_RADIUS = 70     # px around the hub drawn as one piece (the ball and the blade roots)


class Windmill:
    def __init__(self, spec, scale):
        """spec = the "windmill" dictionary of a map in config.MAPS (image names,
        hub position in image px, turns per second); scale = image px -> map px."""
        self.rps = spec["rps"]
        self.walkable_slope = config.ROTOR_WALKABLE_SLOPE   # non-sticky feet slip on steeper blade parts
        self.hub = V(spec["hub"]) * scale                       # rotation centre, map px
        self.angle = 0.0                                        # current rotation (deg)
        self.turn = 0.0                                         # rotation of the last update (deg)
        self._cos, self._sin = 1.0, 0.0                         # of -angle, for distance()

        # tower: crop the big canvas to the tower, scale it, remember where it goes on the map
        base = pygame.image.load(config.asset(spec["base"])).convert_alpha()
        crop = base.get_bounding_rect(min_alpha=1).inflate(4, 4).clip(base.get_rect())
        self.base = pygame.transform.smoothscale(
            base.subsurface(crop), (round(crop.w * scale), round(crop.h * scale)))
        self.base_pos = V(crop.topleft) * scale

        # rotor: crop the big canvas to the rotor, then scale to map size
        img = pygame.image.load(config.asset(spec["blade"])).convert_alpha()
        crop = img.get_bounding_rect(min_alpha=1).inflate(4, 4).clip(img.get_rect())
        size = (round(crop.w * scale), round(crop.h * scale))
        rotor = pygame.transform.smoothscale(img.subsurface(crop), size)
        self.corner = V(crop.topleft) * scale                   # rotor image corner on the map (angle 0)
        self.rotor = rotor

        # collision table of the still rotor, with a PAD px empty border so points
        # near the rotor's edge still get a correct (positive) distance
        alpha = pygame.surfarray.array_alpha(rotor).T > 127     # (h, w), True = solid
        solid = np.zeros((alpha.shape[0] + 2 * PAD, alpha.shape[1] + 2 * PAD), bool)
        solid[PAD:-PAD, PAD:-PAD] = alpha
        self.sdf = Terrain._signed_distance(solid)
        self.origin = self.corner - V(PAD, PAD)                 # map position of sdf[0, 0]
        ys, xs = np.nonzero(alpha)                              # how far the rotor reaches from the hub
        self.reach = float(np.hypot(xs + self.corner.x - self.hub.x,
                                    ys + self.corner.y - self.hub.y).max())

        self.pieces = self._split(rotor)
        self._small = None                                      # (k, rotor image) for the overview map

    def _split(self, rotor):
        """Cut the rotor into one piece per blade (120 deg slices around the hub) and
        the hub ball.
        Turning three thin pieces each frame is much faster than turning the one
        big square picture, and pieces outside the view are skipped."""
        w, h = rotor.get_size()
        xs, ys = np.meshgrid(np.arange(w), np.arange(h))        # pixel coordinates
        hub = self.hub - self.corner                            # hub inside the rotor image
        ang = np.degrees(np.arctan2(ys - hub.y, xs - hub.x))    # direction of each pixel from the hub
        near = np.hypot(xs - hub.x, ys - hub.y) <= HUB_RADIUS   # the hub ball: one piece, no seams
        pieces = []
        for k in range(4):
            if k == 3:
                inside = near
            else:
                centre = -90 + 120 * k                          # up, lower right, lower left
                inside = (np.abs((ang - centre + 180) % 360 - 180) <= 60) & ~near
            part = rotor.copy()
            pygame.surfarray.pixels_alpha(part)[...] *= inside.T   # clear the other two slices
            rect = part.get_bounding_rect(min_alpha=1)
            piece = part.subsurface(rect).copy()
            offset = V(rect.center) - hub                       # piece centre relative to the hub
            pieces.append((piece, offset, math.hypot(*rect.size) / 2))
        return pieces

    # ------------------------------------------------------------- motion --
    def reset(self):
        self.angle, self.turn = 0.0, 0.0
        self._cos, self._sin = 1.0, 0.0

    def update(self, dt):
        self.turn = 360.0 * self.rps * dt
        self.angle = (self.angle + self.turn) % 360.0
        a = math.radians(-self.angle)
        self._cos, self._sin = math.cos(a), math.sin(a)

    def velocity_at(self, p):
        """How fast the rotor surface at point p moves (px/s)."""
        r = V(p) - self.hub
        return V(-r.y, r.x) * math.radians(360.0 * self.rps)   # clockwise on screen

    def carry(self, p):
        """Where a point stuck on the rotor is after the last update."""
        return self.hub + (V(p) - self.hub).rotate(self.turn)

    # ---------------------------------------------------------- collision --
    def distance(self, x, y):
        """Signed distance from (x, y) to the rotor at its current angle."""
        dx, dy = x - self.hub.x, y - self.hub.y
        r = math.hypot(dx, dy)
        if r > self.reach + PAD // 2:
            return r - self.reach         # far away: a safe (never too big) estimate
        # turn the point back by the rotor angle -> position in the still table
        lx = self.hub.x + dx * self._cos - dy * self._sin - self.origin.x
        ly = self.hub.y + dx * self._sin + dy * self._cos - self.origin.y
        hgt, wid = self.sdf.shape
        if not (0 <= lx < wid - 1.001 and 0 <= ly < hgt - 1.001):
            return float(PAD)             # inside the reach circle but beside the rotor's box
        x0, y0 = int(lx), int(ly)         # bilinear sample, as in Terrain.distance
        fx, fy = lx - x0, ly - y0
        s = self.sdf
        top = s[y0, x0] * (1 - fx) + s[y0, x0 + 1] * fx
        bot = s[y0 + 1, x0] * (1 - fx) + s[y0 + 1, x0 + 1] * fx
        return float(top * (1 - fy) + bot * fy)

    # ------------------------------------------------------------ drawing --
    def draw(self, target, offset):
        """Draw the tower, then the rotor at its current angle; offset = top-left of the
        view. Called after the character, so the windmill is in front of it."""
        view = target.get_rect()
        target.blit(self.base, self.base_pos - offset)
        for piece, centre, radius in self.pieces:
            pos = self.hub + centre.rotate(self.angle) - offset   # piece centre on screen
            if not view.colliderect((pos.x - radius, pos.y - radius, 2 * radius, 2 * radius)):
                continue                                          # off screen: skip the slow part
            img = pygame.transform.rotate(piece, -self.angle)     # pygame turns counter-clockwise
            target.blit(img, img.get_rect(center=(round(pos.x), round(pos.y))))

    def draw_small(self, target, corner, k):
        """Rotor for the overview map: whole map shrunk by k, map (0, 0) at `corner`."""
        if self._small is None or self._small[0] != k:
            size = (max(1, round(self.rotor.get_width() * k)), max(1, round(self.rotor.get_height() * k)))
            small = pygame.transform.smoothscale(self.rotor, size)
            self._small = (k, small, (self.hub - self.corner) * k)
        _, small, hub = self._small
        img = pygame.transform.rotate(small, -self.angle)
        centre = V(small.get_size()) / 2 - hub                    # image centre relative to the hub
        pos = V(corner) + self.hub * k + centre.rotate(self.angle)
        target.blit(img, img.get_rect(center=(round(pos.x), round(pos.y))))
