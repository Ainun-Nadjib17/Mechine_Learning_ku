import pygame
import math
import random
import sys
import os

# Inisialisasi Pygame
pygame.init()
screen = pygame.display.set_mode((1000, 700))
pygame.display.set_caption("Shape of My Heart")
clock = pygame.time.Clock()

# Musik latar: love.mpeg
MUSIC_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "love.mpeg")
try:
    pygame.mixer.music.load(MUSIC_FILE)
    pygame.mixer.music.set_volume(0.7)
    pygame.mixer.music.play(-1)  # loop terus
except pygame.error as e:
    print(f"Musik tidak dapat diputar: {e}")

# Warna
BLACK = (0, 0, 0)
RED = (255, 0, 0)
DARK_RED = (200, 0, 0)
WHITE = (255, 255, 255)
PINK = (255, 100, 100)

# Lirik lagu - sama persis seperti di video
LYRICS_LINES = [
    "Got nothing to",
    "hide no more",
    "I don't know where",
    "to start",
    "But to show you",
    "the shape of my heart",
    "I'm lookin' back on",
    "things I've done",
    "I never wanna play",
    "the same old part",
    "I'll keep you in",
    "the dark",
    "Now let me show",
    "you the shape of",
    "my heart"
]

def get_heart_points(cx, cy, size):
    points = []
    for i in range(100):
        t = math.pi * 2 * i / 100
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
        points.append((cx + x * size, cy + y * size))
    return points

class FloatingHeart:
    def __init__(self, x, y, lyric_index):
        self.x = x
        self.y = y
        self.base_size = 8
        self.size = 0
        self.max_size = self.base_size + random.uniform(0, 3)
        self.lyric_index = lyric_index
        self.lyric_text = LYRICS_LINES[lyric_index % len(LYRICS_LINES)]
        self.speed = random.uniform(1.5, 2.5)
        self.font = pygame.font.Font(None, 28)
        
    def update(self):
        self.y -= self.speed
        if self.size < self.max_size:
            self.size += 0.1
        return self.y > -150
    
    def draw(self, surface):
        if self.size <= 0:
            return
            
        # Gambar hati
        pts = get_heart_points(self.x, self.y, self.size)
        pygame.draw.polygon(surface, RED, pts)
        pygame.draw.polygon(surface, DARK_RED, pts, 2)
        
        # Render teks di dalam hati
        text_surface = self.font.render(self.lyric_text, True, WHITE)
        text_rect = text_surface.get_rect(center=(self.x, self.y))
        surface.blit(text_surface, text_rect)

class SmallHeart:
    def __init__(self, w, h):
        self.x = random.randint(0, w)
        self.y = h + random.randint(0, 50)
        self.size = random.randint(3, 8)
        self.speed = random.uniform(1, 3)
        self.color = random.choice([RED, PINK, (255, 150, 150)])
        
    def update(self, w, h):
        self.y -= self.speed
        # Wrap around horizontally
        if self.x < 0:
            self.x = w
        elif self.x > w:
            self.x = 0
        return self.y > -20
    
    def draw(self, surface):
        pts = get_heart_points(self.x, self.y, self.size / 15)
        if len(pts) > 2:
            pygame.draw.polygon(surface, self.color, pts)

# Variabel utama
big_hearts = []
small_hearts = []
current_lyric_index = 0
spawn_timer = 0
frame_count = 0

running = True
while running:
    frame_count += 1
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    w, h = screen.get_size()
    screen.fill(BLACK)
    
    # Spawn hati besar baru secara berkala
    spawn_timer += 1
    if spawn_timer >= 180:  # Setiap 3 detik (60 fps * 3)
        x_pos = random.randint(200, w - 200)
        big_hearts.append(FloatingHeart(x_pos, h + 50, current_lyric_index))
        current_lyric_index += 1
        spawn_timer = 0
    
    # Spawn hati kecil
    if random.random() < 0.3:
        small_hearts.append(SmallHeart(w, h))
    
    # Update dan gambar hati besar
    new_big_hearts = []
    for bh in big_hearts:
        if bh.update():
            bh.draw(screen)
            new_big_hearts.append(bh)
    big_hearts = new_big_hearts
    
    # Update dan gambar hati kecil
    new_small_hearts = []
    for sh in small_hearts:
        if sh.update(w, h):
            sh.draw(screen)
            new_small_hearts.append(sh)
    small_hearts = new_small_hearts
    
    pygame.display.flip()
    clock.tick(60)

pygame.mixer.music.stop()
pygame.quit()
sys.exit()