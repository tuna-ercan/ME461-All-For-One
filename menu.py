"""Main menu: title + Play / Test, then the player-count picker, then the map picker.

The menu is one loop with a `page` variable ("title" -> "players" -> "maps").
Every frame it handles clicks/keys for the current page and redraws that page.
All positions are fractions of the canvas size (e.g. h * 0.80 = 80% down),
so the layout stays right if the canvas size ever changes.
"""
import pygame

import config
from ui import Button, MapButton, draw_text

# two lines of help text shown on each player-count button
PLAYER_INFO = {
    1: ["two long legs", "left arm + right arm"],
    2: ["P1 arms: top legs", "P2 arms: bottom legs"],
    3: ["P1 arms: top legs", "P2 left arm, P3 right arm"],
    4: ["one arm = one leg", "P1 P2 top, P3 P4 bottom"],
}


class Menu:
    """run() returns ("play", players, map index), ("test", 1), ("options",) or None to quit."""

    def __init__(self, display, maps, input_source):
        self.display = display
        self.canvas = display.canvas
        self.input = input_source
        w, h = self.canvas.get_size()
        # background picture: the whole first map shrunk to the canvas
        self.backdrop = pygame.transform.smoothscale(maps[0].terrain.surface, (w, h))
        demo = pygame.image.load(config.asset("character-demo.png")).convert_alpha()
        size = int(h * 0.42)
        self.demo = pygame.transform.smoothscale(demo, (size, size))

        # SysFont("a,b,...") uses the first installed font of the list (see config FONT_*)
        self.title_font = pygame.font.SysFont(config.FONT_HEAVY, int(h * 0.13), bold=True)
        self.big_font = pygame.font.SysFont(config.FONT_HEAVY, int(h * 0.06), bold=True)
        self.mid_font = pygame.font.SysFont(config.FONT_HEAVY, int(h * 0.04), bold=True)
        self.small_font = pygame.font.SysFont(config.FONT_TEXT, int(h * 0.024), bold=True)
        self.credit_font = pygame.font.SysFont(config.FONT_TEXT, int(h * 0.034), bold=True)
        self.sheep = self._render_emoji(config.GAME_CREDIT_EMOJI, int(h * 0.04))
        self.clock = pygame.time.Clock()

        cx = w // 2
        self.play = Button("PLAY", (cx, int(h * 0.80)), (int(w * 0.22), int(h * 0.12)),
                           self.big_font, (220, 60, 60))
        self.options = Button("OPTIONS", (int(w * 0.20), int(h * 0.80)), (int(w * 0.15), int(h * 0.09)),
                              self.mid_font, (190, 120, 40))
        self.test = Button("1P TEST", (int(w * 0.80), int(h * 0.80)), (int(w * 0.15), int(h * 0.09)),
                           self.mid_font, (60, 110, 200))
        bw, bh = int(w * 0.21), int(h * 0.22)
        self.counts = []
        for i, n in enumerate(range(1, config.MAX_PLAYERS + 1)):
            x = int(w * (0.5 + (i - 1.5) * 0.235))      # 4 buttons spread around the centre
            label = f"{n} PLAYER" + ("S" if n > 1 else "")
            self.counts.append((n, Button(label, (x, int(h * 0.55)), (bw, bh), self.big_font,
                                          config.PLAYER_COLORS_RGB[i], PLAYER_INFO[n],
                                          self.small_font)))
        self.back = Button("BACK", (cx, int(h * 0.85)), (int(w * 0.14), int(h * 0.09)),
                           self.big_font, (90, 90, 90))
        self.maps = []
        for game_map in maps:
            self.maps.append(MapButton(game_map.name.upper(), game_map.thumbnail,
                                       (0, int(h * 0.58)), self.mid_font))
        # side by side, centred, with equal gaps (the cards have different widths)
        gap = 40
        x = (w - sum(b.rect.w for b in self.maps) - gap * (len(self.maps) - 1)) // 2
        for b in self.maps:
            b.rect.left = x
            x += b.rect.w + gap
        self.players = 1

    def run(self):
        page = "title"
        while True:
            self.clock.tick(config.FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if self.display.handle_event(event):
                    continue
                # mouse events have a window position: convert it to canvas pixels,
                # because the buttons were placed on the canvas
                pos = self.display.to_canvas(event.pos) if hasattr(event, "pos") else (-1, -1)
                key = event.key if event.type == pygame.KEYDOWN else None
                if key == pygame.K_ESCAPE:
                    if page == "title":
                        return None
                    page = "players" if page == "maps" else "title"
                if page == "title":
                    if self.play.clicked(event, pos) or key == pygame.K_RETURN:
                        page = "players"
                    elif self.test.clicked(event, pos) or key == pygame.K_t:
                        return "test", 1
                    elif self.options.clicked(event, pos) or key == pygame.K_o:
                        return ("options",)
                elif page == "players":
                    if self.back.clicked(event, pos):
                        page = "title"
                    for n, button in self.counts:
                        if button.clicked(event, pos) or key == pygame.K_0 + n:
                            self.players, page = n, "maps"
                            break
                else:
                    if self.back.clicked(event, pos):
                        page = "players"
                    for i, button in enumerate(self.maps):
                        if button.clicked(event, pos) or key == pygame.K_1 + i:
                            return "play", self.players, i
            self.draw(page)
            self.display.present()

    @staticmethod
    def _render_emoji(char, size):
        """The emoji as a picture, or None if no emoji font is installed (common on
        Linux) - then the credit line is shown without it instead of an empty box."""
        if pygame.font.match_font(config.FONT_EMOJI) is None:
            return None
        try:
            return pygame.font.SysFont(config.FONT_EMOJI, size).render(char, True, (255, 255, 255))
        except (pygame.error, ValueError):   # e.g. a bitmap emoji font that can't be resized
            return None

    def draw_credit(self, cx, cy):
        """'From The Group MeEeEe' + a colour sheep emoji (if an emoji font exists)."""
        text = self.credit_font.render(config.GAME_CREDIT, True, (255, 255, 255))
        sheep = self.sheep
        gap = 8 if sheep else 0
        left = cx - (text.get_width() + gap + (sheep.get_width() if sheep else 0)) // 2
        draw_text(self.canvas, config.GAME_CREDIT, self.credit_font, (255, 255, 255),
                  (left + text.get_width() // 2, cy), width=2)
        if sheep:
            self.canvas.blit(sheep, sheep.get_rect(midleft=(left + text.get_width() + gap, cy)))

    def draw(self, page):
        c = self.canvas
        w, h = c.get_size()
        mouse = self.display.to_canvas(pygame.mouse.get_pos())
        c.blit(self.backdrop, (0, 0))
        shade = pygame.Surface((w, h), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 90))
        c.blit(shade, (0, 0))
        draw_text(c, config.GAME_TITLE, self.title_font, (255, 215, 60),
                  (w // 2, int(h * 0.14)), width=5)
        self.draw_credit(w // 2, int(h * 0.245))
        if page == "title":
            c.blit(self.demo, self.demo.get_rect(center=(w // 2, int(h * 0.51))))
            self.play.draw(c, mouse)
            self.test.draw(c, mouse)
            self.options.draw(c, mouse)
            draw_text(c, "F11 fullscreen", self.small_font, (230, 230, 230),
                      (int(w * 0.92), int(h * 0.96)), width=2)
        elif page == "players":
            draw_text(c, "How many players?", self.big_font, (255, 255, 255),
                      (w // 2, int(h * 0.32)))
            for _, button in self.counts:
                button.draw(c, mouse)
            self.back.draw(c, mouse)
        else:
            players = f"{self.players} player" + ("s" if self.players > 1 else "")
            draw_text(c, f"Choose a map  ({players})", self.big_font, (255, 255, 255),
                      (w // 2, int(h * 0.32)))
            for button in self.maps:
                button.draw(c, mouse)
            self.back.draw(c, mouse)
