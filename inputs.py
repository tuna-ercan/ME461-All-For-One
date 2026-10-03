"""Input sources. The game only talks to InputSource, so camera and keyboard are swappable."""
import time

import pygame

import config
from player_state import LimbPose, PlayerState


class InputSource:
    """The interface every input must offer. Subclasses override these methods;
    the game calls them without knowing whether a camera or a keyboard is behind."""
    num_players = 1

    def set_num_players(self, n):
        self.num_players = n

    def get_players(self):
        """List of PlayerState, one per player slot."""
        raise NotImplementedError     # a subclass must provide this

    def get_preview(self):
        """(RGB numpy frame or None, is_new) for the camera panel."""
        return None, False

    def close(self):
        pass


class KeyboardInput(InputSource):
    """Debug controls without a camera. Keys move a character leg directly; the
    pose is handed to whichever player/limb drives that leg in the current scheme.

    top-left    Q/A thigh, W/S knee      top-right    E/D thigh, R/F knee
    bottom-left U/J thigh, I/K knee      bottom-right O/L thigh, P/; knee
    hold 1-4 = that player's mouth open (sticky)
    """
    SPEED = 240.0   # deg/s
    KEYS = {  # leg -> (thigh +, thigh -, bend +, bend -)
        "upper_left": (pygame.K_q, pygame.K_a, pygame.K_w, pygame.K_s),
        "upper_right": (pygame.K_e, pygame.K_d, pygame.K_r, pygame.K_f),
        "lower_left": (pygame.K_u, pygame.K_j, pygame.K_i, pygame.K_k),
        "lower_right": (pygame.K_o, pygame.K_l, pygame.K_p, pygame.K_SEMICOLON),
    }
    MOUTH_KEYS = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]

    def __init__(self):
        self.poses = {leg: LimbPose(*config.LEGS[leg][2:]) for leg in self.KEYS}   # start at rest pose
        self._t = time.time()

    def get_players(self):
        now = time.time()
        step = self.SPEED * min(now - self._t, 0.1)     # degrees to turn since last call
        self._t = now
        keys = pygame.key.get_pressed()                 # which keys are held right now
        for leg, (tp, tm, bp, bm) in self.KEYS.items():
            pose = self.poses[leg]
            # True/False count as 1/0: (plus held) - (minus held) = +1, -1 or 0
            pose.thigh += step * (keys[tp] - keys[tm])
            pose.bend += step * (keys[bp] - keys[bm])

        states = [PlayerState(visible=True, face_found=True, mouth_open=bool(keys[self.MOUTH_KEYS[i]]))
                  for i in range(self.num_players)]
        # hand each leg's pose to the player/limb that controls that leg
        for player, limb, leg in config.CONTROL_SCHEMES[self.num_players]:
            states[player].limbs[limb] = self.poses[leg]
        return states
