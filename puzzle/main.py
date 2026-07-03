import cv2
import mediapipe as mp
import numpy as np
import pygame
import time
import sys
from PIL import Image
import io

# ============================================================
# KONFIGURASI
# ============================================================
GRID_SIZE = 3
PUZZLE_SIZE = 450  # ukuran puzzle di layar
TILE_SIZE = PUZZLE_SIZE // GRID_SIZE
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
FPS = 30

# Warna
COLOR_BG = (30, 30, 30)
COLOR_TILE_BORDER = (255, 255, 255)
COLOR_SELECTED = (255, 255, 0)
COLOR_HAND = (0, 255, 255)
COLOR_HAND_SKELETON = (255, 165, 0)
COLOR_TEXT = (255, 255, 255)
COLOR_ACCENT = (255, 204, 0)

# ============================================================
# INISIALISASI MEDIAPIPE
# ============================================================
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_face_detection = mp.solutions.face_detection

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

face_detection = mp_face_detection.FaceDetection(
    model_selection=1, min_detection_confidence=0.5
)

# ============================================================
# KELAS PUZZLE
# ============================================================
class LivePuzzle:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("LIVE PUZZLE - Face Puzzle Game")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont('arial', 48, bold=True)
        self.font_medium = pygame.font.SysFont('arial', 28)
        self.font_small = pygame.font.SysFont('arial', 20)
        
        self.state = "capture"  # capture, puzzle, complete
        self.puzzle_pieces = []
        self.puzzle_positions = []
        self.selected_tile = None
        self.grabbed_tile = None
        self.start_time = 0
        self.elapsed_time = 0
        self.captured_face = None
        self.name_input = ""
        self.leaderboard = []
        self.webcam = None
        self.hand_landmarks = None
        self.index_tip = None
        self.is_pinching = False
        self.prev_pinching = False
        
        self.offset_x = (SCREEN_WIDTH - PUZZLE_SIZE) // 2
        self.offset_y = 120
        
    def start_webcam(self):
        self.webcam = cv2.VideoCapture(0)
        if not self.webcam.isOpened():
            print("Error: Tidak bisa membuka webcam!")
            sys.exit(1)
    
    def capture_face(self):
        """Fase 1: Tangkap wajah dari webcam"""
        ret, frame = self.webcam.read()
        if not ret:
            return None
        
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Deteksi wajah
        results = face_detection.process(frame_rgb)
        
        if results.detections:
            # Ambil deteksi wajah terbesar
            best_detection = max(results.detections, 
                               key=lambda d: d.location_data.relative_bounding_box.width * 
                                            d.location_data.relative_bounding_box.height)
            
            bbox = best_detection.location_data.relative_bounding_box
            h, w = frame.shape[:2]
            
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            bw = int(bbox.width * w)
            bh = int(bbox.height * h)
            
            # Tambah padding
            padding = 30
            x = max(0, x - padding)
            y = max(0, y - padding)
            bw = min(w - x, bw + padding * 2)
            bh = min(h - y, bh + padding * 2)
            
            face = frame[y:y+bh, x:x+bw]
            return face, (x, y, bw, bh), frame
        
        return None, None, frame
    
    def create_puzzle(self, face_image):
        """Fase 2: Buat puzzle dari wajah yang ditangkap"""
        # Resize face ke ukuran puzzle
        face_pil = Image.fromarray(cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB))
        face_pil = face_pil.resize((PUZZLE_SIZE, PUZZLE_SIZE), Image.LANCZOS)
        face_array = np.array(face_pil)
        
        # Split menjadi grid
        pieces = []
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                y1 = row * TILE_SIZE
                y2 = y1 + TILE_SIZE
                x1 = col * TILE_SIZE
                x2 = x1 + TILE_SIZE
                piece = face_array[y1:y2, x1:x2]
                pieces.append(piece)
        
        # Simpan urutan yang benar
        self.correct_order = list(range(GRID_SIZE * GRID_SIZE))
        
        # Acak pieces (pastikan tidak sudah solved)
        import random
        shuffled = list(range(GRID_SIZE * GRID_SIZE))
        while shuffled == self.correct_order:
            random.shuffle(shuffled)
        
        self.puzzle_pieces = [pieces[i] for i in shuffled]
        self.current_order = shuffled
        
        # Konversi ke pygame surface
        self.puzzle_surfaces = []
        for piece in self.puzzle_pieces:
            piece_rgb = cv2.cvtColor(piece, cv2.COLOR_BGR2RGB)
            surface = pygame.surfarray.make_surface(piece_rgb.transpose(1, 0, 2))
            self.puzzle_surfaces.append(surface)
    
    def get_tile_at_position(self, pos):
        """Dapatkan index tile pada posisi layar tertentu"""
        x, y = pos
        grid_x = (x - self.offset_x) // TILE_SIZE
        grid_y = (y - self.offset_y) // TILE_SIZE
        
        if 0 <= grid_x < GRID_SIZE and 0 <= grid_y < GRID_SIZE:
            return grid_y * GRID_SIZE + grid_x
        return None
    
    def get_tile_at_hand(self):
        """Dapatkan index tile berdasarkan posisi tangan"""
        if self.index_tip is None:
            return None
        
        # Konversi koordinat hand tracking ke koordinat layar
        # Hand tracking memberikan koordinat normalized (0-1)
        hx = int(self.index_tip.x * SCREEN_WIDTH)
        hy = int(self.index_tip.y * SCREEN_HEIGHT)
        
        return self.get_tile_at_position((hx, hy))
    
    def swap_tiles(self, idx1, idx2):
        """Tukar dua tile"""
        if idx1 is not None and idx2 is not None and idx1 != idx2:
            self.puzzle_surfaces[idx1], self.puzzle_surfaces[idx2] = \
                self.puzzle_surfaces[idx2], self.puzzle_surfaces[idx1]
            self.current_order[idx1], self.current_order[idx2] = \
                self.current_order[idx2], self.current_order[idx1]
    
    def check_complete(self):
        """Cek apakah puzzle sudah selesai"""
        return self.current_order == self.correct_order
    
    def process_hands(self, frame_rgb):
        """Proses hand tracking"""
        results = hands.process(frame_rgb)
        self.hand_landmarks = None
        self.index_tip = None
        self.is_pinching = False
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.hand_landmarks = hand_landmarks
                
                # Index finger tip (landmark 8)
                self.index_tip = hand_landmarks.landmark[8]
                
                # Thumb tip (landmark 4)
                thumb_tip = hand_landmarks.landmark[4]
                
                # Cek pinch gesture (jarak antara thumb dan index)
                distance = np.sqrt(
                    (self.index_tip.x - thumb_tip.x) ** 2 +
                    (self.index_tip.y - thumb_tip.y) ** 2
                )
                self.is_pinching = distance < 0.08
                
                break  # Hanya proses tangan pertama
    
    def draw_hand_overlay(self, frame):
        """Gambar overlay tangan di frame"""
        if self.hand_landmarks:
            # Gambar skeleton tangan
            mp_drawing.draw_landmarks(
                frame,
                self.hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )
        return frame
    
    def draw_capture_screen(self, frame):
        """Gambar layar capture"""
        # Konversi frame ke pygame surface
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_surface = pygame.surfarray.make_surface(frame_rgb.transpose(1, 0, 2))
        
        # Scale frame ke ukuran layar
        frame_surface = pygame.transform.scale(frame_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.screen.blit(frame_surface, (0, 0))
        
        # Overlay gelap
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        
        # Judul
        title = self.font_large.render("LIVE PUZZLE", True, COLOR_ACCENT)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 60))
        self.screen.blit(title, title_rect)
        
        subtitle = self.font_small.render("Posisikan wajah Anda di depan kamera", True, COLOR_TEXT)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 110))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Instruksi
        instr = self.font_medium.render("Tekan SPASI untuk menangkap wajah", True, (255, 255, 255))
        instr_rect = instr.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        self.screen.blit(instr, instr_rect)
        
        # Deteksi wajah indicator
        ret, frame_check = self.webcam.read()
        if ret:
            frame_check = cv2.flip(frame_check, 1)
            frame_rgb = cv2.cvtColor(frame_check, cv2.COLOR_BGR2RGB)
            results = face_detection.process(frame_rgb)
            
            if results.detections:
                indicator = self.font_medium.render("✓ Wajah terdeteksi!", True, (0, 255, 0))
            else:
                indicator = self.font_medium.render("✗ Wajah tidak terdeteksi", True, (255, 100, 100))
            
            ind_rect = indicator.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 130))
            self.screen.blit(indicator, ind_rect)
        
        pygame.display.flip()
    
    def draw_puzzle_screen(self, webcam_frame):
        """Gambar layar puzzle"""
        self.screen.fill(COLOR_BG)
        
        # Tampilkan webcam feed kecil di background
        if webcam_frame is not None:
            frame_rgb = cv2.cvtColor(webcam_frame, cv2.COLOR_BGR2RGB)
            frame_surface = pygame.surfarray.make_surface(frame_rgb.transpose(1, 0, 2))
            frame_surface = pygame.transform.scale(frame_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
            # Buat transparan
            frame_surface.set_alpha(60)
            self.screen.blit(frame_surface, (0, 0))
        
        # Judul
        title = self.font_large.render("LIVE PUZZLE", True, COLOR_ACCENT)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 40))
        self.screen.blit(title, title_rect)
        
        # Timer
        mins = int(self.elapsed_time) // 60
        secs = int(self.elapsed_time) % 60
        timer_text = f"⏱ {mins:02d}:{secs:02d}"
        timer_surface = self.font_medium.render(timer_text, True, COLOR_TEXT)
        timer_rect = timer_surface.get_rect(center=(SCREEN_WIDTH // 2, 90))
        self.screen.blit(timer_surface, timer_rect)
        
        # Gambar puzzle grid
        for idx, surface in enumerate(self.puzzle_surfaces):
            row = idx // GRID_SIZE
            col = idx % GRID_SIZE
            x = self.offset_x + col * TILE_SIZE
            y = self.offset_y + row * TILE_SIZE
            
            # Highlight tile yang di-hover tangan
            if self.grabbed_tile == idx or self.get_tile_at_hand() == idx:
                pygame.draw.rect(self.screen, COLOR_SELECTED, 
                               (x - 3, y - 3, TILE_SIZE + 6, TILE_SIZE + 6), 3)
            
            self.screen.blit(surface, (x, y))
            pygame.draw.rect(self.screen, COLOR_TILE_BORDER, (x, y, TILE_SIZE, TILE_SIZE), 2)
        
        # Gambar hand tracking overlay
        if self.hand_landmarks and webcam_frame is not None:
            h, w = webcam_frame.shape[:2]
            
            # Gambar titik index finger
            if self.index_tip:
                hx = int(self.index_tip.x * SCREEN_WIDTH)
                hy = int(self.index_tip.y * SCREEN_HEIGHT)
                
                # Gambar cursor
                pygame.draw.circle(self.screen, COLOR_HAND, (hx, hy), 12)
                pygame.draw.circle(self.screen, (255, 255, 255), (hx, hy), 5)
                
                # Indikator pinch
                if self.is_pinching:
                    pygame.draw.circle(self.screen, (0, 255, 0), (hx, hy), 20, 3)
            
            # Gambar skeleton tangan sederhana
            if self.hand_landmarks:
                landmarks = self.hand_landmarks.landmark
                connections = [
                    (0,1),(1,2),(2,3),(3,4),  # thumb
                    (0,5),(5,6),(6,7),(7,8),  # index
                    (0,9),(9,10),(10,11),(11,12),  # middle
                    (0,13),(13,14),(14,15),(15,16),  # ring
                    (0,17),(17,18),(18,19),(19,20),  # pinky
                    (5,9),(9,13),(13,17)  # palm
                ]
                
                for conn in connections:
                    p1 = landmarks[conn[0]]
                    p2 = landmarks[conn[1]]
                    x1 = int(p1.x * SCREEN_WIDTH)
                    y1 = int(p1.y * SCREEN_HEIGHT)
                    x2 = int(p2.x * SCREEN_WIDTH)
                    y2 = int(p2.y * SCREEN_HEIGHT)
                    pygame.draw.line(self.screen, COLOR_HAND_SKELETON, (x1, y1), (x2, y2), 2)
                
                # Gambar titik landmark
                for i, landmark in enumerate(landmarks):
                    x = int(landmark.x * SCREEN_WIDTH)
                    y = int(landmark.y * SCREEN_HEIGHT)
                    color = (255, 0, 0) if i == 8 else COLOR_HAND_SKELETON
                    pygame.draw.circle(self.screen, color, (x, y), 4)
        
        # Instruksi
        instr = self.font_small.render("Arahkan jari telunjuk ke tile | Cubit (thumb+index) untuk grab & swap", True, (200, 200, 200))
        instr_rect = instr.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        self.screen.blit(instr, instr_rect)
        
        # Tombol reset
        reset_text = self.font_small.render("[R] Reset Puzzle", True, (255, 100, 100))
        reset_rect = reset_text.get_rect(topleft=(20, SCREEN_HEIGHT - 70))
        self.screen.blit(reset_text, reset_rect)
        
        pygame.display.flip()
    
    def draw_complete_screen(self):
        """Gambar layar selesai"""
        self.screen.fill(COLOR_BG)
        
        # Trophy
        trophy = self.font_large.render("🏆", True, COLOR_ACCENT)
        trophy_rect = trophy.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(trophy, trophy_rect)
        
        # Complete text
        complete = self.font_large.render("COMPLETE!", True, COLOR_ACCENT)
        complete_rect = complete.get_rect(center=(SCREEN_WIDTH // 2, 220))
        self.screen.blit(complete, complete_rect)
        
        # Time
        mins = int(self.elapsed_time) // 60
        secs = int(self.elapsed_time) % 60
        time_text = f"⏱ {mins:02d}:{secs:02d}"
        time_surface = self.font_medium.render(time_text, True, COLOR_TEXT)
        time_rect = time_surface.get_rect(center=(SCREEN_WIDTH // 2, 290))
        self.screen.blit(time_surface, time_rect)
        
        # Name input
        name_label = self.font_small.render("Masukkan nama untuk leaderboard:", True, COLOR_TEXT)
        name_rect = name_label.get_rect(center=(SCREEN_WIDTH // 2, 370))
        self.screen.blit(name_label, name_rect)
        
        # Input box
        input_box = pygame.Rect(SCREEN_WIDTH // 2 - 150, 400, 300, 40)
        pygame.draw.rect(self.screen, (60, 60, 60), input_box)
        pygame.draw.rect(self.screen, COLOR_ACCENT, input_box, 2)
        
        name_surface = self.font_medium.render(self.name_input, True, COLOR_TEXT)
        name_pos_rect = name_surface.get_rect(midleft=(input_box.x + 10, input_box.centery))
        self.screen.blit(name_surface, name_pos_rect)
        
        # Leaderboard
        lb_title = self.font_small.render("Leaderboard:", True, COLOR_TEXT)
        lb_rect = lb_title.get_rect(center=(SCREEN_WIDTH // 2, 480))
        self.screen.blit(lb_title, lb_rect)
        
        for i, entry in enumerate(self.leaderboard[:5]):
            entry_text = f"{i+1}. {entry['name']} - {entry['time']}"
            entry_surface = self.font_small.render(entry_text, True, (200, 200, 200))
            entry_rect = entry_surface.get_rect(center=(SCREEN_WIDTH // 2, 510 + i * 25))
            self.screen.blit(entry_surface, entry_rect)
        
        # Instruksi
        instr = self.font_small.render("[ENTER] Simpan | [R] Main Lagi | [ESC] Keluar", True, (150, 150, 150))
        instr_rect = instr.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        self.screen.blit(instr, instr_rect)
        
        pygame.display.flip()
    
    def reset_puzzle(self):
        """Reset puzzle dengan acak baru"""
        import random
        shuffled = list(range(GRID_SIZE * GRID_SIZE))
        while shuffled == self.correct_order:
            random.shuffle(shuffled)
        
        pieces = []
        face_pil = Image.fromarray(cv2.cvtColor(self.captured_face, cv2.COLOR_BGR2RGB))
        face_pil = face_pil.resize((PUZZLE_SIZE, PUZZLE_SIZE), Image.LANCZOS)
        face_array = np.array(face_pil)
        
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                y1 = row * TILE_SIZE
                y2 = y1 + TILE_SIZE
                x1 = col * TILE_SIZE
                x2 = x1 + TILE_SIZE
                piece = face_array[y1:y2, x1:x2]
                pieces.append(piece)
        
        self.puzzle_pieces = [pieces[i] for i in shuffled]
        self.current_order = shuffled
        
        self.puzzle_surfaces = []
        for piece in self.puzzle_pieces:
            piece_rgb = cv2.cvtColor(piece, cv2.COLOR_BGR2RGB)
            surface = pygame.surfarray.make_surface(piece_rgb.transpose(1, 0, 2))
            self.puzzle_surfaces.append(surface)
        
        self.start_time = time.time()
        self.elapsed_time = 0
        self.grabbed_tile = None
        self.selected_tile = None
    
    def run(self):
        """Main loop"""
        self.start_webcam()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    
                    if self.state == "capture":
                        if event.key == pygame.K_SPACE:
                            face_data = self.capture_face()
                            if face_data[0] is not None:
                                self.captured_face = face_data[0]
                                self.create_puzzle(self.captured_face)
                                self.state = "puzzle"
                                self.start_time = time.time()
                    
                    elif self.state == "puzzle":
                        if event.key == pygame.K_r:
                            self.reset_puzzle()
                    
                    elif self.state == "complete":
                        if event.key == pygame.K_RETURN and self.name_input:
                            mins = int(self.elapsed_time) // 60
                            secs = int(self.elapsed_time) % 60
                            self.leaderboard.append({
                                'name': self.name_input,
                                'time': f"{mins:02d}:{secs:02d}",
                                'seconds': self.elapsed_time
                            })
                            self.leaderboard.sort(key=lambda x: x['seconds'])
                            self.name_input = ""
                        
                        if event.key == pygame.K_r:
                            self.reset_puzzle()
                            self.state = "puzzle"
                        
                        if event.key == pygame.K_BACKSPACE:
                            self.name_input = self.name_input[:-1]
                        elif event.key == pygame.K_SPACE:
                            self.name_input += " "
                        elif len(event.unicode) == 1 and event.unicode.isprintable():
                            self.name_input += event.unicode
            
            # Process webcam frame
            ret, frame = self.webcam.read()
            if ret:
                frame = cv2.flip(frame, 1)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process hands
                self.process_hands(frame_rgb)
                
                # Handle pinch gesture for tile swapping
                if self.state == "puzzle":
                    if self.is_pinching and not self.prev_pinching:
                        # Pinch started - grab tile
                        tile_idx = self.get_tile_at_hand()
                        if tile_idx is not None:
                            self.grabbed_tile = tile_idx
                    
                    elif not self.is_pinching and self.prev_pinching:
                        # Pinch ended - release/swap tile
                        if self.grabbed_tile is not None:
                            target_idx = self.get_tile_at_hand()
                            if target_idx is not None and target_idx != self.grabbed_tile:
                                self.swap_tiles(self.grabbed_tile, target_idx)
                            self.grabbed_tile = None
                    
                    self.prev_pinching = self.is_pinching
                    
                    # Check completion
                    if self.check_complete():
                        self.state = "complete"
                        self.elapsed_time = time.time() - self.start_time
            
            # Draw based on state
            if self.state == "capture":
                self.draw_capture_screen(frame if ret else None)
            
            elif self.state == "puzzle":
                self.elapsed_time = time.time() - self.start_time
                self.draw_puzzle_screen(frame if ret else None)
            
            elif self.state == "complete":
                self.draw_complete_screen()
            
            self.clock.tick(FPS)
        
        # Cleanup
        if self.webcam:
            self.webcam.release()
        hands.close()
        face_detection.close()
        pygame.quit()
        print("Program selesai!")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("  LIVE PUZZLE - Face Puzzle Game")
    print("=" * 50)
    print()
    print("Kontrol:")
    print("  [SPASI]  - Tangkap wajah")
    print("  [Cubit]  - Grab & swap tile (thumb + index finger)")
    print("  [R]      - Reset puzzle")
    print("  [ENTER]  - Simpan nama di leaderboard")
    print("  [ESC]    - Keluar")
    print()
    print("Memulai...")
    
    game = LivePuzzle()
    game.run()