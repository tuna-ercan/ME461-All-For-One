"""Options screen: tune the settings in settings.SETTINGS with sliders and switches.

Changes apply immediately (they are written into `config`) and are saved to
settings.json when the player leaves the screen. While tuning, the Mouth and
Head tilt tabs show the live camera values so the thresholds can be set by
watching them.
"""
import pygame

import config
from settings import GROUPS, SETTINGS
from ui import Button, Slider, Toggle, draw_text

ROW_H = 0.105          # height of one setting row (fraction of the canvas height)


def format_value(setting, value):
    if setting.kind == "bool":
        return "ON" if value else "OFF"
    if setting.kind == "int" or setting.step >= 1:
        text = f"{value:.0f}"
    else:
        decimals = len(f"{setting.step:g}".split(".")[1])     # 0.05 -> 2 decimals
        text = f"{value:.{decimals}f}"
    return f"{text} {setting.unit}".strip()


class OptionsScene:
    """run() until BACK/Esc ('menu') or window close ('quit'); saves on the way out."""

    def __init__(self, display, maps, input_source, settings):
        self.display = display
        self.canvas = display.canvas
        self.input = input_source
        self.settings = settings
        w, h = self.canvas.get_size()
        self.backdrop = pygame.transform.smoothscale(maps[0].terrain.surface, (w, h))
        shade = pygame.Surface((w, h), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 165))
        self.backdrop.blit(shade, (0, 0))

        self.title_font = pygame.font.SysFont(config.FONT_HEAVY, int(h * 0.075), bold=True)
        self.tab_font = pygame.font.SysFont(config.FONT_HEAVY, int(h * 0.032), bold=True)
        self.label_font = pygame.font.SysFont(config.FONT_TEXT, int(h * 0.034), bold=True)
        self.value_font = pygame.font.SysFont(config.FONT_MONO, int(h * 0.034), bold=True)
        self.help_font = pygame.font.SysFont(config.FONT_TEXT, int(h * 0.028))
        self.clock = pygame.time.Clock()

        # left column: one tab per group
        self.tabs = []
        for i, group in enumerate(GROUPS):
            self.tabs.append((group, Button(group.upper(), (int(w * 0.13), int(h * (0.22 + i * 0.095))),
                                            (int(w * 0.19), int(h * 0.075)), self.tab_font, (70, 70, 80))))
        # right panel: one row per setting of the selected group
        self.panel = pygame.Rect(int(w * 0.255), int(h * 0.17), int(w * 0.715), int(h * 0.62))
        self.rows = {}                                   # key -> (label pos, value pos, widget)
        for group in GROUPS:
            items = [s for s in SETTINGS if s.group == group]
            for i, s in enumerate(items):
                y = int(self.panel.y + h * (0.075 + i * ROW_H))
                if s.kind == "bool":
                    widget = Toggle((int(w * 0.80), y - 16, 74, 32))
                else:
                    widget = Slider((int(w * 0.66), y - 12, int(w * 0.28), 24), s.lo, s.hi, s.step)
                self.rows[s.key] = ((self.panel.x + 24, y), (int(w * 0.585), y), widget)
        self.reset = Button("RESET TO DEFAULTS", (int(w * 0.36), int(h * 0.92)),
                            (int(w * 0.25), int(h * 0.085)), self.tab_font, (190, 120, 40))
        self.back = Button("BACK", (int(w * 0.84), int(h * 0.92)), (int(w * 0.15), int(h * 0.085)),
                           self.tab_font, (90, 90, 90))
        self.group = GROUPS[0]
        self.hover_help = ""

    def visible(self):
        return [s for s in SETTINGS if s.group == self.group]

    def run(self):
        self.group = GROUPS[0]
        while True:
            self.clock.tick(config.FPS)
            # head tilt is only measured in 1-player mode; elsewhere watch up to 4 people
            self.input.set_num_players(1 if self.group == "Head tilt" else config.MAX_PLAYERS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.settings.save()
                    return "quit"
                if self.display.handle_event(event):
                    continue
                pos = self.display.to_canvas(event.pos) if hasattr(event, "pos") else (-1, -1)
                escape = event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                if escape or self.back.clicked(event, pos):
                    self.settings.save()
                    return "menu"
                if self.reset.clicked(event, pos):
                    self.settings.reset()
                    self._apply_fullscreen()
                for group, button in self.tabs:
                    if button.clicked(event, pos):
                        self.group = group
                for s in self.visible():
                    widget = self.rows[s.key][2]
                    if s.kind == "bool":
                        if widget.clicked(event, pos):
                            self.settings.set(s.key, not self.settings.get(s.key))
                            if s.key == "START_FULLSCREEN":
                                self._apply_fullscreen()
                    else:
                        value = widget.handle(event, pos)
                        if value is not None:
                            self.settings.set(s.key, value)
            self.draw()
            self.display.present()

    def _apply_fullscreen(self):
        """Make the window match the Fullscreen setting right away."""
        if self.display.fullscreen != config.START_FULLSCREEN:
            self.display.toggle_fullscreen()

    # ---------------------------------------------------------------- draw --
    def draw(self):
        c = self.canvas
        w, h = c.get_size()
        mouse = self.display.to_canvas(pygame.mouse.get_pos())
        c.blit(self.backdrop, (0, 0))
        draw_text(c, "Options", self.title_font, (255, 215, 60), (w // 2, int(h * 0.08)), width=4)

        for group, button in self.tabs:
            button.color = pygame.Color((60, 110, 200) if group == self.group else (70, 70, 80))
            button.draw(c, mouse)

        pygame.draw.rect(c, (25, 27, 32), self.panel, border_radius=16)
        pygame.draw.rect(c, (0, 0, 0), self.panel, 3, border_radius=16)
        help_text = ""
        for s in self.visible():
            (lx, ly), (vx, vy), widget = self.rows[s.key]
            value = self.settings.get(s.key)
            changed = value != self.settings.defaults[s.key]
            label = self.label_font.render(s.label + ("  *" if changed else ""), True,
                                           (255, 225, 120) if changed else (235, 235, 235))
            c.blit(label, label.get_rect(midleft=(lx, ly)))
            draw_text(c, format_value(s, value), self.value_font, (255, 255, 255), (vx, vy), width=1)
            widget.draw(c, value)
            row = pygame.Rect(self.panel.x, ly - h * ROW_H / 2, self.panel.w, h * ROW_H)
            if row.collidepoint(mouse) or getattr(widget, "dragging", False):
                help_text = s.help
        live = self._live_text()
        if live:
            draw_text(c, live, self.label_font, (120, 230, 140),
                      (self.panel.centerx, self.panel.bottom - int(h * 0.05)), width=1)
        default_help = "* = changed from the default.   Changes apply at once and are saved when you leave."
        draw_text(c, help_text or default_help, self.help_font, (210, 210, 210),
                  (w // 2, int(h * 0.835)), width=1)
        self.reset.draw(c, mouse)
        self.back.draw(c, mouse)

    def _live_text(self):
        """Live camera values for the tabs where they help tuning."""
        players = self.input.get_players()
        if self.group == "Mouth":
            parts = []
            for i, st in enumerate(players):
                if st.visible and st.face_found:
                    parts.append(f"P{i + 1} {st.mouth_score:.2f} {'OPEN' if st.mouth_open else 'closed'}")
            return "Live:  " + ("    ".join(parts) if parts else "no face seen")
        if self.group == "Head tilt":
            st = players[0] if players else None
            if st is None or st.sticky_side is None:
                return "Live head tilt is measured in 1-player mode (try it in 1P TEST)."
            return f"Live:  roll {st.head_tilt:+.0f} deg  ->  sticky foot {st.sticky_side.upper()}"
        return ""
