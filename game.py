"""Game scene: ties terrain, character, camera view and the players' input together.

Every frame of Game.run():
    1. handle keys/window events
    2. read the players (arm angles, mouths) from the input source
    3. turn them into leg targets and sticky flags (apply_players)
    4. run the physics a few small steps (substeps)
    5. move the camera view, update the timer, check the flag
    6. draw everything and show it (display.present)
"""
import pygame

import config
from assets import CharacterSprites
from character import Character
from ui import draw_text
from viewport import Viewport, view_size

LEG_LABELS = {"upper_left": "top-left", "upper_right": "top-right",
              "lower_left": "bottom-left", "lower_right": "bottom-right"}


def apply_players(character, scheme, players):
    """Players' limb angles -> leg targets, mouths (and head tilt) -> sticky feet."""
    # scheme rows look like (0, "left_arm", "upper_left"): player 0's left arm
    # drives the character's upper-left leg (see config.CONTROL_SCHEMES)
    for player, limb, leg_name in scheme:
        if player >= len(players):      # vision thread not switched over yet
            continue
        st = players[player]
        leg = character.legs[leg_name]
        pose = st.limbs.get(limb)
        if pose is not None:            # arm not seen this frame: the leg keeps its last target
            leg.set_target(pose.thigh, pose.bend)
        # 1 player: head tilt picks a side, only that side's foot gets sticky
        side_ok = st.sticky_side is None or limb.startswith(st.sticky_side)
        leg.sticky = st.mouth_open and side_ok


