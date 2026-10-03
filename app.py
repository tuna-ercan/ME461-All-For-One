"""App: owns the single window and switches between menu, game and test scenes.

A "scene" is a screen with its own loop (menu, game, 1P test). Each scene's
run() keeps drawing frames until the player leaves it, then returns what
should happen next; App.run() is the switchboard between them.
"""
import pygame

import config
from display import Display
from game import Game
from menu import Menu
from maps import load_maps
from test_scene import TestScene
from viewport import view_size


class App:
    def __init__(self, input_source, debug=False):
        pygame.init()                                     # start pygame: video, fonts, events
        pygame.display.set_caption(config.GAME_TITLE)     # window title bar text
        self.input = input_source

        # The window must exist before images can be converted for fast drawing,
        # so Display comes first, then the maps (which load and convert images).
        self.display = Display(view_size(), input_source)
        self.maps = load_maps()
        # Every scene shares the same display (window) and input source.
        self.menu = Menu(self.display, self.maps, input_source)
        self.game = Game(self.display, input_source, debug)
        self.test = TestScene(self.display, input_source)

    def run(self):
        # try/finally: even if the game crashes, the camera thread is stopped and
        # the window is closed properly.
        try:
            while True:
                choice = self.menu.run()        # blocks until the player picks something
                if choice is None:              # Esc / window closed on the title page
                    break
                if choice[0] == "test":
                    scene = self.test.run()
                else:
                    _, players, map_index = choice
                    scene = self.game.run(players, self.maps[map_index])
                if scene == "quit":             # window closed during a scene
                    break
                # otherwise the scene returned "menu": loop back to the menu
        finally:
            self.input.close()
            pygame.quit()
