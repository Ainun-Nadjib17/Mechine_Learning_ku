import cv2
import mediapipe as mp
import numpy as np
import sys

print("Python executable:", sys.executable)
print("Sys path:", sys.path)
print("OpenCV version:", cv2.__version__)
print("Mediapipe version:", mp.__version__)
try:
    print("Mediapipe solutions:", mp.solutions)
except AttributeError as e:
    print("Error accessing mp.solutions:", e)

print("Numpy version:", np.__version__)
