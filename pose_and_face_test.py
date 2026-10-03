"""
Pose + face mesh test.

Pipeline per frame:
  1. YOLO pose (+ tracking)          -> 17 body keypoints and an ID per person
  2. Head crop from keypoints 0-4    -> nose, eyes, ears tell us where the face is
  3. MediaPipe Face Landmarker       -> 478 landmarks on the crop only
  4. Map landmarks back to the frame -> draw mesh on top of the skeleton
  5. Mouth ratio + jawOpen, smoothed per person ID -> OPEN / closed label

Keys:  m = face view (mesh / contours / points / off)   k = keypoint indices
       a = joint angles     + / - = keypoint confidence threshold     q = quit

Usage: python pose_face_test.py                       # webcam 0
       python pose_face_test.py --source video.mp4
       python pose_face_test.py --source photo.jpg
       python pose_face_test.py --max-faces 2          # mesh only the 2 biggest people

Install: pip install ultralytics mediapipe opencv-python
Checked against ultralytics 8.4.170 and mediapipe 0.10.33.
"""
import argparse
import os
import time
import urllib.request

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions
from ultralytics import YOLO

# ---------------------------------------------------------------- settings --
FACE_MODEL = "face_landmarker.task"
FACE_URL = ("https://storage.googleapis.com/mediapipe-models/face_landmarker/"
            "face_landmarker/float16/1/face_landmarker.task")
CROP_SCALE = 2.4      # head box = span of head keypoints * this (guess, tune it)
CROP_DOWN = 0.25      # shift crop down (in spans) so the chin is included (guess)
MIN_CROP = 24         # px; smaller heads are skipped, the mesh would be unreliable
UPSCALE_TO = 256      # small crops are enlarged to this size before the face model
OPEN_T, CLOSE_T = 0.35, 0.25   # mouth hysteresis thresholds (guesses, calibrate!)
EMA = 0.5             # smoothing for the mouth score

# ------------------------------------------------------------- pose layout --
SKELETON = [
    ((0, 1), "head"), ((0, 2), "head"), ((1, 3), "head"), ((2, 4), "head"),
    ((5, 6), "torso"), ((5, 11), "torso"), ((6, 12), "torso"), ((11, 12), "torso"),
    ((5, 7), "left"), ((7, 9), "left"), ((11, 13), "left"), ((13, 15), "left"),
    ((6, 8), "right"), ((8, 10), "right"), ((12, 14), "right"), ((14, 16), "right"),
]
COLORS = {"head": (255, 200, 80), "torso": (200, 200, 200),
          "left": (80, 255, 80), "right": (80, 80, 255)}  # BGR
ANGLES = {"L elbow": (5, 7, 9), "R elbow": (6, 8, 10),
          "L knee": (11, 13, 15), "R knee": (12, 14, 16)}

# ------------------------------------------------------------- face layout --
C = vision.FaceLandmarksConnections
CONTOURS = [
    (C.FACE_LANDMARKS_FACE_OVAL, (200, 200, 200)), (C.FACE_LANDMARKS_LIPS, (80, 80, 255)),
    (C.FACE_LANDMARKS_LEFT_EYE, (80, 255, 80)), (C.FACE_LANDMARKS_RIGHT_EYE, (80, 255, 80)),
    (C.FACE_LANDMARKS_LEFT_EYEBROW, (255, 200, 80)), (C.FACE_LANDMARKS_RIGHT_EYEBROW, (255, 200, 80)),
    (C.FACE_LANDMARKS_LEFT_IRIS, (255, 255, 0)), (C.FACE_LANDMARKS_RIGHT_IRIS, (255, 255, 0)),
]
FACE_VIEWS = ["mesh", "contours", "points", "off"]


# ================================================================== helpers ==
def load_face_landmarker():
    if not os.path.exists(FACE_MODEL):
        print("Downloading face_landmarker.task ...")
        try:
            urllib.request.urlretrieve(FACE_URL, FACE_MODEL)
        except Exception as e:
            raise SystemExit(f"Download failed ({e}). Get it from the MediaPipe "
                             "Face Landmarker page and put it next to this script.")
    # IMAGE mode: each crop is handled independently. VIDEO mode expects ONE
    # continuous stream, but here we feed crops of different people each frame.
    return vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=FACE_MODEL),
        running_mode=vision.RunningMode.IMAGE,
        num_faces=1,
        output_face_blendshapes=True,
    ))


