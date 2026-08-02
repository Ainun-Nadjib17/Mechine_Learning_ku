"""
Cyber Frame - ULTRA STABILIZED Version
Menggunakan individual point tracking dan prediction system
"""

import cv2
import numpy as np
import mediapipe as mp
import time
from collections import deque

class PointTracker:
    """Tracker untuk individual point dengan smoothing dan prediction"""
    def __init__(self, smoothing_factor=0.3, max_history=15):
        self.smoothing_factor = smoothing_factor
        self.max_history = max_history
        self.history = deque(maxlen=max_history)
        self.last_position = None
        self.velocity = np.array([0.0, 0.0])
        self.confidence = 0.0
        self.missed_count = 0
        
    def update(self, position, is_detected=True):
        if is_detected and position is not None:
            pos = np.array(position, dtype=np.float32)
            
            # Hitung velocity untuk prediction
            if self.last_position is not None:
                self.velocity = 0.3 * (pos - self.last_position) + 0.7 * self.velocity
            
            # Exponential moving average
            if len(self.history) == 0:
                smoothed = pos
            else:
                last_smooth = self.history[-1] if len(self.history) > 0 else pos
                smoothed = self.smoothing_factor * pos + (1 - self.smoothing_factor) * last_smooth
            
            self.history.append(smoothed)
            self.last_position = pos
            self.confidence = min(1.0, self.confidence + 0.15)
            self.missed_count = 0
            
            return smoothed.astype(np.int32)
        else:
            # Prediction mode - gunakan velocity untuk prediksi
            self.missed_count += 1
            self.confidence = max(0.0, self.confidence - 0.08)
            
            if self.last_position is not None:
                # Prediksi posisi berdasarkan velocity
                predicted = self.last_position + self.velocity * self.missed_count
                self.history.append(predicted)
                return predicted.astype(np.int32)
            return None
    
    def get_position(self):
        if len(self.history) > 0:
            return self.history[-1].astype(np.int32)
        return None
    
    def is_reliable(self):
        return self.confidence > 0.3 and self.missed_count < 20


