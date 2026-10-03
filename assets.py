"""Character images: scaled, cropped, mirrored and tinted copies of the part pngs."""
import numpy as np
import pygame

import config


class PivotSprite:
    """An image that is drawn rotated around a pivot point (e.g. a joint)."""

    def __init__(self, image, pivot):
        self.image = image
        self.pivot = pygame.Vector2(pivot)

    def draw(self, target, pos, angle):
        """Draw with the pivot at `pos`. angle (deg) turns the 'hanging down'
        sprite counter-clockwise on screen, same as pygame.transform.rotate."""
        img = pygame.transform.rotozoom(self.image, angle, 1.0)
        centre = pygame.Vector2(self.image.get_size()) / 2 - self.pivot
        target.blit(img, img.get_rect(center=pos + centre.rotate(-angle)))

    def flipped(self):
        w = self.image.get_width()
        return PivotSprite(pygame.transform.flip(self.image, True, False),
                           (w - self.pivot.x, self.pivot.y))


def _crop_scale(surface, pivot, scale):
    """Crop a canvas-sized png to its content and scale it; keep the pivot aligned."""
    rect = surface.get_bounding_rect(min_alpha=1).inflate(4, 4).clip(surface.get_rect())
    part = surface.subsurface(rect).copy()
    size = (max(1, round(rect.w * scale)), max(1, round(rect.h * scale)))
    part = pygame.transform.smoothscale(part, size)
    return PivotSprite(part, ((pivot[0] - rect.x) * scale, (pivot[1] - rect.y) * scale))


def stretch_leg(surface, k, split):
    """Lengthen a leg png by k: rows between the pivot and `split` are stretched,
    rows below `split` (the shoe) are only moved down. The pivot stays put."""
    if k == 1:
        return surface
    w, h = surface.get_size()
    top = int(config.LEG_PIVOT[1])
    split = min(split, h)
    mid_h = round((split - top) * k)
    out = pygame.Surface((w, top + mid_h + h - split), pygame.SRCALPHA)
    out.blit(surface, (0, 0), (0, 0, w, top))
    mid = surface.subsurface((0, top, w, split - top))
    out.blit(pygame.transform.smoothscale(mid, (w, mid_h)), (0, top))
    out.blit(surface, (0, top + mid_h), (0, split, w, h - split))
    return out


def recolor_red(surface, weights):
    """Filter that recolours the red shoe while keeping its shading.

    On reddish pixels the 'redness' (R above the grey level) is redistributed
    over the channels with `weights` (r, g, b), e.g. (0, 1, 0) = green.
    """
    out = surface.copy()
    rgb = pygame.surfarray.pixels3d(out)
    r, g, b = (rgb[..., i].astype(np.float32) for i in range(3))
    mask = (r > g + 40) & (r > b + 40)
    grey = (g + b) / 2
    for i, w in enumerate(weights):
        rgb[..., i][mask] = np.clip(grey + (r - grey) * w, 0, 255)[mask].astype(np.uint8)
    del rgb
    return out


class CharacterSprites:
    """Head, thigh and shin(+shoe) sprites at game scale.

    Leg sprites hang straight down from their pivot; shoes point right (+x),
    so left legs use mirrored copies to keep the toes pointing outward.
    """

    def __init__(self, scale, leg_stretch=1.0):
        def load(name):
            return pygame.image.load(config.asset(name)).convert_alpha()

        self.scale = scale
        self.leg_stretch = leg_stretch
        self.head = _crop_scale(load("head.png"), config.HEAD_CENTER, scale)
        thigh = _crop_scale(stretch_leg(load("leg-part.png"), leg_stretch, config.SPRITE_CANVAS),
                            config.LEG_PIVOT, scale)
        shin = _crop_scale(stretch_leg(load("leg-part-with-shoe.png"), leg_stretch, config.SHOE_TOP),
                           config.LEG_PIVOT, scale)
        green = PivotSprite(recolor_red(shin.image, (0.0, 1.0, 0.0)), shin.pivot)
        purple = PivotSprite(recolor_red(shin.image, (0.7, 0.0, 1.0)), shin.pivot)

        # [side] -> sprite, side = -1 (left) or +1 (right)
        self.thigh = {+1: thigh, -1: thigh.flipped()}
        self.shin = {+1: shin, -1: shin.flipped()}               # normal: red shoe
        self.shin_sticky = {+1: green, -1: green.flipped()}      # sticky, in the air
        self.shin_stuck = {+1: purple, -1: purple.flipped()}     # sticky and glued to rock
