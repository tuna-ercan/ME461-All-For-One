"""Draws the camera preview: grey bodies, controlling limbs in the player's colour, mouths only."""
import cv2
import numpy as np
from mediapipe.tasks.python.vision import FaceLandmarksConnections

import config
from player_state import limb_chains

# pairs of COCO keypoints joined by a line (the stick figure)
BODY_EDGES = [(0, 1), (0, 2), (1, 3), (2, 4), (5, 6), (5, 11), (6, 12), (11, 12),
              (5, 7), (7, 9), (6, 8), (8, 10), (11, 13), (13, 15), (12, 14), (14, 16)]
# pairs of face-mesh points that outline the lips (MediaPipe provides this list)
LIPS = [(c.start, c.end) for c in FaceLandmarksConnections.FACE_LANDMARKS_LIPS]
LEG_LABELS = {"upper_left": "top-left", "upper_right": "top-right",
              "lower_left": "bottom-left", "lower_right": "bottom-right"}


class PreviewRenderer:
    backend = ""   # shown next to the FPS, e.g. "TensorRT"

    def draw(self, frame, persons, states, scheme, fps):
        img = frame.copy()                 # never draw on the frame the detectors use
        ok_thr = config.KEYPOINT_THR
        for p in persons:
            ok = p.conf > ok_thr
            pts = p.xy.astype(int)         # OpenCV draws at whole pixels
            grey = config.BODY_COLOR_BGR
            # 1) the whole body in grey
            for i, j in BODY_EDGES:
                if ok[i] and ok[j]:
                    cv2.line(img, tuple(pts[i]), tuple(pts[j]), grey, 2, cv2.LINE_AA)
            for k in np.nonzero(ok)[0]:
                cv2.circle(img, tuple(pts[k]), 3, grey, -1)

            # 2) on top: only the limbs this player controls, thick and coloured
            if p.player is not None:
                col = config.PLAYER_COLORS_BGR[p.player]
                chains = limb_chains(p.xy)
                for player, limb, _ in scheme:
                    if player != p.player:
                        continue
                    a, b, c = chains[limb]
                    for i, j in ((a, b), (b, c)):
                        if ok[i] and ok[j]:
                            cv2.line(img, tuple(pts[i]), tuple(pts[j]), col, 5, cv2.LINE_AA)
                    for k in (a, b, c):
                        if ok[k]:
                            cv2.circle(img, tuple(pts[k]), 5, col, -1)
                head = p.head_center()
                if head is not None:
                    cv2.putText(img, f"P{p.player + 1}", (int(head[0]) - 15, int(head[1]) - 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, col, 2)
            # 3) the mouth outline (the only part of the face mesh that is shown)
            if p.face is not None:
                self._draw_mouth(img, p, states)

        self._draw_hud(img, states, scheme, fps)
        return img

    @staticmethod
    def _draw_mouth(img, p, states):
        face = p.face.astype(int)
        is_open = p.player is not None and states[p.player].mouth_open
        col = (0, 255, 255) if is_open else (255, 255, 255)        # yellow when open (BGR)
        for i, j in LIPS:
            cv2.line(img, tuple(face[i]), tuple(face[j]), col, 2 if is_open else 1, cv2.LINE_AA)

    @staticmethod
    def _draw_hud(img, states, scheme, fps):
        """Text in the top-left corner: FPS and one status line per player."""
        y = 25
        cv2.putText(img, f"{fps:.0f} FPS {PreviewRenderer.backend}", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        for i, st in enumerate(states):
            y += 25
            legs = ", ".join(LEG_LABELS[leg] for pl, _, leg in scheme if pl == i)
            if not st.visible:
                status = "not found"
            else:
                mouth = "OPEN (sticky)" if st.mouth_open else "closed"
                status = f"mouth {mouth}" if st.face_found else "no face"
                if st.sticky_side is not None:
                    status += f" | sticks {st.sticky_side.upper()} (roll {st.head_tilt:+.0f} deg)"
            cv2.putText(img, f"P{i + 1} [{legs}]: {status}", (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, config.PLAYER_COLORS_BGR[i], 2)
