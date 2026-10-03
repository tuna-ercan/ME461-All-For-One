"""Goal flag: stands on the top-right peak; touching it with the head wins."""
import pygame

import config


class Flag:
    def __init__(self, terrain):
        img = pygame.image.load(config.asset("flag.png")).convert_alpha()
        scale = config.MAP_HEIGHT * config.FLAG_FRACTION / img.get_height()   # same size on every map
        self.image = pygame.transform.smoothscale(
            img, (round(img.get_width() * scale), round(img.get_height() * scale)))
        self.mask = pygame.mask.from_surface(self.image)

        # stand on the highest ground near the right edge, fully inside the map:
        # find the right-most column with room above it for the whole flag, then
        # take the highest such ground within FLAG_SEARCH of the map width from there
        base_x, base_y = config.FLAG_BASE[0] * scale, config.FLAG_BASE[1] * scale
        x_max = int(terrain.width - (self.image.get_width() - base_x))
        fits = [x for x in range(x_max, int(base_x), -1) if terrain.ground_y(x) >= base_y]
        if not fits:
            fits = [x_max]
        window = [x for x in fits if x >= fits[0] - terrain.width * config.FLAG_SEARCH]
        peak_x = min(window, key=terrain.ground_y)
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
