"""Webcam -> players. YOLO pose for bodies, MediaPipe Face Landmarker for mouths.

Faces are found on the whole frame and given to the body whose head keypoints
are closest in pixels. Players are numbered left -> right on the mirrored image.
Everything runs in a background thread so the game keeps its frame rate.

Per camera frame (VisionInput._loop):
    read frame -> mirror -> YOLO pose (bodies) -> pick/number players
    -> MediaPipe faces -> match faces to bodies -> limb angles, mouth, head tilt
    -> PlayerState per player + annotated preview picture for the game window
"""
import importlib.util
import os
import threading
import time
import urllib.request
from dataclasses import dataclass

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision as mp_vision

import config
from inputs import InputSource
from player_state import L_SH, R_SH, LIMBS, AngleSmoother, PlayerState, limb_poses
from preview import PreviewRenderer


@dataclass
class Person:
    """One body found by the pose model in the current frame."""
    xy: np.ndarray          # (17, 2) keypoints, pixels
    conf: np.ndarray        # (17,)
    box: np.ndarray         # x1, y1, x2, y2
    face: np.ndarray | None = None   # (478, 2) face landmarks, pixels
    player: int | None = None

    # @property: used like a value (p.area), computed when read
    @property
    def area(self):
        """Size of the body's box; bigger = closer to the camera."""
        return float((self.box[2] - self.box[0]) * (self.box[3] - self.box[1]))

    @property
    def center_x(self):
        """Where the person stands left/right: middle of the shoulders (or of the box)."""
        ok = self.conf[[L_SH, R_SH]] > config.KEYPOINT_THR
        if ok.all():
            return float(self.xy[[L_SH, R_SH], 0].mean())
        return float((self.box[0] + self.box[2]) / 2)

    def head_center(self):
        """Average of the visible nose/eye/ear keypoints (0-4), or None."""
        ok = self.conf[:5] > config.KEYPOINT_THR
        return self.xy[:5][ok].mean(axis=0) if ok.any() else None

    def shoulder_width(self):
        """Body size in pixels, used to scale distance limits (far people are small)."""
        if (self.conf[[L_SH, R_SH]] > config.KEYPOINT_THR).all():
            return float(np.linalg.norm(self.xy[L_SH] - self.xy[R_SH]))
        return float(self.box[2] - self.box[0]) / 2

    def head_box(self, shape):
        """Square crop around nose/eyes/ears (fallback face search)."""
        pts = self.xy[:5][self.conf[:5] > config.KEYPOINT_THR]
        if len(pts) < 2:
            return None
        cx, cy = pts.mean(axis=0)
        # span = how spread out the head keypoints are (np.ptp = max - min)
        span = max(np.ptp(pts[:, 0]), np.ptp(pts[:, 1]), config.MIN_CROP / config.CROP_SCALE)
        cy += config.CROP_DOWN * span            # eyes/ears sit above the mouth: shift down
        half = span * config.CROP_SCALE / 2
        h, w = shape[:2]
        # clip the square to the picture borders
        x1, y1 = int(max(cx - half, 0)), int(max(cy - half, 0))
        x2, y2 = int(min(cx + half, w)), int(min(cy + half, h))
        if x2 - x1 < config.MIN_CROP or y2 - y1 < config.MIN_CROP:
            return None
        return x1, y1, x2, y2


