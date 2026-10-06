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
from minimap import MiniMap
from scoreboard import NAME_MAX, ScoreBoard
from ui import draw_text
from viewport import Viewport, view_size

BOARD_ROWS = 8      # rows of the score board on the completion screen

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
    Touching the flag with the head completes the level and stops the timer; the
    team then types a name and the time goes on the score board (scores.json)."""

    def __init__(self, display, input_source, debug=False):
        self.display = display
        self.canvas = display.canvas            # draw here; display.present() shows it
        self.map = self.terrain = self.flag = self.view = None   # set when a game starts
        self.input = input_source
        self.debug = debug

        # sprite scale: the 500 px character canvas becomes 1/8 of the map height
        self.sprite_scale = config.MAP_HEIGHT * config.CHARACTER_FRACTION / config.SPRITE_CANVAS
        self._sprites = {}          # leg stretch -> CharacterSprites
        self._minimaps = {}         # map name -> MiniMap (the overview under the camera)
        self.minimap = None
        self.character = None
        self.font = pygame.font.SysFont(config.FONT_TEXT, 20, bold=True)
        self.timer_font = pygame.font.SysFont(config.FONT_MONO, 40, bold=True)
        self.clock = pygame.time.Clock()        # measures frame time and limits the FPS
        self.scheme = config.CONTROL_SCHEMES[2]
        self.elapsed = 0.0                      # timer, seconds
        self.finished = False
        self.scores = ScoreBoard()  # all finished runs, saved in scores.json
        self.entering = False       # completion screen: typing the team name
        self.name = ""              # the name being typed (kept for the next run)
        self.saved = None           # the score-board row of this run, once saved
        self.new_best = False
        self.big_font = pygame.font.SysFont(config.FONT_HEAVY, 72, bold=True)
        self.mid_font = pygame.font.SysFont(config.FONT_HEAVY, 34, bold=True)
        self.row_font = pygame.font.SysFont(config.FONT_HEAVY, 28, bold=True)   # score board rows

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
        self.map.reset()
        self.view.snap(self.character.pos)
        self.elapsed = 0.0
        self.finished = False
        self.entering = False
        self.saved = None

    # ------------------------------------------------------------------ loop --
    def run(self, num_players, game_map):
        self.map, self.terrain, self.flag = game_map, game_map.terrain, game_map.flag
        if game_map.name not in self._minimaps:          # one overview per map, kept for next time
            self._minimaps[game_map.name] = MiniMap(game_map)
        self.minimap = self._minimaps[game_map.name]
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
                if self.entering and self.name_key(event, num_players):
                    continue                            # a key used for typing the name
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
                self.map.update(sub)                    # windmill rotor turns
                self.character.update(sub, self.terrain)
            self.view.follow(self.character.pos, dt)
            if not self.finished:
                self.elapsed += dt
                if self.flag.touches(self.character.pos, self.character.head_radius):
                    self.complete(num_players)

            self.draw(players)

    def complete(self, num_players):
        """Flag reached: stop the timer and ask for the team name."""
        self.finished = True
        best = self.scores.best(self.map.name, num_players)
        self.new_best = best is None or self.elapsed < best
        self.entering, self.saved = True, None
        pygame.key.start_text_input()           # deliver typed letters as TEXTINPUT events

    def name_key(self, event, num_players):
        """Typing the team name. True if the event was used for it.
        Enter saves, Esc skips saving; both then show the score board."""
        if event.type == pygame.TEXTINPUT:      # a typed character (works for any keyboard layout)
            text = "".join(ch for ch in event.text if ch.isprintable())
            self.name = (self.name + text)[:NAME_MAX]
            return True
        if event.type != pygame.KEYDOWN:
            return False
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.name.strip():               # no empty names
                self.saved = self.scores.add(self.name, self.map.name, num_players, self.elapsed)
                self.entering = False
        elif event.key == pygame.K_BACKSPACE:
            self.name = self.name[:-1]
        elif event.key == pygame.K_ESCAPE:
            self.entering = False               # don't save, just show the board
        else:
            return event.key not in (pygame.K_F1, pygame.K_F5)   # letters etc. only type
        return True

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
        self.map.draw_movers(self.canvas, offset)               # windmill tower + rotor, in front
        self.draw_leg_owners(offset)
        self.draw_hud(players)
        self.draw_timer()
        if self.finished:
            self.draw_complete()
        self.display.present(self.draw_minimap)

    def draw_minimap(self, surface, rect):
        """Called by the display: the whole map with the character and the visible area."""
        return self.minimap.draw(surface, rect, self.character.pos, self.view.rect)

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
        """The "COMPLETED!" overlay: time, then the name entry or the score board."""
        w, h = self.canvas.get_size()
        shade = pygame.Surface((w, h), pygame.SRCALPHA)   # see-through dark layer
        shade.fill((0, 0, 0, 150))                        # alpha 150 of 255
        self.canvas.blit(shade, (0, 0))
        draw_text(self.canvas, "COMPLETED!", self.big_font, (255, 215, 60), (w // 2, h * 0.12), width=5)
        n = len({p for p, _, _ in self.scheme})
        if self.new_best:
            note = "NEW BEST!"
        else:
            note = f"best  {self.format_time(self.scores.best(self.map.name, n))}"
        draw_text(self.canvas, f"time  {self.format_time(self.elapsed)}     {note}", self.mid_font,
                  (255, 255, 255), (w // 2, h * 0.25))
        if self.entering:
            self.draw_name_entry(w, h)
        else:
            self.draw_board(w, h, n)
            draw_text(self.canvas, "Enter: menu    F5: play again", self.font,
                      (255, 255, 255), (w // 2, h * 0.94), width=2)

    def draw_name_entry(self, w, h):
        draw_text(self.canvas, "Team name for the score board:", self.mid_font,
                  (255, 255, 255), (w // 2, h * 0.43))
        box = pygame.Rect(0, 0, w * 0.42, h * 0.11)
        box.center = (w // 2, h * 0.56)
        pygame.draw.rect(self.canvas, (25, 25, 32), box, border_radius=12)
        pygame.draw.rect(self.canvas, (255, 215, 60), box, 3, border_radius=12)
        cursor = "|" if pygame.time.get_ticks() // 500 % 2 else " "    # blinks once a second
        draw_text(self.canvas, self.name + cursor, self.mid_font, (255, 255, 255), box.center)
        draw_text(self.canvas, "Enter: save    Esc: don't save", self.font,
                  (255, 255, 255), (w // 2, h * 0.70), width=2)

    def draw_board(self, w, h, n):
        """Fastest runs on this map with this many players; this run highlighted."""
        rows = self.scores.ranking(self.map.name, n)
        title = f"BEST TIMES   {self.map.name}, {n} player{'s' if n > 1 else ''}"
        draw_text(self.canvas, title, self.mid_font, (120, 255, 120), (w // 2, h * 0.37))
        if not rows:
            draw_text(self.canvas, "no times saved yet", self.font, (220, 220, 220), (w // 2, h * 0.50))
            return
        shown = list(enumerate(rows[:BOARD_ROWS], 1))      # (place, row)
        if self.saved is not None and self.saved not in rows[:BOARD_ROWS]:
            # this run is further down: show it in the last line with its real place
            shown[-1] = (rows.index(self.saved) + 1, self.saved)
        for i, (place, row) in enumerate(shown):
            y = h * 0.46 + i * h * 0.058
            color = (255, 215, 60) if row is self.saved else (255, 255, 255)
            self._cell(f"{place}.", w * 0.25, y, color, "right")
            self._cell(self._fit(row["name"], w * 0.37), w * 0.27, y, color, "left")
            self._cell(self.format_time(row["time"]), w * 0.73, y, color, "right")
            self._cell(row.get("date", "")[:10], w * 0.76, y, (180, 180, 180), "left")

    def _fit(self, text, width):
        """Shorten text with '...' until it is at most `width` px wide in the row font."""
        if self.row_font.size(text)[0] <= width:
            return text
        while text and self.row_font.size(text + "...")[0] > width:
            text = text[:-1]
        return text + "..."

    def _cell(self, text, x, y, color, align):
        """One table cell: outlined text whose left or right edge is at x."""
        width = self.row_font.size(text)[0]
        cx = x + width / 2 if align == "left" else x - width / 2
        draw_text(self.canvas, text, self.row_font, color, (cx, y), width=2)

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
