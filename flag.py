"""Goal flag: stands on the top-right peak; touching it with the head wins."""
import pygame

import config


class Flag:
    def __init__(self, terrain):
        img = pygame.image.load(config.asset("flag.png")).convert_alpha()
        scale = terrain.height * config.FLAG_FRACTION / img.get_height()
        self.image = pygame.transform.smoothscale(
            img, (round(img.get_width() * scale), round(img.get_height() * scale)))
        self.mask = pygame.mask.from_surface(self.image)

        # stand on the highest ground of the right edge, fully inside the map
        base_x, base_y = config.FLAG_BASE[0] * scale, config.FLAG_BASE[1] * scale
        x_min = int(terrain.width * (1 - config.FLAG_SEARCH))
        x_max = int(terrain.width - (self.image.get_width() - base_x))
        peak_x = min(range(x_min, max(x_min + 1, x_max)), key=terrain.ground_y)
        self.pos = pygame.Vector2(peak_x - base_x, terrain.ground_y(peak_x) - base_y)
        self.rect = self.image.get_rect(topleft=self.pos)

    def touches(self, center, radius):
        """True if a circle (the head) overlaps the flag's visible pixels."""
        r = int(radius)
        circle = pygame.Surface((2 * r + 1, 2 * r + 1), pygame.SRCALPHA)
        pygame.draw.circle(circle, (255, 255, 255), (r, r), r)
        offset = (int(center[0] - r - self.rect.x), int(center[1] - r - self.rect.y))
        return self.mask.overlap(pygame.mask.from_surface(circle), offset) is not None

    def draw(self, target, offset):
        target.blit(self.image, self.pos - offset)
