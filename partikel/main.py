import pygame
import cv2
import mediapipe as mp
import random
import math
import numpy as np

# ======================
# CONFIG
# ======================

WIDTH = 1200
HEIGHT = 700
PARTICLE_COUNT = 5000

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gesture Particle System")

clock = pygame.time.Clock()

# ======================
# HAND TRACKING
# ======================

cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# ======================
# PARTICLE
# ======================

class Particle:

    def __init__(self):

        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)

        self.tx = self.x
        self.ty = self.y

    def update(self):

        self.x += (self.tx - self.x) * 0.05
        self.y += (self.ty - self.y) * 0.05

    def draw(self):

        pygame.draw.circle(
            screen,
            (255,255,255),
            (int(self.x), int(self.y)),
            2
        )

        pygame.draw.circle(
            screen,
            (120,120,255),
            (int(self.x), int(self.y)),
            4,
            1
        )

particles = [Particle() for _ in range(PARTICLE_COUNT)]

# ======================
# SHAPES
# ======================

def random_scene():

    points = []

    for _ in range(PARTICLE_COUNT):

        points.append((
            random.randint(0, WIDTH),
            random.randint(0, HEIGHT)
        ))

    return points

def text_scene():

    surface = pygame.Surface((WIDTH, HEIGHT))
    surface.fill((0,0,0))

    font = pygame.font.SysFont("Arial", 180, bold=True)

    txt = font.render(
        "HELLO WORLD",
        True,
        (255,255,255)
    )

    rect = txt.get_rect(
        center=(WIDTH//2, HEIGHT//2)
    )

    surface.blit(txt, rect)

    points = []

    for x in range(0, WIDTH, 6):
        for y in range(0, HEIGHT, 6):

            if surface.get_at((x,y))[0] > 0:
                points.append((x,y))

    return points

def heart_scene():

    points = []

    for t in np.linspace(
        0,
        math.pi*2,
        PARTICLE_COUNT
    ):

        x = 16 * math.sin(t)**3

        y = (
            13 * math.cos(t)
            - 5 * math.cos(2*t)
            - 2 * math.cos(3*t)
            - math.cos(4*t)
        )

        scale = 20

        px = WIDTH//2 + x * scale
        py = HEIGHT//2 - y * scale

        points.append((px, py))

    return points

def planet_scene():

    points = []

    cx = WIDTH//2
    cy = HEIGHT//2

    # planet

    for _ in range(2500):

        angle = random.uniform(0, math.pi*2)

        r = random.randint(40,140)

        x = cx + math.cos(angle)*r
        y = cy + math.sin(angle)*r

        points.append((x,y))

    # ring

    for _ in range(2500):

        angle = random.uniform(0, math.pi*2)

        rx = 250
        ry = 90

        x = cx + math.cos(angle)*rx
        y = cy + math.sin(angle)*ry

        rot = math.radians(30)

        xr = (
            (x-cx)*math.cos(rot)
            -
            (y-cy)*math.sin(rot)
        ) + cx

        yr = (
            (x-cx)*math.sin(rot)
            +
            (y-cy)*math.cos(rot)
        ) + cy

        points.append((xr,yr))

    return points

# ======================
# APPLY SHAPE
# ======================

current_shape = "random"

def apply_shape(points):

    for i, p in enumerate(particles):

        if i < len(points):

            p.tx = points[i][0]
            p.ty = points[i][1]

        else:

            p.tx = random.randint(0, WIDTH)
            p.ty = random.randint(0, HEIGHT)

apply_shape(random_scene())

# ======================
# GESTURE
# ======================

last_change = 0

def detect_fingers(frame):

    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    result = hands.process(rgb)

    if not result.multi_hand_landmarks:
        return 0

    hand = result.multi_hand_landmarks[0]

    mp_draw.draw_landmarks(
        frame,
        hand,
        mp_hands.HAND_CONNECTIONS
    )

    fingers = 0

    if hand.landmark[4].x < hand.landmark[3].x:
        fingers += 1

    tips = [8,12,16,20]

    for tip in tips:

        if hand.landmark[tip].y < hand.landmark[tip-2].y:
            fingers += 1

    return fingers

# ======================
# LOOP
# ======================

running = True

font_small = pygame.font.SysFont(
    "Arial",
    30
)

CAM_W = 320
CAM_H = 240

camera_surface = None
fingers = 0

while running:

    clock.tick(60)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

    ret, frame = cap.read()

    if ret:

        fingers = detect_fingers(frame)

        frame_rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        frame_rgb = cv2.flip(
            frame_rgb,
            1
        )

        frame_rgb = cv2.resize(
            frame_rgb,
            (CAM_W, CAM_H)
        )

        camera_surface = pygame.surfarray.make_surface(
            np.rot90(frame_rgb)
        )

        now = pygame.time.get_ticks()

        if now - last_change > 1000:

            if fingers == 1:

                apply_shape(
                    planet_scene()
                )

                current_shape = "PLANET"

            elif fingers == 2:

                apply_shape(
                    heart_scene()
                )

                current_shape = "LOVE"

            elif fingers == 5:

                apply_shape(
                    text_scene()
                )

                current_shape = "HELLO WORLD"

            elif fingers == 0:

                apply_shape(
                    random_scene()
                )

                current_shape = "RANDOM"

            last_change = now

    screen.fill((0,0,0))

    for p in particles:

        p.update()
        p.draw()

    text = font_small.render(
        f"Mode : {current_shape}",
        True,
        (255,255,255)
    )

    screen.blit(text, (20,20))

    fps = font_small.render(
        f"FPS : {int(clock.get_fps())}",
        True,
        (255,255,255)
    )

    screen.blit(fps, (20,60))

    # ======================
    # CAMERA WINDOW
    # ======================

    if camera_surface is not None:

        pygame.draw.rect(
            screen,
            (255,255,255),
            (
                WIDTH - CAM_W - 15,
                15,
                CAM_W + 4,
                CAM_H + 4
            ),
            2
        )

        screen.blit(
            camera_surface,
            (
                WIDTH - CAM_W - 13,
                17
            )
        )

        finger_text = font_small.render(
            f"Fingers : {fingers}",
            True,
            (255,255,255)
        )

        screen.blit(
            finger_text,
            (
                WIDTH - CAM_W - 13,
                CAM_H + 30
            )
        )

    pygame.display.flip()

cap.release()
pygame.quit()