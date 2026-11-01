from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Ganti nanti dengan URL Cloudflare Tunnel dari Colab
COLAB_API_URL = "https://rug-fur-cakes-generates.trycloudflare.com"

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/inspect", methods=["POST"])
def inspect():
    if "image" not in request.files:
        return jsonify({"error": "Gambar belum dipilih"}), 400

    image = request.files["image"]

    if not image.filename:
        return jsonify({"error": "Nama gambar tidak valid"}), 400

    try:
        response = requests.post(
            f"{COLAB_API_URL}/predict",
            files={
                "image": (
                    image.filename,
                    image.stream,
                    image.mimetype or "image/png"
                )
            },
            timeout=180
        )

        response.raise_for_status()
        return jsonify(response.json())

    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Proses inspeksi terlalu lama. Coba lagi."
        }), 504

    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": f"Gagal terhubung ke server AI: {str(e)}"
        }), 502


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)