def angle_at(a, b, c):
    v1, v2 = a - b, c - b
    cos = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
    return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))


def head_box(xy, conf, thr, shape):
    """Square box around the face, built from nose/eyes/ears. None if unreliable."""
    pts = xy[:5][conf[:5] > thr]
    if len(pts) < 2:
        return None
    cx, cy = pts.mean(axis=0)
    span = max(np.ptp(pts[:, 0]), np.ptp(pts[:, 1]))
    span = max(span, MIN_CROP / CROP_SCALE)
    cy += CROP_DOWN * span
    half = span * CROP_SCALE / 2
    h, w = shape[:2]
    x1, y1 = int(max(cx - half, 0)), int(max(cy - half, 0))
    x2, y2 = int(min(cx + half, w)), int(min(cy + half, h))
    if x2 - x1 < MIN_CROP or y2 - y1 < MIN_CROP:
        return None
    return x1, y1, x2, y2


def run_face(landmarker, frame, box):
    """Face mesh on one crop. Returns (478x2 pixel points in FRAME coords, blendshapes)."""
    x1, y1, x2, y2 = box
    crop = frame[y1:y2, x1:x2]
    ch, cw = crop.shape[:2]
    scale = max(1.0, UPSCALE_TO / max(ch, cw))
    if scale > 1.0:
        crop = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    rgb = np.ascontiguousarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
    res = landmarker.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
    if not res.face_landmarks:
        return None, None
    # normalized (0..1 of the crop) -> crop pixels -> frame pixels
    pts = np.array([(p.x * cw + x1, p.y * ch + y1) for p in res.face_landmarks[0]])
    bs = {b.category_name: b.score for b in res.face_blendshapes[0]}
    return pts, bs


def mouth_ratio(pts):
    width = np.linalg.norm(pts[61] - pts[291])
    return float(np.linalg.norm(pts[13] - pts[14]) / width) if width else 0.0


