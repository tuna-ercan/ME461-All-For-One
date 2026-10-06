"""Map overview for the panel under the camera: the whole map, the flag, the
part of the map the game view shows, and where the character is."""
import pygame

MARKER = (255, 220, 40)        # character dot (yellow, visible on sky and in the dark cave)
VIEW_FRAME = (255, 255, 255)   # rectangle of the area shown in the game view


class MiniMap:
    def __init__(self, game_map):
        self.map = game_map
        self._image = None          # map picture scaled for the panel (made once per panel size)
        self._size = None

    def _picture(self, size):
        """The whole map with its flag, shrunk to `size`. Cached: scaling the big map
        picture is slow, so it is redone only when the panel size changes (F11)."""
        if size != self._size:
            t = self.map.terrain
            k = size[1] / t.height
            img = pygame.transform.smoothscale(t.surface, size)
            flag = self.map.flag
            fw, fh = flag.image.get_size()
            small = pygame.transform.smoothscale(flag.image, (max(1, round(fw * k)), max(1, round(fh * k))))
            img.blit(small, flag.pos * k)
            self._image, self._size = img, size
        return self._image

    def draw(self, surface, rect, char_pos, view_rect):
        """Draw into `rect` (window pixels); returns the rectangle actually used."""
        t = self.map.terrain
        k = min(rect.w / t.width, rect.h / t.height)        # fit the whole map, keep its shape
        img = self._picture((max(1, round(t.width * k)), max(1, round(t.height * k))))
        area = img.get_rect(center=rect.center)
        surface.blit(img, area)
        self.map.draw_movers_small(surface, area.topleft, k)   # windmill rotor, turning

        # the part of the map that the game view shows right now
        view = pygame.Rect(area.x + view_rect.x * k, area.y + view_rect.y * k,
                           max(2, view_rect.w * k), max(2, view_rect.h * k)).clip(area)
        pygame.draw.rect(surface, (0, 0, 0), view.inflate(2, 2), 1)
        pygame.draw.rect(surface, VIEW_FRAME, view, 2)

        # the character: a dot with a dark ring, kept inside the picture even when
        # the character is above the map's top edge
        x = min(max(area.x + char_pos[0] * k, area.left + 6), area.right - 6)
        y = min(max(area.y + char_pos[1] * k, area.top + 6), area.bottom - 6)
        pygame.draw.circle(surface, (0, 0, 0), (x, y), 7)
        pygame.draw.circle(surface, MARKER, (x, y), 5)
        return area
