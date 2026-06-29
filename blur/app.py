from flask import Flask, render_template, Response
import cv2
import mediapipe as mp

app = Flask(__name__)

mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

camera = cv2.VideoCapture(0)


def finger_up(hand_landmarks):
    tip = [4, 8, 12, 16, 20]
    pip = [3, 6, 10, 14, 18]

    fingers = []

    fingers.append(
        hand_landmarks.landmark[4].x <
        hand_landmarks.landmark[3].x
    )

    for t, p in zip(tip[1:], pip[1:]):
        fingers.append(
            hand_landmarks.landmark[t].y <
            hand_landmarks.landmark[p].y
        )

    return fingers


def generate():

    while True:

        success, frame = camera.read()

        if not success:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        result = hands.process(rgb)

        blur = False

        if result.multi_hand_landmarks:

            for hand in result.multi_hand_landmarks:

                fingers = finger_up(hand)

                if fingers == [False, True, True, False, False]:
                    blur = True

        if blur:

            frame = cv2.GaussianBlur(frame, (51, 51), 0)

            cv2.putText(
                frame,
                "PEACE DETECTED",
                (20,40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,255,0),
                2
            )

        ret, buffer = cv2.imencode(".jpg", frame)

        frame = buffer.tobytes()

        yield(
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            frame +
            b'\r\n'
        )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video")
def video():
    return Response(
        generate(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


if __name__ == "__main__":
    app.run(debug=True)