"""App: owns the single window and switches between menu, game and test scenes."""
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
        pygame.init()
        pygame.display.set_caption(config.GAME_TITLE)
        self.input = input_source

        self.display = Display(view_size(), input_source)
        self.maps = load_maps()
        self.menu = Menu(self.display, self.maps, input_source)
        self.game = Game(self.display, input_source, debug)
        self.test = TestScene(self.display, input_source)

    def run(self):
        try:
            while True:
                choice = self.menu.run()
                if choice is None:
                    break
                if choice[0] == "test":
                    scene = self.test.run()
                else:
                    _, players, map_index = choice
                    scene = self.game.run(players, self.maps[map_index])
                if scene == "quit":
                    break
        finally:
            self.input.close()
            pygame.quit()
