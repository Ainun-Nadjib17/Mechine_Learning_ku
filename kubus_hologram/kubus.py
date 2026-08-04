import cv2
import time
import math
import os
import urllib.request
import numpy as np

try:
    import mediapipe as mp
    from mediapipe.tasks.python import vision
except ImportError:
    raise SystemExit("Install dulu: pip install mediapipe opencv-python numpy")

# ================= KONFIGURASI =================
CAMERA   = 0
W, H     = 1280, 720
FOCAL    = 900
MIN_SIZE = 35
MAX_SIZE = 240
GRAB_ON  = 0.40    # pinch ratio mulai jepit (makin kecil = makin rapat)
GRAB_OFF = 0.65    # pinch ratio lepasin (hysteresis biar stabil)

MODEL_FILE = "hand_landmarker.task"
MODEL_URL  = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

# ================= GEOMETRI KUBUS =================
VERTS = np.array([
    [-1,-1,-1],[ 1,-1,-1],[ 1, 1,-1],[-1, 1,-1],
    [-1,-1, 1],[ 1,-1, 1],[ 1, 1, 1],[-1, 1, 1],
], dtype=float)
FACES = [(0,1,2,3),(7,6,5,4),(0,4,5,1),(3,2,6,7),(0,3,7,4),(1,5,6,2)]
EDGES = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),
         (0,4),(1,5),(2,6),(3,7)]

def rot_mat(rx, ry, rz):
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    Rx = np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
    Ry = np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])
    Rz = np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    return Rz @ Ry @ Rx

def project(pts3d, cx, cy):
    out = np.empty((len(pts3d), 2), int)
    for i, (x, y, z) in enumerate(pts3d):
        s = FOCAL / (FOCAL + z)
        out[i] = (cx + x*s, cy + y*s)
    return out

class OneEuro:
    """Filter one-euro: halus saat diam, responsif saat gerak cepat."""
    def __init__(self, min_cutoff=1.1, beta=0.03):
        self.min_cutoff, self.beta = min_cutoff, beta
        self.prev = None; self.dprev = None; self.tprev = None
    def reset(self):
        self.prev = None; self.tprev = None
    def __call__(self, x, t):
        if self.prev is None:
            self.prev = x; self.dprev = np.zeros_like(x); self.tprev = t
            return x
        dt = max(t - self.tprev, 1e-3); self.tprev = t
        dx = (x - self.prev) / dt
        ad = 1.0 / (1.0 + 1.0/(2*math.pi*dt))
        dhat = ad*dx + (1-ad)*self.dprev
        cutoff = self.min_cutoff + self.beta*np.abs(dhat)
        a = 1.0 / (1.0 + 1.0/(2*math.pi*cutoff*dt))
        hat = a*x + (1-a)*self.prev
        self.prev = hat; self.dprev = dhat
        return hat