class CyberFrameApp:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.4,
            min_tracking_confidence=0.4
        )
        self.mp_draw = mp.solutions.drawing_utils

        # 4 point trackers (TL, TR, BR, BL)
        self.trackers = [PointTracker(smoothing_factor=0.25, max_history=15) for _ in range(4)]
        
        # State tracking
        self.frame_count = 0
        self.last_valid_frame = None
        self.stable_count = 0
        self.fps = 0
        self.fps_time = time.time()
        self.frame_count_fps = 0

    def order_points(self, pts):
        """Urutkan 4 titik dengan validasi yang lebih ketat"""
        pts = np.array(pts, dtype=np.float32)
        
        # Sort by x-coordinate
        x_sorted = pts[np.argsort(pts[:, 0])]
        left = x_sorted[:2]
        right = x_sorted[2:]
        
        # Sort left and right by y-coordinate
        left_sorted = left[np.argsort(left[:, 1])]
        right_sorted = right[np.argsort(right[:, 1])]
        
        return np.array([
            left_sorted[0],  # TL
            right_sorted[0], # TR
            right_sorted[1], # BR
            left_sorted[1]   # BL
        ], dtype=np.float32)

    def validate_rectangle(self, pts):
        """Validasi apakah 4 titik membentuk rectangle yang valid"""
        if len(pts) != 4:
            return False, 0
        
        # Hitung area
        area = cv2.contourArea(pts.astype(np.int32))
        if area < 8000:  # Minimum area lebih besar
            return False, area
        
        # Check aspect ratio (jangan terlalu extreme)
        width = max(np.linalg.norm(pts[0] - pts[1]), np.linalg.norm(pts[2] - pts[3]))
        height = max(np.linalg.norm(pts[0] - pts[3]), np.linalg.norm(pts[1] - pts[2]))
        
        if width < 50 or height < 50:
            return False, area
        
        aspect_ratio = width / height if height > 0 else 0
        if aspect_ratio < 0.1 or aspect_ratio > 10:  # Terlalu gepeng
            return False, area
        
        # Check jika titik terlalu berdekatan
        for i in range(4):
            for j in range(i+1, 4):
                dist = np.linalg.norm(pts[i] - pts[j])
                if dist < 30:  # Minimum distance antar titik
                    return False, area
        
        return True, area

    def apply_cyber_effect(self, frame, points):
        pts = self.order_points(points)
        pts_int = pts.astype(np.int32)

        width = int(max(np.linalg.norm(pts[0] - pts[1]), np.linalg.norm(pts[2] - pts[3])))
        height = int(max(np.linalg.norm(pts[0] - pts[3]), np.linalg.norm(pts[1] - pts[2])))

        if width < 30 or height < 30:
            return frame

        dst_pts = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype=np.float32)

        try:
            M = cv2.getPerspectiveTransform(pts, dst_pts)
            warped = cv2.warpPerspective(frame, M, (width, height), borderMode=cv2.BORDER_REPLICATE)

            # EFEK CYBER
            wf = warped.astype(np.float32)
            wf[:, :, 0] = np.clip(wf[:, :, 0] * 2.2, 0, 255)
            wf[:, :, 1] = np.clip(wf[:, :, 1] * 1.5, 0, 255)
            wf[:, :, 2] = np.clip(wf[:, :, 2] * 0.25, 0, 255)
            warped = wf.astype(np.uint8)

            # Scan lines
            for i in range(0, warped.shape[0], 3):
                warped[i:i+2, :] = (warped[i:i+2, :].astype(np.float32) * 0.25).astype(np.uint8)

            # Glitch effect
            for i in range(0, warped.shape[0], 4):
                if np.random.random() > 0.35:
                    shift = np.random.randint(-8, 8)
                    warped[i:i+3] = np.roll(warped[i:i+3], shift, axis=1)

            warped = cv2.convertScaleAbs(warped, alpha=1.6, beta=25)
            warped = cv2.GaussianBlur(warped, (3, 3), 0)

            M_inv = cv2.getPerspectiveTransform(dst_pts, pts)
            warped_back = cv2.warpPerspective(warped, M_inv, (frame.shape[1], frame.shape[0]), borderMode=cv2.BORDER_REPLICATE)

            mask = np.zeros(frame.shape[:2], dtype=np.uint8)
            cv2.fillConvexPoly(mask, pts_int, 255)
            mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

            mask_inv = cv2.bitwise_not(mask_3ch)
            frame_outside = cv2.bitwise_and(frame, mask_inv)
            effect_inside = cv2.bitwise_and(warped_back, mask_3ch)
            result = cv2.add(frame_outside, effect_inside)

            # Draw border dengan opacity
            cv2.polylines(result, [pts_int], True, (0, 255, 255), 3, cv2.LINE_AA)
            cv2.polylines(result, [pts_int], True, (0, 200, 200), 1, cv2.LINE_AA)
            
            for pt in pts_int:
                cv2.circle(result, tuple(pt), 7, (0, 255, 255), -1)
                cv2.circle(result, tuple(pt), 3, (0, 100, 100), -1)

            return result

        except Exception as e:
            print(f"Error apply effect: {e}")
            return frame

    def draw_ui(self, frame, cyber_active, confidence=0):
        h, w = frame.shape[:2]
        pw, ph = 210, 140
        px, py = w - pw - 25, 55

        cv2.rectangle(frame, (px, py), (px + pw, py + ph), (12, 20, 40), -1)
        cv2.rectangle(frame, (px, py), (px + pw, py + ph), (60, 120, 180), 2)
        cv2.putText(frame, "CAMERA MODE / 02", (px + 15, py + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (120, 170, 220), 1, cv2.LINE_AA)
        cv2.putText(frame, "SUBJECT", (px + 15, py + 62), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, "DETECTION", (px + 15, py + 92), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

        if cyber_active:
            status_text = f"HAND FRAME ACTIVE {int(confidence*100)}%"
            status_color = (0, 255, 200) if confidence > 0.6 else (0, 200, 150)
        else:
            status_text = "HAND FRAME WAITING"
            status_color = (100, 150, 200)
        
        cv2.putText(frame, status_text, (px + 15, py + 122), cv2.FONT_HERSHEY_SIMPLEX, 0.38, status_color, 1, cv2.LINE_AA)

        cv2.putText(frame, f"FPS: {self.fps}", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 255, 100), 1, cv2.LINE_AA)

        if cyber_active:
            cv2.putText(frame, "CYBER FRAME AKTIF. EFEK HANYA DI DALAM KOTAK.", (20, h - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 255), 2, cv2.LINE_AA)
        else:
            cv2.putText(frame, "BENTUK KOTAK DENGAN DUA TANGAN.", (20, h - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (100, 180, 255), 1, cv2.LINE_AA)

        # Corner decorations
        cl = 30
        corners = [((10, 10), (1, 1)), ((w - 10, 10), (-1, 1)), ((10, h - 10), (1, -1)), ((w - 10, h - 10), (-1, -1))]
        for (cx, cy), (dx, dy) in corners:
            cv2.line(frame, (cx, cy), (cx + cl * dx, cy), (0, 200, 255), 2)
            cv2.line(frame, (cx, cy), (cx, cy + cl * dy), (0, 200, 255), 2)

        return frame

    def update_fps(self):
        self.frame_count_fps += 1
        elapsed = time.time() - self.fps_time
        if elapsed >= 1.0:
            self.fps = self.frame_count_fps
            self.frame_count_fps = 0
            self.fps_time = time.time()

    def run(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        print("=" * 55)
        print("   CYBER FRAME - ULTRA STABILIZED")
        print("=" * 55)
        print("Tunggu 2-3 detik untuk stabilisasi awal...")
        print("Tekan 'q' untuk keluar, 's' untuk screenshot")
        print("=" * 55)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb)

            corner_points = []
            hands_detected = 0
            hand_landmarks_list = []

            # Deteksi tangan dan sort
            if results.multi_hand_landmarks:
                for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    wrist_x = hand_landmarks.landmark[0].x
                    hand_landmarks_list.append((wrist_x, hand_landmarks))
                
                # Sort dari kiri ke kanan
                hand_landmarks_list.sort(key=lambda x: x[0])
                hands_detected = len(hand_landmarks_list)

            # Ekstrak corner points dari 2 tangan
            current_points = [None, None, None, None]  # TL, TR, BR, BL
            
            if hands_detected == 2:
                for hand_idx, (_, hand_landmarks) in enumerate(hand_landmarks_list):
                    idx = hand_landmarks.landmark[8]  # Telunjuk
                    thb = hand_landmarks.landmark[4]  # Jempol

                    ix, iy = int(idx.x * w), int(idx.y * h)
                    tx, ty = int(thb.x * w), int(thb.y * h)

                    # Validasi jarak
                    dist = np.sqrt((ix - tx)**2 + (iy - ty)**2)
                    
                    if hand_idx == 0:  # Tangan kiri
                        current_points[0] = (ix, iy) if dist > 40 else None  # TL
                        current_points[1] = (tx, ty) if dist > 40 else None  # TR
                    else:  # Tangan kanan
                        current_points[2] = (tx, ty) if dist > 40 else None  # BR
                        current_points[3] = (ix, iy) if dist > 40 else None  # BL

                    # Draw landmarks
                    self.mp_draw.draw_landmarks(
                        frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
                        landmark_drawing_spec=self.mp_draw.DrawingSpec(color=(0, 255, 100), thickness=1, circle_radius=3),
                        connection_drawing_spec=self.mp_draw.DrawingSpec(color=(0, 180, 80), thickness=1)
                    )

            # Update trackers
            for i in range(4):
                self.trackers[i].update(current_points[i], is_detected=(current_points[i] is not None))

            # Get smoothed points dari semua trackers
            smoothed_points = []
            all_reliable = True
            for tracker in self.trackers:
                pos = tracker.get_position()
                if pos is not None and tracker.is_reliable():
                    smoothed_points.append(pos)
                else:
                    all_reliable = False

            cyber_active = False
            confidence = 0.0

            if len(smoothed_points) == 4:
                pts = np.array(smoothed_points, dtype=np.float32)
                is_valid, area = self.validate_rectangle(pts)
                
                if is_valid:
                    # Hitung average confidence
                    confidence = np.mean([t.confidence for t in self.trackers])
                    
                    if confidence > 0.4:  # Threshold confidence
                        frame = self.apply_cyber_effect(frame, pts)
                        cyber_active = True
                        self.stable_count += 1
                        
                        # Draw active text
                        ordered = self.order_points(pts)
                        cv2.putText(frame, "CYBER FRAME // ACTIVE", (int(ordered[0][0]) + 10, int(ordered[0][1]) - 12),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2, cv2.LINE_AA)
                    else:
                        self.stable_count = 0
                else:
                    self.stable_count = 0
            else:
                self.stable_count = 0

            # Butuh minimal 5 frame stabil untuk activate
            if self.stable_count < 5:
                cyber_active = False

            frame = self.draw_ui(frame, cyber_active, confidence if cyber_active else 0)
            self.update_fps()

            cv2.imshow('Cyber Frame - Ultra Stabilized', frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                filename = f"screenshot_{int(time.time())}.png"
                cv2.imwrite(filename, frame)
                print(f"[✓] Screenshot: {filename}")

        cap.release()
        cv2.destroyAllWindows()
        self.hands.close()

if __name__ == '__main__':
    app = CyberFrameApp()
    app.run()