class Game:
    """run(num_players, game_map) plays until Esc ('menu') or window close ('quit').
    Touching the flag with the head completes the level and stops the timer."""

    def __init__(self, display, input_source, debug=False):
        self.display = display
        self.canvas = display.canvas            # draw here; display.present() shows it
        self.map = self.terrain = self.flag = self.view = None   # set when a game starts
        self.input = input_source
        self.debug = debug

        # sprite scale: the 500 px character canvas becomes 1/8 of the map height
        self.sprite_scale = config.MAP_HEIGHT * config.CHARACTER_FRACTION / config.SPRITE_CANVAS
        self._sprites = {}          # leg stretch -> CharacterSprites
        self.character = None
        self.font = pygame.font.SysFont("arial", 20, bold=True)
        self.timer_font = pygame.font.SysFont("consolas,couriernew", 40, bold=True)
        self.clock = pygame.time.Clock()        # measures frame time and limits the FPS
        self.scheme = config.CONTROL_SCHEMES[2]
        self.elapsed = 0.0                      # timer, seconds
        self.finished = False
        self.best = {}              # (map name, player count) -> best time this session
        self.big_font = pygame.font.SysFont("arialblack,arial", 72, bold=True)
        self.mid_font = pygame.font.SysFont("arialblack,arial", 34, bold=True)

    def spawn_point(self):
        return pygame.Vector2(self.map.spawn)

    def build_character(self, num_players):
        """Only the legs that someone controls, stretched for small teams."""
        stretch = config.LEG_STRETCH.get(num_players, 1.0)
        if stretch not in self._sprites:        # build each sprite set once, then reuse it
            self._sprites[stretch] = CharacterSprites(self.sprite_scale, stretch)
        legs = [leg for _, _, leg in self.scheme]
        return Character(self._sprites[stretch], self.spawn_point(), legs)

    def restart(self):
        self.character.reset(self.spawn_point())
        self.view.snap(self.character.pos)
        self.elapsed = 0.0
        self.finished = False

    # ------------------------------------------------------------------ loop --
    def run(self, num_players, game_map):
        self.map, self.terrain, self.flag = game_map, game_map.terrain, game_map.flag
        self.view = Viewport(self.terrain.width, self.terrain.height, *view_size())
        self.input.set_num_players(num_players)
        self.scheme = config.CONTROL_SCHEMES[num_players]
        self.character = self.build_character(num_players)
        self.restart()
        self.clock.tick()                       # reset the clock so the first dt is small
        while True:
            # tick() waits so the loop runs at most FPS times per second and returns
            # the ms since the last frame. dt is capped at 1/20 s so a hiccup (e.g.
            # dragging the window) can't make the physics take one giant step.
            dt = min(self.clock.tick(config.FPS) / 1000.0, 1 / 20)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if self.display.handle_event(event):    # F11 etc.
                    continue
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or (
                            self.finished and event.key == pygame.K_RETURN):
                        return "menu"
                    if event.key == pygame.K_F5:
                        self.restart()
                    elif event.key == pygame.K_F1:
                        self.debug = not self.debug

            players = self.input.get_players()
            self.apply_players(players)
            # several small physics steps per frame: smaller steps = fewer feet
            # passing through thin rock and a more stable solver
            sub = dt / config.PHYSICS_SUBSTEPS
            for _ in range(config.PHYSICS_SUBSTEPS):
                self.character.update(sub, self.terrain)
            self.view.follow(self.character.pos, dt)
            if not self.finished:
                self.elapsed += dt
                if self.flag.touches(self.character.pos, self.character.head_radius):
                    self.complete(num_players)

            self.draw(players)

    def complete(self, num_players):
        """Flag reached: stop the timer and remember the best time."""
        self.finished = True
        key = (self.map.name, num_players)
        best = self.best.get(key)
        self.new_best = best is None or self.elapsed < best
        if self.new_best:
            self.best[key] = self.elapsed

    def apply_players(self, players):
        apply_players(self.character, self.scheme, players)

    # --------------------------------------------------------------- drawing --
    def draw(self, players):
        # Painter's order: things drawn later cover earlier ones.
        rect = self.view.rect
        offset = pygame.Vector2(rect.topleft)
        self.canvas.blit(self.terrain.surface, (0, 0), rect)   # copy just the visible part of the map
        self.flag.draw(self.canvas, offset)
        self.character.draw(self.canvas, offset, self.debug)
        self.draw_leg_owners(offset)
        self.draw_hud(players)
        self.draw_timer()
        if self.finished:
            self.draw_complete()
        self.display.present()

    def draw_leg_owners(self, offset):
        """Small dot on each knee in the colour of the player driving that leg."""
        for player, _, leg_name in self.scheme:
            _, knee, _ = self.character.legs[leg_name].joints(self.character.pos - offset)
            pygame.draw.circle(self.canvas, (0, 0, 0), knee, 7)     # black ring
            pygame.draw.circle(self.canvas, config.PLAYER_COLORS_RGB[player], knee, 5)

    def draw_hud(self, players):
        """Status text in the top-left corner."""
        y = 10
        n = len({p for p, _, _ in self.scheme})                    # number of players
        for i in range(n):
            st = players[i] if i < len(players) else None
            legs = ", ".join(LEG_LABELS[leg] for p, _, leg in self.scheme if p == i)
            state = ("STICKY" if st.mouth_open else "free") if st and st.visible else "not seen"
            self._text(f"P{i + 1} [{legs}]: {state}", (10, y), config.PLAYER_COLORS_RGB[i])
            y += 24
        height = self.terrain.height - self.character.pos.y        # y grows downward
        self._text(f"{self.map.name}   height {height / self.terrain.height * 100:.0f}%   "
                   f"F5 restart  F1 debug  F11 fullscreen  Esc menu   {self.clock.get_fps():.0f} FPS",
                   (10, y), (255, 255, 255))

    @staticmethod
    def format_time(t):
        """83.456 s -> "01:23.46"."""
        minutes, seconds = divmod(t, 60)
        return f"{int(minutes):02d}:{seconds:05.2f}"

    def draw_complete(self):
        """The "COMPLETED!" overlay with time and best time."""
        w, h = self.canvas.get_size()
        shade = pygame.Surface((w, h), pygame.SRCALPHA)   # see-through dark layer
        shade.fill((0, 0, 0, 110))                        # alpha 110 of 255
        self.canvas.blit(shade, (0, 0))
        draw_text(self.canvas, "COMPLETED!", self.big_font, (255, 215, 60), (w // 2, h * 0.34), width=5)
        draw_text(self.canvas, f"time  {self.format_time(self.elapsed)}", self.mid_font,
                  (255, 255, 255), (w // 2, h * 0.50))
        n = len({p for p, _, _ in self.scheme})
        best = ("NEW BEST!" if self.new_best
                else f"best  {self.format_time(self.best[(self.map.name, n)])}")
        draw_text(self.canvas, best, self.mid_font, (120, 255, 120), (w // 2, h * 0.59))
        draw_text(self.canvas, "Enter: menu    F5: play again", self.font,
                  (255, 255, 255), (w // 2, h * 0.70), width=2)

    def draw_timer(self):
        text = self.format_time(self.elapsed)
        color = (255, 215, 60) if self.finished else (255, 255, 255)    # gold when finished
        img = self.timer_font.render(text, True, (255, 255, 255))      # only to measure the width
        center = (self.canvas.get_width() - img.get_width() // 2 - 20, 32)   # top-right corner
        draw_text(self.canvas, text, self.timer_font, color, center)

    def _text(self, msg, pos, color):
        """Small text with a 2 px black shadow so it reads on any background."""
        shadow = self.font.render(msg, True, (0, 0, 0))
        self.canvas.blit(shadow, (pos[0] + 2, pos[1] + 2))
        self.canvas.blit(self.font.render(msg, True, color), pos)
