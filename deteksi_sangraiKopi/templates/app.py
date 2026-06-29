from flask import Flask, render_template, request
import os
from detek import predict

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/", methods=["GET","POST"])
def index():

    label = None
    conf = None
    img_path = None

    if request.method == "POST":

        file = request.files["image"]

        if file:

            path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(path)

            label, conf = predict(path)

            img_path = path

    return render_template(
        "index.html",
        label=label,
        conf=conf,
        img_path=img_path
    )


if __name__ == "__main__":
    app.run(debug=True)