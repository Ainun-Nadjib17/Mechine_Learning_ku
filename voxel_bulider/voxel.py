import cv2
import mediapipe as mp
import numpy as np

# kamera
cap = cv2.VideoCapture(0)

# mediapipe hand
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# voxel grid
grid_size = 20
voxel_grid = np.zeros((grid_size, grid_size))

cell = 30

while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)

    h, w, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    cursor_x, cursor_y = None, None
    pinch = False

    if result.multi_hand_landmarks:
        for hand in result.multi_hand_landmarks:

            lm = hand.landmark

            # index finger tip
            ix = int(lm[8].x * w)
            iy = int(lm[8].y * h)

            # thumb tip
            tx = int(lm[4].x * w)
            ty = int(lm[4].y * h)

            cursor_x, cursor_y = ix, iy

            dist = np.hypot(ix - tx, iy - ty)

            if dist < 40:
                pinch = True

            mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

    # convert posisi ke grid
    if cursor_x is not None:
        gx = int(cursor_x / cell)
        gy = int(cursor_y / cell)

        if gx < grid_size and gy < grid_size:

            if pinch:
                voxel_grid[gy][gx] = 1

    # gambar voxel
    for y in range(grid_size):
        for x in range(grid_size):

            px = x * cell
            py = y * cell

            if voxel_grid[y][x] == 1:
                cv2.rectangle(frame,(px,py),(px+cell,py+cell),(255,0,0),-1)

            cv2.rectangle(frame,(px,py),(px+cell,py+cell),(50,50,50),1)

    # cursor
    if cursor_x:
        cv2.circle(frame,(cursor_x,cursor_y),10,(0,255,0),-1)

    cv2.imshow("Voxel Builder", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()