class PoseDetector:
    """YOLO pose on the fastest backend available:
    TensorRT engine (GPU) > PyTorch on GPU > PyTorch on CPU."""

    def __init__(self, model_path=config.POSE_MODEL):
        import torch                    # slow imports, only needed in camera mode
        from ultralytics import YOLO

        gpu = torch.cuda.is_available()                        # NVIDIA GPU usable?
        engine = os.path.splitext(model_path)[0] + ".engine"   # yolo26n-pose.engine
        # the engine file alone is not enough: the tensorrt package must be installed too
        trt = importlib.util.find_spec("tensorrt") is not None
        if gpu and trt and config.USE_TENSORRT and model_path.endswith(".pt") and os.path.exists(engine):
            model_path, self.backend = engine, "TensorRT"
        else:
            self.backend = "GPU" if gpu else "CPU"
        self.device = 0 if gpu else "cpu"
        self.model = YOLO(model_path, task="pose")
        print(f"Pose model: {model_path} on {self.backend}")

    def detect(self, frame):
        """All people in the frame as Person objects (keypoints + box)."""
        r = self.model.predict(frame, verbose=False, device=self.device)[0]   # [0] = first (only) image
        if r.keypoints is None or len(r.keypoints) == 0 or r.keypoints.conf is None:
            return []
        # results live on the GPU as torch tensors: .cpu().numpy() makes plain arrays
        xy = r.keypoints.xy.cpu().numpy()
        cf = r.keypoints.conf.cpu().numpy()
        boxes = r.boxes.xyxy.cpu().numpy()
        return [Person(p, c, b) for p, c, b in zip(xy, cf, boxes)]


class FaceDetector:
    """MediaPipe Face Landmarker: 478 points per face (eyes, lips, outline...)."""

    def __init__(self, max_faces):
        if not os.path.exists(config.FACE_MODEL):
            print("Downloading face_landmarker.task ...")
            urllib.request.urlretrieve(config.FACE_URL, config.FACE_MODEL)

        def make(mode, n):
            return mp_vision.FaceLandmarker.create_from_options(mp_vision.FaceLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=config.FACE_MODEL),
                running_mode=mode, num_faces=n))

        # VIDEO mode: for one continuous stream (it reuses the last frame's result
        # to track faces faster). IMAGE mode: every picture is independent, needed
        # for the head crops, which come from different people each time.
        self.full = make(mp_vision.RunningMode.VIDEO, max_faces)
        self.crop = make(mp_vision.RunningMode.IMAGE, 1) if config.FACE_CROP_FALLBACK else None
        self._last_ts = -1

    @staticmethod
    def _mp_image(bgr):
        # OpenCV pictures are BGR, MediaPipe wants RGB in one continuous memory block
        rgb = np.ascontiguousarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        return mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    def detect_full(self, frame):
        """Faces on the whole frame, as (478, 2) arrays of pixel positions."""
        # VIDEO mode needs a timestamp (ms) that always increases
        ts = max(int(time.monotonic() * 1000), self._last_ts + 1)
        self._last_ts = ts
        res = self.full.detect_for_video(self._mp_image(frame), ts)
        h, w = frame.shape[:2]
        # landmarks come as 0..1 fractions of the picture: multiply by its size
        return [np.array([(p.x * w, p.y * h) for p in face]) for face in res.face_landmarks]

    def detect_crop(self, frame, box):
        """Face inside one head crop (fallback for faces too small on the full frame)."""
        if self.crop is None:
            return None
        x1, y1, x2, y2 = box
        crop = frame[y1:y2, x1:x2]
        ch, cw = crop.shape[:2]
        scale = max(1.0, config.UPSCALE_TO / max(ch, cw))
        if scale > 1.0:                          # enlarge tiny crops so the model sees detail
            crop = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
        res = self.crop.detect(self._mp_image(crop))
        if not res.face_landmarks:
            return None
        # crop fractions -> crop pixels -> full-frame pixels (add the crop's corner)
        return np.array([(p.x * cw + x1, p.y * ch + y1) for p in res.face_landmarks[0]])

    def close(self):
        self.full.close()
        if self.crop:
            self.crop.close()


def match_faces(persons, faces):
    """Give each face to the person whose head keypoints are closest (greedy)."""
    # 1) every (person, face) pair that is close enough, with its pixel distance
    pairs = []
    for i, p in enumerate(persons):
        head = p.head_center()
        if head is None:
            continue
        limit = max(config.FACE_MATCH_MIN_PX, config.FACE_MATCH_FACTOR * p.shoulder_width())
        for j, f in enumerate(faces):
            d = float(np.linalg.norm(f.mean(axis=0) - head))   # face centre <-> head centre
            if d < limit:
                pairs.append((d, i, j))
    # 2) closest pairs first; each person and each face is used at most once
    used_p, used_f = set(), set()
    for _, i, j in sorted(pairs):
        if i not in used_p and j not in used_f:
            persons[i].face = faces[j]
            used_p.add(i)
            used_f.add(j)


