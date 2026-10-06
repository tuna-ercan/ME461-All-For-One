"""Screenshots + recorded physics data for the code guide (run from the project folder)."""
import json
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.getcwd())
import pygame

pygame.display.get_desktop_sizes = lambda: [(1920, 1080)]
import config
from app import App
from game import apply_players
from inputs import InputSource
from minimap import MiniMap
from scoreboard import ScoreBoard
from player_state import LimbPose, PlayerState
from viewport import Viewport, view_size

OUT = sys.argv[1]


class Fake(InputSource):
    def __init__(self):
        self.mouth = set()
        self.poses = {}

    def get_players(self):
        n = self.num_players
        st = [PlayerState(True, mouth_open=(i in self.mouth), face_found=True, mouth_score=0.18 + 0.2 * i)
              for i in range(n)]
        for p, limb, leg in config.CONTROL_SCHEMES[n]:
            st[p].limbs[limb] = self.poses.get(leg, LimbPose(*config.LEGS[leg][2:]))
        if n == 1:
            st[0].sticky_side, st[0].head_tilt = "right", 14.0
        return st


src = Fake()
app = App(src)
d = app.display
win = lambda name: pygame.image.save(d.window, os.path.join(OUT, name))

for page in ("title", "players", "maps"):
    app.menu.players = 2
    app.menu.draw(page)
    d.present()
    win(f"shot_menu_{page}.png")

# options screen, Mouth tab (live scores come from the fake input)
app.options.group = "Mouth"
src.set_num_players(2)
app.options.draw()
d.present()
win("shot_options.png")

g = app.game


def start(map_index, n):
    m = app.maps[map_index]
    g.map, g.terrain, g.flag = m, m.terrain, m.flag
    g.minimap = MiniMap(m)
    g.view = Viewport(m.terrain.width, m.terrain.height, *view_size())
    src.set_num_players(n)
    g.scheme = config.CONTROL_SCHEMES[n]
    g.character = g.build_character(n)
    g.restart()
    return g.character


def step(c, frames):
    for _ in range(frames):
        apply_players(c, g.scheme, src.get_players())
        for _ in range(config.PHYSICS_SUBSTEPS):
            c.update(1 / 180, g.terrain)
        g.view.follow(c.pos, 1 / 60)
        g.elapsed += 1 / 60
        g.clock.tick(config.FPS)        # like the real loop, so the HUD shows a real FPS value


# mountain, 2 players, P2 mouth open (sticky bottom feet)
c = start(0, 2)
step(c, 120)
src.mouth = {1}
step(c, 30)
g.draw(src.get_players())
win("shot_game_mountain.png")
g.debug = True
g.draw(src.get_players())
win("shot_game_debug.png")
g.debug = False
src.mouth = set()

# cave, 3 players
c = start(1, 3)
step(c, 120)
g.draw(src.get_players())
win("shot_game_cave.png")

# windmill map, 2 players, rotor in view
c = start(2, 2)
step(c, 60)
g.map.update(0.35)                          # turn the rotor a little
w = g.map.windmill
c.reset(w.hub + pygame.Vector2(-520, 330))
step(c, 20)
g.view.snap(w.hub + pygame.Vector2(-150, 120))
g.draw(src.get_players())
win("shot_game_windmill.png")

# finish screen: name entry, then the score board (a demo board, not the real scores.json)
demo = os.path.join(OUT, "scores_demo.json")
if os.path.exists(demo):
    os.unlink(demo)
g.scores = ScoreBoard(demo)
for name, t in (("Sheep Squad Forever", 71.2), ("Rock Goats", 79.9), ("ME461 A", 95.35), ("Night Owls", 102.7)):
    g.scores.add(name, "Mountain", 4, t)
c = start(0, 4)
g.elapsed, g.finished, g.new_best = 83.46, True, False
g.entering, g.name, g.saved = True, "MeEeEe", None
g.view.snap(g.flag.rect.center)
c.pos.update(g.flag.rect.centerx - 60, g.flag.rect.top + 60)
g.draw(src.get_players())
win("shot_complete.png")
g.saved = g.scores.add(g.name, "Mountain", 4, g.elapsed)
g.entering = False
g.draw(src.get_players())
win("shot_scores.png")

# 1-player test screen
src.mouth = {0}
src.poses = {"lower_left": LimbPose(100, 40), "lower_right": LimbPose(30, -20)}
t = app.test
src.set_num_players(1)
t.character.reset(t.center)
for _ in range(60):
    apply_players(t.character, t.scheme, src.get_players())
    for leg in t.character.legs.values():
        leg.update_angles(1 / 60)
t.draw(src.get_players()[0])
d.present()
win("shot_test.png")
src.mouth, src.poses = set(), {}

# recorded jump: crouch, then extend the bottom legs fast
c = start(0, 2)
step(c, 150)
src.poses = {"lower_left": LimbPose(80, -120), "lower_right": LimbPose(80, -120)}
step(c, 60)
y_ground = c.pos.y
rec = {"t": [], "height": [], "vy": [], "foot_depth": [], "thigh": []}
src.poses = {"lower_left": LimbPose(10, 0), "lower_right": LimbPose(10, 0)}
L = c.legs["lower_left"]
for f in range(90):
    step(c, 1)
    rec["t"].append(f / 60)
    rec["height"].append(y_ground - c.pos.y)
    rec["vy"].append(-c.vel.y)
    rec["foot_depth"].append(L.foot_radius - g.terrain.distance(*L.foot(c.pos)))
    rec["thigh"].append(L.thigh)
json.dump(rec, open(os.path.join(OUT, "jump.json"), "w"))
print("screens + jump data written")
