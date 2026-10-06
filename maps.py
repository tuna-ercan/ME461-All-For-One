"""Playable maps: terrain + flag + start point, built from the entries in config.MAPS."""
import pygame

import config
from flag import Flag
from terrain import Terrain
from windmill import Windmill

THUMB_HEIGHT = 230   # menu picture height (canvas px)


class GameMap:
    def __init__(self, spec):
        # spec = one dictionary from config.MAPS (name, image files, spawn, scale)
        self.name = spec["name"]
        bg = pygame.image.load(config.asset(spec["background"])).convert_alpha()
        fg = pygame.image.load(config.asset(spec["foreground"])).convert_alpha()
        # Resize so the map is MAP_HEIGHT tall (times its own "scale"). The
        # character, flag and view are sized from MAP_HEIGHT, so they look the
        # same on every map; "scale" makes a map bigger compared to them.
        height = round(config.MAP_HEIGHT * spec.get("scale", 1.0))   # MAP_HEIGHT x map scale
        scale = height / fg.get_height()
        if abs(scale - 1) > 1e-3:                                     # skip if already right
            size = (round(fg.get_width() * scale), height)            # keep the shape
            bg = pygame.transform.smoothscale(bg, size)
            fg = pygame.transform.smoothscale(fg, size)
        self.terrain = Terrain(bg, fg)
        self.windmill = None
        if "windmill" in spec:
            self.windmill = Windmill(spec["windmill"], scale)
            self.terrain.surface.blit(self.windmill.base, (0, 0))   # tower: just a picture
            self.terrain.movers.append(self.windmill)               # rotor: solid
        self.flag = Flag(self.terrain)
        self.spawn = self._find_spawn(*spec["spawn"])

        # Small picture for the map-selection menu: the whole map shrunk to
        # THUMB_HEIGHT tall, with a shrunk flag pasted at the same relative spot.
        t = self.terrain.surface
        thumb = (round(t.get_width() * THUMB_HEIGHT / t.get_height()), THUMB_HEIGHT)
        self.thumbnail = pygame.transform.smoothscale(t, thumb)
        self.thumbnail.blit(pygame.transform.smoothscale(
            self.flag.image, [max(1, round(v * THUMB_HEIGHT / t.get_height()))
                              for v in self.flag.image.get_size()]),
            self.flag.pos * THUMB_HEIGHT / t.get_height())
        if self.windmill:
            self.windmill.draw_small(self.thumbnail, (0, 0), THUMB_HEIGHT / t.get_height())

    # --- moving parts (windmill rotor); maps without them do nothing here ---
    def reset(self):
        if self.windmill:
            self.windmill.reset()

    def update(self, dt):
        if self.windmill:
            self.windmill.update(dt)

    def draw_movers(self, target, offset):
        if self.windmill:
            self.windmill.draw(target, offset)

    def draw_movers_small(self, target, corner, k):
        if self.windmill:
            self.windmill.draw_small(target, corner, k)

    def _find_spawn(self, fx, fy):
        """Drop from (fx, fy) (map fractions) to the floor below; start a little above it,
        but not higher than the middle of the gap (so it fits in tunnels)."""
        t = self.terrain
        x, y = fx * t.width, fy * t.height
        while y > 0 and t.distance(x, y) <= 0:            # start point in rock: go up into air
            y -= 2
        floor = y
        while floor < t.height - 1 and t.distance(x, floor) > 0:    # walk down to the floor
            floor += 2
        ceiling = y
        while ceiling > 0 and t.distance(x, ceiling) > 0:           # walk up to the ceiling (or top)
            ceiling -= 2
        lift = config.MAP_HEIGHT * config.SPAWN_LIFT
        # normally start `lift` above the floor; in a low tunnel start at its middle
        return pygame.Vector2(x, max(floor - lift, (floor + ceiling) / 2))


def load_maps():
    return [GameMap(spec) for spec in config.MAPS]