def assign_players(persons, frame_w, n):
    """Pick the n biggest people and number them left -> right on screen."""
    chosen = sorted(persons, key=lambda p: -p.area)[:n]   # biggest = closest = the players
    chosen.sort(key=lambda p: p.center_x)                  # then order them left to right
    if len(chosen) == n:
        slots = list(range(n))
    else:   # fewer people than players: use the screen region they stand in
        slots, taken = [], set()
        for p in chosen:
            # split the picture into n equal strips; the strip you stand in = your number
            s = min(n - 1, max(0, int(p.center_x / frame_w * n)))
            while s in taken:
                s = (s + 1) % n
            taken.add(s)
            slots.append(s)
    for p, s in zip(chosen, slots):
        p.player = s


def mouth_ratio(pts):
    """Lip gap / mouth width. Face-mesh points 13/14 = middle of the upper/lower
    lip, 61/291 = the mouth corners. Dividing by the width makes the number the
    same whether the face is near (big) or far (small) from the camera."""
    width = np.linalg.norm(pts[61] - pts[291])
    return float(np.linalg.norm(pts[13] - pts[14]) / width) if width else 0.0


class MouthTracker:
    """Smoothed mouth opening with hysteresis, per player slot."""

    def __init__(self):
        self.score, self.open, self.last_seen = 0.0, False, 0.0

    def update(self, pts, now):
        if pts is None:                     # face not found this frame
            if now - self.last_seen > config.MOUTH_TIMEOUT:
                self.open, self.score = False, 0.0
            return                          # short drop-outs keep the last state
        self.last_seen = now
        # smoothed score (EMA): half new measurement, half previous value
        self.score = config.MOUTH_EMA * mouth_ratio(pts) + (1 - config.MOUTH_EMA) * self.score
        # Hysteresis: open above 0.35, closed below 0.25, in between keep the state.
        # One single threshold would flicker open/closed when the score hovers near it.
        if self.open and self.score < config.MOUTH_CLOSE_T:
            self.open = False
        elif not self.open and self.score > config.MOUTH_OPEN_T:
            self.open = True


class HeadTilt:
    """Which side sticks, from the sideways tilt (roll) of the head.

    roll = angle of the line from the screen-left ear to the screen-right ear
    (the eyes are used if an ear is not seen). On the mirrored image the
    screen-right ear is the player's right ear, so roll > 0 means the right
    ear is lower = head tilted to the right. Tilt right -> right side, tilt
    left -> left side (HEAD_TILT_INVERT swaps this). Inside +-HEAD_TILT_ANGLE
    the last side is kept.
    """
    PAIRS = ((3, 4), (1, 2))   # ears, then eyes

    def __init__(self):
        self.side = "right"
        self.roll = 0.0

    def update(self, person):
        ok = person.conf > config.KEYPOINT_THR
        for a, b in self.PAIRS:
            if ok[a] and ok[b]:
                left, right = sorted((person.xy[a], person.xy[b]), key=lambda p: p[0])
                # slope angle of the line left ear -> right ear (0 = level head)
                self.roll = float(np.degrees(np.arctan2(right[1] - left[1], right[0] - left[0])))
                break
        else:                   # for-else: runs when the loop found no usable pair
            return self.side
        tilt_right = self.roll > config.HEAD_TILT_ANGLE
        tilt_left = self.roll < -config.HEAD_TILT_ANGLE
        if tilt_right or tilt_left:
            self.side = "right" if tilt_right != config.HEAD_TILT_INVERT else "left"
        return self.side


