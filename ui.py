"""Small UI helpers: clickable buttons and outlined text."""
import pygame


def draw_text(surface, text, font, color, center, outline=(0, 0, 0), width=3):
    """Text with a dark outline so it reads on top of the busy map art."""
    img = font.render(text, True, color)
    rect = img.get_rect(center=center)
    if outline is not None:
        shadow = font.render(text, True, outline)
        for dx in range(-width, width + 1, width):
            for dy in range(-width, width + 1, width):
                if dx or dy:
                    surface.blit(shadow, rect.move(dx, dy))
    surface.blit(img, rect)
    return rect


class Button:
    def __init__(self, text, center, size, font, color=(70, 160, 70), subtitle=None, small_font=None):
        self.text = text
        self.rect = pygame.Rect(0, 0, *size)
        self.rect.center = center
        self.font = font
        self.color = pygame.Color(color)
        self.subtitle = subtitle
        self.small_font = small_font

    def clicked(self, event, pos):
        """pos = event.pos already mapped to canvas coordinates."""
        return (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(pos))

    def draw(self, surface, mouse=None):
        hover = mouse is not None and self.rect.collidepoint(mouse)
        fill = self.color.lerp((255, 255, 255), 0.25) if hover else self.color
        rect = self.rect.inflate(8, 8) if hover else self.rect
        pygame.draw.rect(surface, (0, 0, 0), rect.move(4, 5), border_radius=18)
        pygame.draw.rect(surface, fill, rect, border_radius=18)
        pygame.draw.rect(surface, (0, 0, 0), rect, 4, border_radius=18)
        if self.subtitle and self.small_font:   # subtitle = list of lines
            draw_text(surface, self.text, self.font, (255, 255, 255),
                      (rect.centerx, rect.centery - rect.h * 0.18))
            line_h = self.small_font.get_linesize()
            for i, line in enumerate(self.subtitle):
                draw_text(surface, line, self.small_font, (255, 255, 255),
                          (rect.centerx, rect.centery + rect.h * 0.15 + i * line_h), width=2)
        else:
            draw_text(surface, self.text, self.font, (255, 255, 255), rect.center)


class MapButton(Button):
    """A button showing a map picture with its name underneath."""

    def __init__(self, name, image, center, font, color=(60, 60, 70)):
        pad, label_h = 14, font.get_linesize() + 6
        size = (image.get_width() + 2 * pad, image.get_height() + label_h + 2 * pad)
        super().__init__(name, center, size, font, color)
        self.image, self.pad = image, pad

    def draw(self, surface, mouse=None):
        hover = mouse is not None and self.rect.collidepoint(mouse)
        fill = self.color.lerp((255, 255, 255), 0.25) if hover else self.color
        rect = self.rect.inflate(10, 10) if hover else self.rect
        pygame.draw.rect(surface, (0, 0, 0), rect.move(4, 5), border_radius=18)
        pygame.draw.rect(surface, fill, rect, border_radius=18)
        pygame.draw.rect(surface, (0, 0, 0), rect, 4, border_radius=18)
        img_rect = self.image.get_rect(midtop=(rect.centerx, rect.top + self.pad))
        surface.blit(self.image, img_rect)
        pygame.draw.rect(surface, (0, 0, 0), img_rect, 2)
        draw_text(surface, self.text, self.font, (255, 255, 255),
                  (rect.centerx, (img_rect.bottom + rect.bottom) // 2), width=2)
