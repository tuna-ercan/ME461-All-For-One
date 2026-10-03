"""App: owns the single window and switches between menu, game and test scenes."""
import pygame

import config
from display import Display
from game import Game
from menu import Menu
from terrain import Terrain
from test_scene import TestScene
from viewport import Viewport


class App:
    def __init__(self, input_source, debug=False):
        pygame.init()
        pygame.display.set_caption(config.GAME_TITLE)
        self.input = input_source

        bg = pygame.image.load(config.asset("background.png"))
        fg = pygame.image.load(config.asset("foreground.png"))
        view = Viewport(*fg.get_size())
        self.display = Display((view.w, view.h), input_source)

        self.terrain = Terrain(bg.convert_alpha(), fg.convert_alpha())
        self.menu = Menu(self.display, self.terrain, input_source)
        self.game = Game(self.display, self.terrain, input_source, debug)
        self.test = TestScene(self.display, input_source)

    def run(self):
        try:
            while True:
                choice = self.menu.run()
                if choice is None:
                    break
                mode, players = choice
                scene = self.test.run() if mode == "test" else self.game.run(players)
                if scene == "quit":
                    break
        finally:
            self.input.close()
            pygame.quit()
