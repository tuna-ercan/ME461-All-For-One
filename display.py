"""The single app window: game screen on the left, camera preview on the right.

    +--------------------------------------------+
    |  +--------------------------+               |
    |  |                          |  +---------+  |
    |  |       game screen        |  | camera  |  |
    |  |                          |  +---------+  |
    |  |                          |               |
    |  +--------------------------+               |
    +--------------------------------------------+

Scenes draw onto `canvas` (map-view sized); present() scales it into the
window. Mouse positions must go through to_canvas() before hit-testing.
F11 (handled in handle_event) switches between window and fullscreen.
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
        self.full_w = cw + config.LAYOUT_CAMERA_WIDTH * cw + 3 * self.margin
        self.full_h = ch + 4 * self.margin
        self.fullscreen = False
        self.cam_surface = None
        self._cam_source = None
        self._set_mode(config.START_FULLSCREEN)
        self.canvas = pygame.Surface(canvas_size).convert()

    # -------------------------------------------------------------- window --
    def _set_mode(self, fullscreen):
        self.fullscreen = fullscreen
        if fullscreen:
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            desk_w, desk_h = pygame.display.get_desktop_sizes()[0]
            s = min(config.WINDOW_SCALE, desk_w * config.LAYOUT_SCREEN_FILL / self.full_w,
                    desk_h * config.LAYOUT_SCREEN_FILL / self.full_h)
            self.window = pygame.display.set_mode((round(self.full_w * s), round(self.full_h * s)))
        self._layout(*self.window.get_size())

    def _layout(self, w, h):
        """Fit the layout into a w x h window, centred (letterboxed in fullscreen)."""
        cw, ch = self.canvas_size
        s = min(w / self.full_w, h / self.full_h)
        self.scale = s
        left = (w - self.full_w * s) / 2
        m = self.margin * s
        self.game_rect = pygame.Rect(round(left + m), 0, round(cw * s), round(ch * s))
        self.game_rect.centery = h // 2
        cam_w = round(config.LAYOUT_CAMERA_WIDTH * cw * s)
        self.cam_rect = pygame.Rect(self.game_rect.right + round(m), 0, cam_w, round(cam_w * 3 / 4))
        self.cam_rect.centery = round(self.game_rect.centery - self.game_rect.h * 0.08)
        self.label_font = pygame.font.SysFont("arial", max(14, cam_w // 22), bold=True)
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
        return ((pos[0] - self.game_rect.x) / self.scale, (pos[1] - self.game_rect.y) / self.scale)

    # ---------------------------------------------------------------- draw --
    def present(self):
        self.window.fill(config.LAYOUT_BG)
        if self.game_rect.size == self.canvas.get_size():
            self.window.blit(self.canvas, self.game_rect)
        else:
            self.window.blit(pygame.transform.smoothscale(self.canvas, self.game_rect.size),
                             self.game_rect)
        pygame.draw.rect(self.window, (0, 0, 0), self.game_rect.inflate(6, 6), 3)
        self._draw_camera()
        pygame.display.flip()

    def _draw_camera(self):
        frame, fresh = self.input.get_preview()
        if frame is not None and (fresh or self._cam_source is not frame):
            self._cam_source = frame
            h, w = frame.shape[:2]
            img = pygame.image.frombuffer(frame.tobytes(), (w, h), "RGB")
            fit = min(self.cam_rect.w / w, self.cam_rect.h / h)
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
