"""The single app window: game screen on the left, camera preview on the right.

    +--------------------------------------------+
    |  +--------------------------+               |
    |  |                          |  +---------+  |
    |  |       game screen        |  | camera  |  |
    |  |                          |  +---------+  |
    |  |                          |  +---------+  |
    |  |                          |  |   map   |  |
    |  +--------------------------+  +---------+  |
    +--------------------------------------------+

Scenes draw onto `canvas` (map-view sized); present() scales it into the
window. Mouse positions must go through to_canvas() before hit-testing.
F11 (handled in handle_event) switches between window and fullscreen.

Why a canvas: scenes always draw at the same size (1365 x 721) no matter how
big the window is; only present() deals with the real window size.
"""
import pygame

import config
from ui import draw_text


class Display:
    def __init__(self, canvas_size, input_source):
        self.input = input_source
        self.canvas_size = canvas_size
        cw, ch = canvas_size
        # whole layout at canvas scale (1 unit = 1 canvas px)
        self.margin = config.LAYOUT_MARGIN * cw
        self.full_w = cw + config.LAYOUT_CAMERA_WIDTH * cw + 3 * self.margin   # game + camera + 3 gaps
        self.full_h = ch + 4 * self.margin
        self.fullscreen = False
        self.cam_surface = None        # last camera picture, already scaled for the panel
        self._cam_source = None        # the frame cam_surface was made from
        self._set_mode(config.START_FULLSCREEN)
        self.canvas = pygame.Surface(canvas_size).convert()

    # -------------------------------------------------------------- window --
    def _set_mode(self, fullscreen):
        """Create (or re-create) the window, then work out where things go in it."""
        self.fullscreen = fullscreen
        if fullscreen:
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)   # (0, 0) = screen size
        else:
            # biggest scale that fits LAYOUT_SCREEN_FILL of the desktop (and WINDOW_SCALE)
            desk_w, desk_h = pygame.display.get_desktop_sizes()[0]
            s = min(config.WINDOW_SCALE, desk_w * config.LAYOUT_SCREEN_FILL / self.full_w,
                    desk_h * config.LAYOUT_SCREEN_FILL / self.full_h)
            self.window = pygame.display.set_mode((round(self.full_w * s), round(self.full_h * s)))
        self._layout(*self.window.get_size())

    def _layout(self, w, h):
        """Fit the layout into a w x h window, centred (letterboxed in fullscreen)."""
        cw, ch = self.canvas_size
        s = min(w / self.full_w, h / self.full_h)    # scale that fits both width and height
        self.scale = s
        left = (w - self.full_w * s) / 2             # empty space on each side, if any
        m = self.margin * s
        self.game_rect = pygame.Rect(round(left + m), 0, round(cw * s), round(ch * s))
        self.game_rect.centery = h // 2
        cam_w = round(config.LAYOUT_CAMERA_WIDTH * cw * s)
        self.label_font = pygame.font.SysFont(config.FONT_TEXT, max(14, cam_w // 22), bold=True)
        label = self.label_font.get_linesize() + 6           # room for a "CAMERA" / "MAP" title
        # right column, top-aligned with the game: camera (4:3 like a webcam picture),
        # then the map overview using the rest of the height
        x = self.game_rect.right + round(m)
        self.cam_rect = pygame.Rect(x, self.game_rect.top + label, cam_w, round(cam_w * 3 / 4))
        map_top = self.cam_rect.bottom + round(m) + label
        self.map_rect = pygame.Rect(x, map_top, cam_w, max(20, self.game_rect.bottom - map_top))
        self._cam_source = None   # rescale the camera image for the new size

    def toggle_fullscreen(self):
        self._set_mode(not self.fullscreen)

    def handle_event(self, event):
        """Window-level keys shared by every scene. True if the event was used."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self.toggle_fullscreen()
            return True
        return False

    def to_canvas(self, pos):
        """Window pixel -> canvas pixel (for mouse clicks)."""
        # undo what present() did: subtract the game panel's corner, divide by the scale
        return ((pos[0] - self.game_rect.x) / self.scale, (pos[1] - self.game_rect.y) / self.scale)

    # ---------------------------------------------------------------- draw --
    def present(self, minimap=None):
        """Put the finished canvas, the camera picture and the map overview in the
        window and show it. minimap(surface, rect) draws the map (the game passes
        one); without it the map panel shows a short note."""
        self.window.fill(config.LAYOUT_BG)
        if self.game_rect.size == self.canvas.get_size():
            self.window.blit(self.canvas, self.game_rect)          # same size: plain copy (fast)
        else:
            self.window.blit(pygame.transform.smoothscale(self.canvas, self.game_rect.size),
                             self.game_rect)
        pygame.draw.rect(self.window, (0, 0, 0), self.game_rect.inflate(6, 6), 3)   # black frame
        self._draw_camera()
        self._draw_map(minimap)
        # Everything above was drawn into a hidden buffer; flip() shows it all at
        # once, so the player never sees a half-drawn frame.
        pygame.display.flip()

    def _draw_camera(self):
        frame, fresh = self.input.get_preview()
        # convert numpy -> pygame image only when a NEW camera frame arrived
        # (the camera runs slower than the game; re-converting each frame is waste)
        if frame is not None and (fresh or self._cam_source is not frame):
            self._cam_source = frame
            h, w = frame.shape[:2]
            img = pygame.image.frombuffer(frame.tobytes(), (w, h), "RGB")
            fit = min(self.cam_rect.w / w, self.cam_rect.h / h)    # fit inside the panel, keep shape
            self.cam_surface = pygame.transform.smoothscale(img, (round(w * fit), round(h * fit)))
        if self.cam_surface is not None and self._cam_source is not None:
            rect = self.cam_surface.get_rect(center=self.cam_rect.center)
            self.window.blit(self.cam_surface, rect)
        else:
            rect = self.cam_rect
            pygame.draw.rect(self.window, (20, 20, 24), rect)
            draw_text(self.window, "no camera (keyboard mode)", self.label_font,
                      (200, 200, 200), rect.center, width=1)
        pygame.draw.rect(self.window, (0, 0, 0), rect.inflate(6, 6), 3)
        draw_text(self.window, "CAMERA", self.label_font, (230, 230, 230),
                  (rect.centerx, rect.top - self.label_font.get_linesize()), width=1)

    def _draw_map(self, minimap):
        """The whole-map overview under the camera (only filled in during a game)."""
        if minimap is not None:
            rect = minimap(self.window, self.map_rect)
        else:
            rect = self.map_rect
            pygame.draw.rect(self.window, (20, 20, 24), rect)
            draw_text(self.window, "the whole map is shown here during the game", self.label_font,
                      (150, 150, 150), rect.center, width=1)
        pygame.draw.rect(self.window, (0, 0, 0), rect.inflate(6, 6), 3)
        draw_text(self.window, "MAP", self.label_font, (230, 230, 230),
                  (rect.centerx, rect.top - self.label_font.get_linesize()), width=1)
