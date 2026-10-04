"""Small UI helpers: clickable buttons, sliders, switches and outlined text."""
import pygame


def draw_text(surface, text, font, color, center, outline=(0, 0, 0), width=3):
    """Text with a dark outline so it reads on top of the busy map art."""
    img = font.render(text, True, color)        # True = smooth (anti-aliased) letters
    rect = img.get_rect(center=center)
    if outline is not None:
        # the outline = the same text in black, pasted 8 times around the real
        # position (left, right, up, down and the diagonals), then the text on top
        shadow = font.render(text, True, outline)
        for dx in range(-width, width + 1, width):
            for dy in range(-width, width + 1, width):
                if dx or dy:
                    surface.blit(shadow, rect.move(dx, dy))
    surface.blit(img, rect)
    return rect


class Button:
    """A rounded, clickable rectangle with a label (and optional lines of small text)."""

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
        hover = mouse is not None and self.rect.collidepoint(mouse)   # mouse over the button?
        # hovering: 25% lighter colour and slightly bigger, so it feels "pressable"
        fill = self.color.lerp((255, 255, 255), 0.25) if hover else self.color
        rect = self.rect.inflate(8, 8) if hover else self.rect
        pygame.draw.rect(surface, (0, 0, 0), rect.move(4, 5), border_radius=18)   # drop shadow
        pygame.draw.rect(surface, fill, rect, border_radius=18)                    # body
        pygame.draw.rect(surface, (0, 0, 0), rect, 4, border_radius=18)           # 4 px black border
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
        super().__init__(name, center, size, font, color)    # reuse Button's setup and clicked()
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


class Slider:
    """Horizontal slider for a number between lo and hi. Click or drag to change it."""

    def __init__(self, rect, lo, hi, step, color=(70, 160, 220)):
        self.rect = pygame.Rect(rect)        # the track
        self.lo, self.hi, self.step = lo, hi, step
        self.color = pygame.Color(color)
        self.dragging = False

    def value_at(self, x):
        """Mouse x position -> value on the track (snapped to the step)."""
        t = min(max((x - self.rect.x) / self.rect.w, 0.0), 1.0)
        v = self.lo + t * (self.hi - self.lo)
        return round(round(v / self.step) * self.step, 6)

    def handle(self, event, pos):
        """Returns the new value while the slider is clicked/dragged, otherwise None.
        pos = mouse position already converted to canvas coordinates."""
        grab = self.rect.inflate(16, 24)     # a bit bigger than the thin track: easier to hit
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and grab.collidepoint(pos):
            self.dragging = True
            return self.value_at(pos[0])
        if event.type == pygame.MOUSEMOTION and self.dragging:
            return self.value_at(pos[0])
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        return None

    def draw(self, surface, value):
        t = (value - self.lo) / (self.hi - self.lo) if self.hi > self.lo else 0
        knob_x = self.rect.x + t * self.rect.w
        track = self.rect.inflate(0, -self.rect.h + 8)               # 8 px tall bar, centred
        pygame.draw.rect(surface, (60, 60, 66), track, border_radius=4)
        filled = track.copy()
        filled.w = max(0, int(knob_x - track.x))
        pygame.draw.rect(surface, self.color, filled, border_radius=4)  # part left of the knob
        pygame.draw.circle(surface, (0, 0, 0), (knob_x, self.rect.centery), 11)
        pygame.draw.circle(surface, (255, 255, 255), (knob_x, self.rect.centery), 8)


class Toggle:
    """On/off switch. Click anywhere on it to flip."""

    def __init__(self, rect, color=(70, 180, 90)):
        self.rect = pygame.Rect(rect)
        self.color = pygame.Color(color)

    def clicked(self, event, pos):
        return (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.inflate(10, 10).collidepoint(pos))

    def draw(self, surface, on):
        r = self.rect.h // 2
        pygame.draw.rect(surface, self.color if on else (90, 90, 96), self.rect, border_radius=r)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2, border_radius=r)
        knob = (self.rect.right - r if on else self.rect.x + r, self.rect.centery)
        pygame.draw.circle(surface, (255, 255, 255), knob, r - 4)