def main():
    if not os.path.exists(MODEL_FILE):
        print("Download model hand landmarker (~7.5 MB)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_FILE)

    options = vision.HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=MODEL_FILE),
        running_mode=vision.RunningMode.IMAGE,
        num_hands=2,
        min_hand_detection_confidence=0.6,
        min_tracking_confidence=0.5,
    )
    landmarker = vision.HandLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(CAMERA)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)

    # state kubus (terpisah dari wireframe!)
    cube_pos  = np.array([W/2, H/2-30], float)
    cube_size = 110.0
    vis = 0.0
    grab_id = -1
    grab_offset = np.zeros(2)
    tilt = np.zeros(2)
    prev_tip = None
    filters = {}
    t0 = time.time(); prev = t0; fps = 30

    print("=== HOLO CUBE v2 ===")
    print("pinch (jempol+telunjuk rapat) = AMBIL kubus, bawa kemana aja")
    print("lepas pinch                   = kubus melayang di situ")
    print("2 tangan renggangkan telunjuk = resize")
    print("q / esc = keluar")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Kamera gak kebaca!"); break
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        now = time.time()

        # ---------- TRACKING + FILTER ----------
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = landmarker.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
        hl = res.hand_landmarks

        infos = []
        if hl:
            for i, lm in enumerate(hl):
                tip_raw = np.array([lm[8].x*w, lm[8].y*h])
                tip = filters.setdefault(i, OneEuro())(tip_raw, now)
                th  = np.array([lm[4].x*w, lm[4].y*h])
                wr  = np.array([lm[0].x*w, lm[0].y*h])
                mcp = np.array([lm[9].x*w, lm[9].y*h])
                ratio = np.linalg.norm(th-tip_raw) / max(np.linalg.norm(wr-mcp), 1)
                infos.append((tip, ratio))
            vis = min(1.0, vis + 0.08)
        else:
            vis = max(0.0, vis - 0.08)
            grab_id = -1
            for f in filters.values(): f.reset()

        # ---------- GRAB (hysteresis biar gak kedip) ----------
        if infos:
            if grab_id == -1:
                for i, (tip, ratio) in enumerate(infos):
                    if ratio < GRAB_ON:
                        grab_id = i
                        grab_offset = cube_pos - tip   # biar kubus gak lompat saat dijepit
                        break
            if grab_id >= 0:
                if grab_id < len(infos):
                    tip, ratio = infos[grab_id]
                    if ratio > GRAB_OFF:
                        grab_id = -1
                    else:
                        target = tip + grab_offset
                        cube_pos += (target - cube_pos) * 0.5   # mau lebih nempel: naikkan ke 0.7
                        vel = (tip - prev_tip) if prev_tip is not None else np.zeros(2)
                        prev_tip = tip.copy()
                        tilt_tgt = np.clip(vel*0.004, -0.35, 0.35)
                        tilt += (tilt_tgt - tilt) * 0.12
                else:
                    grab_id = -1
        if grab_id == -1:
            prev_tip = None
            tilt += (0 - tilt) * 0.06

        # ---------- SCALE pakai 2 tangan ----------
        if len(infos) >= 2:
            d = np.linalg.norm(infos[0][0] - infos[1][0])
            cube_size += (np.clip(d*0.55, MIN_SIZE, MAX_SIZE) - cube_size) * 0.2

        t  = now - t0
        rx = 0.25 + 0.10*math.sin(t*0.5) + tilt[1]   # rotasi pelan = stabil
        ry = t*0.3 + tilt[0]
        rz = 0.05*math.sin(t*0.33)
        draw_pos = cube_pos + np.array([0, 4*math.sin(t*1.6)])  # idle floating halus
        cx, cy = int(draw_pos[0]), int(draw_pos[1])

        # ---------- WIREFRAME AR (DIAM, anchor tengah) ----------
        if vis > 0.02:
            ax, ay = w//2, h//2 - 20
            wire = np.zeros_like(frame)
            for sc, off in [(1.6, 0.0), (1.15, 1.1), (0.8, 2.2)]:
                Rw = rot_mat(0.15*math.sin(t*0.2), t*0.12 + off, 0.05*math.sin(t*0.17))
                wp = project((VERTS * 170 * sc) @ Rw.T, ax, ay)
                for a, b in EDGES:
                    cv2.line(wire, tuple(wp[a]), tuple(wp[b]), (255,255,255), 1)
            for dx, dy, s in [(-1.6,-0.2,24),(1.5,0.15,18),(-0.2,-1.45,14),(0.35,1.4,16)]:
                x, y = int(ax+dx*170), int(ay+dy*170)
                cv2.rectangle(wire, (x-s,y-s), (x+s,y+s), (255,255,255), 1)
            frame = cv2.add(frame, (wire * (0.35*vis)).astype(np.uint8))

            # ---------- KUBUS (bebas gerak) ----------
            p3   = (VERTS * cube_size) @ rot_mat(rx, ry, rz).T
            proj = project(p3, cx, cy)
            hull = cv2.convexHull(proj.reshape(-1,1,2))

            faces = []
            for f in FACES:
                z = p3[list(f), 2].mean()
                n = np.cross(p3[f[1]]-p3[f[0]], p3[f[2]]-p3[f[0]])
                n = n / (np.linalg.norm(n) + 1e-9)
                faces.append((z, f, abs(n[2])))
            faces.sort(key=lambda d: -d[0])

            edge_col = (255,200,80) if grab_id >= 0 else (255,110,30)
            overlay = frame.copy()
            for z, f, nz in faces:
                b = 0.45 + 0.55*nz
                cv2.fillPoly(overlay, [proj[list(f)].reshape(-1,1,2)],
                             (int(255*b), int(205*b), int(150*b)))
            for a, b in EDGES:
                cv2.line(overlay, tuple(proj[a]), tuple(proj[b]), edge_col, 2)
            aw = 0.9 * vis
            frame = cv2.addWeighted(overlay, aw, frame, 1-aw, 0)

            glow = np.zeros_like(frame)
            for z, f, nz in faces:
                cv2.fillPoly(glow, [proj[list(f)].reshape(-1,1,2)], (190,120,60))
            for a, b in EDGES:
                cv2.line(glow, tuple(proj[a]), tuple(proj[b]), (255,150,70), 3)
            glow = cv2.GaussianBlur(glow, (61,61), 0)
            frame = cv2.add(frame, (glow * (0.55*vis)).astype(np.uint8))

            if vis > 0.05:
                amp = int(28*vis)
                noise = np.random.randint(0, amp+1, (h//2, w//2), np.uint8)
                noise = cv2.resize(noise, (w, h), interpolation=cv2.INTER_NEAREST)
                m = np.zeros((h, w), np.uint8)
                cv2.fillConvexPoly(m, hull, 255)
                frame = np.where(m[:,:,None] > 0,
                                 cv2.add(frame, cv2.merge([noise]*3)), frame)

        # ---------- HUD ----------
        cv2.rectangle(frame, (0,0), (w,26), (12,12,15), -1)
        cv2.putText(frame, "/project1/comp4   HOLO-CUBE v2", (8,17),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (210,210,215), 1)
        state = "GRAB!" if grab_id >= 0 else "FLOAT"
        col = (120,255,150) if grab_id >= 0 else (150,180,210)
        cv2.putText(frame, state, (w-80,17), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1)
        cv2.rectangle(frame, (0,h-32), (w,h), (12,12,15), -1)
        el = time.time() - t0
        tc = f"{int(el//3600):02d}:{int(el//60)%60:02d}:{int(el)%60:02d}:{int(el*30)%30:02d}"
        cv2.putText(frame, f"FPS: {fps:5.1f}", (8,h-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (170,170,175), 1)
        cv2.putText(frame, tc, (w//2-75, h-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (90,190,255), 1)
        cv2.putText(frame, "pinch=ambil | 2tangan=scale | q=keluar", (w-330, h-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (170,170,175), 1)

        cv2.imshow("HOLO CUBE", frame)

        now2 = time.time(); fps = fps*0.9 + (1/max(now2-prev, 1e-6))*0.1; prev = now2
        k = cv2.waitKey(1) & 0xFF
        if k in (ord('q'), 27):
            break

    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()

if __name__ == "__main__":
    main()