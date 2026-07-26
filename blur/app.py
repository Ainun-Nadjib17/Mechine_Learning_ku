from flask import Flask, render_template, request, jsonify
import cv2
import mediapipe as mp
import numpy as np
import base64

app = Flask(__name__)

mp_hands = mp.solutions.hands


def create_hands():

    return mp_hands.Hands(
        static_image_mode=True,
        max_num_hands=1,
        model_complexity=0,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    )


def finger_up(hand_landmarks):

    tip = [4, 8, 12, 16, 20]
    pip = [3, 6, 10, 14, 18]

    fingers = []

    # ibu jari
    fingers.append(
        hand_landmarks.landmark[4].x <
        hand_landmarks.landmark[3].x
    )

    # jari lain
    for t, p in zip(tip[1:], pip[1:]):

        fingers.append(
            hand_landmarks.landmark[t].y <
            hand_landmarks.landmark[p].y
        )

    return fingers



@app.route("/")
def index():

    return render_template("index.html")



@app.route("/detect", methods=["POST"])
def detect():

    try:

        data = request.json["image"]

        header, encoded = data.split(",", 1)


        img = base64.b64decode(encoded)

        npimg = np.frombuffer(
            img,
            np.uint8
        )


        frame = cv2.imdecode(
            npimg,
            cv2.IMREAD_COLOR
        )


        if frame is None:
            raise Exception("Frame kosong")


        frame = cv2.resize(
            frame,
            (640,480)
        )


        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )


        blur = False


        # MediaPipe baru setiap request
        with create_hands() as hands:

            result = hands.process(rgb)


            if result.multi_hand_landmarks:

                for hand in result.multi_hand_landmarks:


                    fingers = finger_up(hand)


                    if fingers == [
                        False,
                        True,
                        True,
                        False,
                        False
                    ]:

                        blur = True



        if blur:

            frame = cv2.GaussianBlur(
                frame,
                (21,21),
                0
            )


            cv2.putText(
                frame,
                "PEACE DETECTED",
                (20,40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,255,0),
                2
            )


        _, buffer = cv2.imencode(
            ".jpg",
            frame
        )


        image = base64.b64encode(
            buffer
        ).decode()



        return jsonify({

            "image": image,
            "blur": blur

        })


    except Exception as e:

        print(
            "ERROR DETECT:",
            e
        )


        return jsonify({

            "error": str(e)

        }),500




if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True,
        use_reloader=False
    )