# ================================================================ drawing ==
def draw_skeleton(img, xy, conf, thr, show_idx, show_ang):
    ok = conf > thr
    for (i, j), part in SKELETON:
        if ok[i] and ok[j]:
            cv2.line(img, tuple(xy[i].astype(int)), tuple(xy[j].astype(int)),
                     COLORS[part], 2, cv2.LINE_AA)
    for k, (x, y) in enumerate(xy):
        if ok[k]:
            g = int(255 * min(1.0, conf[k]))
            cv2.circle(img, (int(x), int(y)), 4, (0, g, 255 - g), -1)
            if show_idx:
                cv2.putText(img, str(k), (int(x) + 5, int(y) - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    if show_ang:
        for a, b, c in ANGLES.values():
            if ok[a] and ok[b] and ok[c]:
                cv2.putText(img, f"{angle_at(xy[a], xy[b], xy[c]):.0f}",
                            (int(xy[b][0]) + 8, int(xy[b][1]) + 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)


def draw_face(img, pts, view):
    p = pts.astype(np.int32)
    if view == "mesh":
        for c in C.FACE_LANDMARKS_TESSELATION:
            cv2.line(img, tuple(p[c.start]), tuple(p[c.end]), (110, 110, 110), 1, cv2.LINE_AA)
    if view in ("mesh", "contours"):
        for conns, color in CONTOURS:
            for c in conns:
                cv2.line(img, tuple(p[c.start]), tuple(p[c.end]), color, 1, cv2.LINE_AA)
    if view == "points":
        for x, y in p:
            cv2.circle(img, (int(x), int(y)), 1, (0, 255, 255), -1)


# ============================================================== per frame ==
def process(model, landmarker, frame, st, track=True):
    """st = settings/state dict. Returns (people, faces_meshed)."""
    r = (model.track(frame, persist=True, verbose=False) if track
         else model.predict(frame, verbose=False))[0]
    if r.keypoints is None or len(r.keypoints) == 0:
        return 0, 0
    xy = r.keypoints.xy.cpu().numpy()
    cf = r.keypoints.conf.cpu().numpy()
    ids = r.boxes.id.int().cpu().tolist() if r.boxes.id is not None else [None] * len(xy)
    areas = (r.boxes.xywh[:, 2] * r.boxes.xywh[:, 3]).cpu().numpy()

    # only mesh the N largest people (face model cost grows per person)
    face_people = set(np.argsort(-areas)[:st["max_faces"]].tolist())
    meshed = 0

    for i, (p_xy, p_cf, tid) in enumerate(zip(xy, cf, ids)):
        draw_skeleton(frame, p_xy, p_cf, st["thr"], st["show_idx"], st["show_ang"])
        label = f"ID {tid}" if tid is not None else f"#{i}"

        if st["view"] != "off" and i in face_people:
            box = head_box(p_xy, p_cf, st["thr"], frame.shape)
            if box is not None:
                pts, bs = run_face(landmarker, frame, box)
                if pts is not None:
                    meshed += 1
                    draw_face(frame, pts, st["view"])
                    key = tid if tid is not None else f"img{i}"
                    m = st["mouth"].setdefault(key, {"score": 0.0, "open": False})
                    m["score"] = EMA * mouth_ratio(pts) + (1 - EMA) * m["score"]
                    if m["open"] and m["score"] < CLOSE_T:
                        m["open"] = False
                    elif not m["open"] and m["score"] > OPEN_T:
                        m["open"] = True
                    label += (f" | mouth {'OPEN' if m['open'] else 'closed'}"
                              f" {m['score']:.2f} | jaw {bs.get('jawOpen', 0):.2f}")
                if st["show_box"]:
                    cv2.rectangle(frame, box[:2], box[2:], (255, 0, 255), 1)

        ok = p_cf[:5] > st["thr"]
        if ok.any():
            head = p_xy[:5][ok].mean(axis=0).astype(int)
            cv2.putText(frame, label, (head[0] - 40, max(15, head[1] - 45)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
    return len(xy), meshed


# ==================================================================== main ==
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="0", help="0 = webcam, or path to video/image")
    ap.add_argument("--model", default="yolo26n-pose.pt")
    ap.add_argument("--max-faces", type=int, default=3)
    ap.add_argument("--show-box", action="store_true", help="draw the head crop box")
    args = ap.parse_args()

    model = YOLO(args.model)
    landmarker = load_face_landmarker()
    st = {"thr": 0.5, "show_idx": False, "show_ang": False, "view": "mesh",
          "max_faces": args.max_faces, "show_box": args.show_box, "mouth": {}}

    if args.source.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".webp")):
        img = cv2.imread(args.source)
        n, meshed = process(model, landmarker, img, st, track=False)
        print(f"people: {n}, faces meshed: {meshed}")
        cv2.imshow("pose + face", img)
        cv2.waitKey(0)
        return

    cap = cv2.VideoCapture(int(args.source) if args.source.isdigit() else args.source)
    t_prev, fps = time.time(), 0.0
    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break
        n, meshed = process(model, landmarker, frame, st)

        now = time.time()
        fps = 0.9 * fps + 0.1 * (1 / max(now - t_prev, 1e-6))
        t_prev = now
        hud = (f"{fps:.0f} FPS | people {n} | faces {meshed} | face: {st['view']} | "
               f"thr {st['thr']:.2f} | m k a +/- q")
        cv2.putText(frame, hud, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

        cv2.imshow("pose + face", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("m"):
            st["view"] = FACE_VIEWS[(FACE_VIEWS.index(st["view"]) + 1) % len(FACE_VIEWS)]
        elif key == ord("k"):
            st["show_idx"] = not st["show_idx"]
        elif key == ord("a"):
            st["show_ang"] = not st["show_ang"]
        elif key in (ord("+"), ord("=")):
            st["thr"] = min(0.95, st["thr"] + 0.05)
        elif key == ord("-"):
            st["thr"] = max(0.05, st["thr"] - 0.05)
    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()


if __name__ == "__main__":
    main()