class VisionInput(InputSource):
    """Camera input. A background thread does all detection; the game thread only
    picks up the newest results. A lock makes sure the game never reads a result
    while the thread is half-way through replacing it."""

    def __init__(self, source=config.CAMERA_SOURCE, pose_model=config.POSE_MODEL):
        self.pose = PoseDetector(pose_model)
        self.faces = FaceDetector(config.MAX_PLAYERS + 2)
        self.renderer = PreviewRenderer()
        PreviewRenderer.backend = self.pose.backend
        self.cap = cv2.VideoCapture(int(source) if str(source).isdigit() else source)
        if not self.cap.isOpened():
            raise SystemExit(f"Could not open camera/video source {source!r}")

        self._lock = threading.Lock()
        self._preview = None
        self._new_preview = False
        self._reset_players(self.num_players)
        self._wanted_n = self.num_players
        self._running = True
        # daemon thread: does not keep Python alive when the game window closes
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def set_num_players(self, n):
        self._wanted_n = n          # picked up by the worker thread

    def _reset_players(self, n):
        """Fresh per-player trackers for a new player count (and its control scheme)."""
        self.n = n
        self.scheme = config.CONTROL_SCHEMES[n]
        self.smoothers = [{limb: AngleSmoother() for limb in LIMBS} for _ in range(n)]
        self.mouths = [MouthTracker() for _ in range(n)]
        self.tilts = [HeadTilt() for _ in range(n)] if n in config.HEAD_TILT_PLAYERS else None
        with self._lock:
            self._states = [PlayerState() for _ in range(n)]

    # ------------------------------------------------------- worker thread --
    def _loop(self):
        fps, t_prev = 0.0, time.time()
        while self._running:
            if self._wanted_n != self.n:
                self._reset_players(self._wanted_n)
            ok, frame = self.cap.read()
            if not ok:
                time.sleep(0.01)
                continue
            if config.MIRROR_CAMERA:
                frame = cv2.flip(frame, 1)       # 1 = flip left/right, like a mirror
            states, persons = self._process(frame)
            now = time.time()
            fps = 0.9 * fps + 0.1 / max(now - t_prev, 1e-6)   # smoothed frames per second
            t_prev = now
            preview = cv2.cvtColor(self.renderer.draw(frame, persons, states, self.scheme, fps),
                                   cv2.COLOR_BGR2RGB)
            with self._lock:
                self._states, self._preview, self._new_preview = states, preview, True

    def _process(self, frame):
        """One camera frame -> one PlayerState per player slot."""
        now = time.time()
        persons = self.pose.detect(frame)                       # bodies
        assign_players(persons, frame.shape[1], self.n)         # who is P1, P2, ...
        match_faces(persons, self.faces.detect_full(frame))     # faces -> bodies

        states = [PlayerState() for _ in range(self.n)]
        by_slot = {p.player: p for p in persons if p.player is not None}
        for slot in range(self.n):
            p = by_slot.get(slot)
            st = states[slot]
            if p is not None:
                if p.face is None:                    # retry on a head crop
                    box = p.head_box(frame.shape)
                    if box is not None:
                        p.face = self.faces.detect_crop(frame, box)
                poses = limb_poses(p.xy, p.conf)
                st.visible = True
                for limb, smoother in self.smoothers[slot].items():
                    value = smoother.update(poses.get(limb))
                    if value is not None:
                        st.limbs[limb] = value
                st.face_found = p.face is not None
            if self.tilts is not None:
                tilt = self.tilts[slot]
                st.sticky_side = tilt.update(p) if p is not None else tilt.side
                st.head_tilt = tilt.roll
            mouth = self.mouths[slot]
            mouth.update(p.face if p is not None else None, now)
            st.mouth_open, st.mouth_score = mouth.open, mouth.score
        return states, persons

    # ---------------------------------------------------------- main thread --
    def get_players(self):
        with self._lock:                    # wait if the thread is writing right now
            return list(self._states)

    def get_preview(self):
        """Newest annotated camera frame (RGB numpy array) and whether it is new."""
        with self._lock:
            frame, fresh = self._preview, self._new_preview
            self._new_preview = False
        return frame, fresh

    def close(self):
        self._running = False
        self._thread.join(timeout=2)
        self.cap.release()
        self.faces.close()
