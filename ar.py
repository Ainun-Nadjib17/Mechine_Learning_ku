import cv2
import mediapipe as mp
import numpy as np
import math
import time

# ================= INIT =================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2,
                       min_detection_confidence=0.7,
                       min_tracking_confidence=0.7)
cap = cv2.VideoCapture(0)

# ================= ROTATION =================
def rotate_x(P,a):
    Rx=np.array([[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]])
    return P@Rx.T

def rotate_y(P,a):
    Ry=np.array([[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]])
    return P@Ry.T

# ================= OBJECTS =================
CUBE=np.array([
    [-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],
    [-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]
],float)

CUBE_EDGES=[(0,1),(1,2),(2,3),(3,0),
            (4,5),(5,6),(6,7),(7,4),
            (0,4),(1,5),(2,6),(3,7)]

TRI=np.array([[0,-1,0],[-1,1,0],[1,1,0]],float)
TRI_EDGES=[(0,1),(1,2),(2,0)]

PYR=np.array([
    [0,-1,0],[-1,1,-1],[1,1,-1],[1,1,1],[-1,1,1]
],float)
PYR_EDGES=[(0,1),(0,2),(0,3),(0,4),
           (1,2),(2,3),(3,4),(4,1)]

# ================= VOLUME LINES =================
def volume_lines(step=0.5):
    lines=[]
    g=np.arange(-1,1.01,step)
    for y in g:
        for z in g:
            lines.append(([-1,y,z],[1,y,z]))
    for x in g:
        for z in g:
            lines.append(([x,-1,z],[x,1,z]))
    for x in g:
        for y in g:
            lines.append(([x,y,-1],[x,y,1]))
    return lines

VLINES=volume_lines()

# ================= INSIDE CHECK =================
def inside_cube(p):
    x,y,z=p
    return -1<=x<=1 and -1<=y<=1 and -1<=z<=1

def inside_pyramid(p):
    x,y,z=p
    return y>=abs(x) and y>=abs(z) and y<=1

def inside_triangle(p):
    x,y,z=p
    return y>=abs(x) and y<=1

# ================= STATE =================
obj_mode="CUBE"
scale=1.0
rx=0
ry=0
cx,cy=320,240
locked=False
prev_dist=None
prev_center=None
tick=0

# ================= UTILS =================
def finger_up(h,tip,pip):
    return h.landmark[tip].y < h.landmark[pip].y

def pinch(h,W,H):
    return math.hypot(
        (h.landmark[4].x-h.landmark[8].x)*W,
        (h.landmark[4].y-h.landmark[8].y)*H
    ) < 35

# ================= LOOP =================
while True:
    ret,frame=cap.read()
    if not ret: break
    frame=cv2.flip(frame,1)
    H,W,_=frame.shape

    rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
    res=hands.process(rgb)

    if res.multi_hand_landmarks and len(res.multi_hand_landmarks)==2:
        h1,h2=res.multi_hand_landmarks

        c1=(h1.landmark[9].x*W,h1.landmark[9].y*H)
        c2=(h2.landmark[9].x*W,h2.landmark[9].y*H)
        center=((c1[0]+c2[0])/2,(c1[1]+c2[1])/2)

        locked = pinch(h1,W,H) or pinch(h2,W,H)

        if not locked:
            cx,cy=int(center[0]),int(center[1])

        dist=math.hypot(c2[0]-c1[0],c2[1]-c1[1])
        if prev_dist and not locked:
            scale += (dist-prev_dist)*0.002
            scale = max(0.4,min(2.8,scale))
        prev_dist=dist

        if prev_center and not locked:
            dx=center[0]-prev_center[0]
            dy=center[1]-prev_center[1]
            ry += dx*0.005
            rx += dy*0.005
        prev_center=center

        # ===== SWITCH OBJECT =====
        if finger_up(h1,8,6) and not finger_up(h1,12,10):
            obj_mode="CUBE"
        if finger_up(h1,8,6) and finger_up(h1,12,10):
            obj_mode="TRI"
        if finger_up(h1,8,6) and finger_up(h1,20,18):
            obj_mode="PYR"

        if obj_mode=="CUBE":
            P,E=CUBE,CUBE_EDGES
            check=inside_cube
        elif obj_mode=="TRI":
            P,E=TRI,TRI_EDGES
            check=inside_triangle
        else:
            P,E=PYR,PYR_EDGES
            check=inside_pyramid

        # ===== SCANLINES =====
        overlay=frame.copy()
        for y in range(0,H,6):
            cv2.line(overlay,(0,y),(W,y),(255,0,255),1)
        frame=cv2.addWeighted(frame,0.88,overlay,0.12,0)

        # ===== SOLID VOLUME (ISI DALAM) =====
        for a,b in VLINES:
            if not (check(a) and check(b)):
                continue

            A=np.array([a])*80*scale
            B=np.array([b])*80*scale

            A=rotate_x(A,rx); A=rotate_y(A,ry)[0]
            B=rotate_x(B,rx); B=rotate_y(B,ry)[0]

            depth=(A[2]+B[2])/2
            bright=int(np.interp(depth,[-80,80],[80,255]))
            pulse=int(40*math.sin(tick+depth*0.05))
            col=(bright+pulse,0,bright+pulse)

            p1=(int(cx+A[0]),int(cy+A[1]))
            p2=(int(cx+B[0]),int(cy+B[1]))
            cv2.line(frame,p1,p2,col,1)

        # ===== OUTER FRAME =====
        P=P*80*scale
        P=rotate_x(P,rx); P=rotate_y(P,ry)
        proj=[(int(cx+x),int(cy+y)) for x,y,z in P]

        glow=frame.copy()
        for e in E:
            cv2.line(glow,proj[e[0]],proj[e[1]],(255,0,255),6)
        glow=cv2.GaussianBlur(glow,(25,25),0)
        frame=cv2.addWeighted(frame,0.7,glow,0.7,0)

        for e in E:
            cv2.line(frame,proj[e[0]],proj[e[1]],(255,0,255),2)

        # ===== HUD =====
        cv2.putText(frame,f"{obj_mode} | SCALE {scale:.2f}",
            (20,40),cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,255),2)
        if locked:
            cv2.putText(frame,"GRAB",(20,75),
                cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,0,255),2)

        tick+=0.08

    cv2.imshow("FLOATING SOLID CYBER HOLOGRAM 3D",frame)
    if cv2.waitKey(1)&0xFF==27:
        break

cap.release()
cv2.destroyAllWindows()
