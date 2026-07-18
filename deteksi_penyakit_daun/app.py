import os
import json
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from utils.detector import TomatoDetector

app = Flask(__name__)
app.secret_key = "tomato-ai-secret-key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
DATABASE_PATH = os.path.join(BASE_DIR, "database", "disease_info.json")

os.makedirs(UPLOAD_DIR, exist_ok=True)

detector = TomatoDetector()

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_diseases():
    with open(DATABASE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@app.route("/")
def index():
    model_stats = detector.get_model_info()
    return render_template("index.html", model_stats=model_stats)


@app.route("/tentang")
def tentang():
    return render_template("tentang.html")


@app.route("/deteksi", methods=["GET", "POST"])
def deteksi():
    if request.method == "POST":
        if "image" not in request.files:
            return render_template("deteksi.html", error="Tidak ada gambar yang dipilih.")

        file = request.files["image"]
        if file.filename == "":
            return render_template("deteksi.html", error="Tidak ada gambar yang dipilih.")

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_DIR, filename)
            file.save(filepath)

            try:
                detections, result_image = detector.detect(filepath)
                diseases = load_diseases()

                disease_info = {}
                if detections:
                    top = detections[0]["class_name"]
                    if top in diseases:
                        disease_info = diseases[top]

                return render_template(
                    "deteksi.html",
                    results=detections,
                    disease_info=disease_info,
                    result_image=result_image,
                    uploaded_image=filename,
                )
            except Exception as e:
                return render_template("deteksi.html", error=f"Terjadi kesalahan: {str(e)}")

        return render_template("deteksi.html", error="Format file tidak didukung. Gunakan PNG, JPG, atau JPEG.")

    return render_template("deteksi.html")


@app.route("/penyakit")
def penyakit():
    diseases = load_diseases()
    return render_template("penyakit.html", diseases=diseases)


@app.route("/penyakit/<path:name>")
def detail_penyakit(name):
    diseases = load_diseases()
    if name in diseases:
        return render_template("detail_penyakit.html", disease=diseases[name], disease_name=name)
    return render_template("penyakit.html", diseases=diseases, error="Penyakit tidak ditemukan.")


@app.route("/kontak")
def kontak():
    return render_template("kontak.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
