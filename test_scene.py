"""1-player test: the character hangs fixed in front of a white background so a
player can check arm -> leg control, mouth (sticky) and head tilt without physics."""
import pygame

import config
from assets import CharacterSprites
from character import Character
from game import apply_players
from ui import draw_text

PLAYERS = 1
TEST_CHARACTER_SCALE = 0.62   # sprite scale (canvas px per png px), bigger than in game
BG = (255, 255, 255)


class TestScene:
    """run() until Esc ('menu') or window close ('quit')."""

    def __init__(self, display, input_source):
        self.display = display
        self.canvas = display.canvas
        self.input = input_source
        w, h = self.canvas.get_size()
        self.center = pygame.Vector2(w / 2, h * 0.56)
        self.scheme = config.CONTROL_SCHEMES[PLAYERS]
        sprites = CharacterSprites(TEST_CHARACTER_SCALE, config.LEG_STRETCH.get(PLAYERS, 1.0))
        self.character = Character(sprites, self.center, [leg for _, _, leg in self.scheme])
        self.huge_font = pygame.font.SysFont("arialblack,arial", int(h * 0.12), bold=True)
        self.mid_font = pygame.font.SysFont("arialblack,arial", int(h * 0.05), bold=True)
        self.small_font = pygame.font.SysFont("arial", int(h * 0.03), bold=True)
        self.clock = pygame.time.Clock()

    def run(self):
        self.input.set_num_players(PLAYERS)
        self.character.reset(self.center)
        self.clock.tick()
        while True:
            dt = min(self.clock.tick(config.FPS) / 1000.0, 1 / 20)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if self.display.handle_event(event):
                    continue
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return "menu"
            players = self.input.get_players()
            apply_players(self.character, self.scheme, players)
            # no Character.update() here = no physics: only the leg angles are
            # moved towards the arm angles, the body never falls or moves
            for leg in self.character.legs.values():   # legs move, body stays put
                leg.update_angles(dt)
            self.draw(players[0] if players else None)
            self.display.present()

    def draw(self, st):
        c = self.canvas
        w, h = c.get_size()
        c.fill(BG)
        self.character.draw(c, pygame.Vector2(0, 0))    # offset 0: the position is already a canvas position

        if st is None or not st.visible:
            mouth, color = "NOT SEEN", (150, 150, 150)
        elif st.mouth_open:
            mouth, color = "MOUTH OPEN", (40, 200, 40)
        else:
            mouth, color = "MOUTH CLOSED", (220, 60, 60)
        draw_text(c, mouth, self.huge_font, color, (w // 2, int(h * 0.11)), width=4)

        if st is not None and st.sticky_side is not None:
            side = st.sticky_side.upper()
            draw_text(c, f"sticky foot: {side}", self.mid_font, (255, 255, 255),
                      (w // 2, int(h * 0.22)), width=3)
            draw_text(c, f"head roll {st.head_tilt:+.0f} deg  (switch at "
                         f"+-{config.HEAD_TILT_ANGLE:.0f})", self.small_font, (60, 60, 60),
                      (w // 2, int(h * 0.285)), outline=None)
        draw_text(c, "1 PLAYER TEST   Esc: menu   F11: fullscreen", self.small_font, (90, 90, 90),
                  (int(w * 0.2), int(h * 0.97)), outline=None)
