const imageInput = document.getElementById("imageInput");
const preview = document.getElementById("preview");
const fileName = document.getElementById("fileName");
const inspectButton = document.getElementById("inspectButton");

let selectedImage = null;

imageInput.addEventListener("change", () => {
    selectedImage = imageInput.files[0];

    if (!selectedImage) return;

    fileName.textContent = selectedImage.name;
    preview.src = URL.createObjectURL(selectedImage);
    preview.hidden = false;
    inspectButton.disabled = false;

    document.getElementById("result").hidden = true;
    document.getElementById("emptyState").hidden = false;
    document.getElementById("errorMessage").textContent = "";
});

inspectButton.addEventListener("click", async () => {
    if (!selectedImage) return;

    const formData = new FormData();
    formData.append("image", selectedImage);

    inspectButton.disabled = true;
    inspectButton.textContent = "ANALYZING...";

    document.getElementById("errorMessage").textContent = "";

    try {
        const response = await fetch("/inspect", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Inspection failed");
        }

        document.getElementById("emptyState").hidden = true;
        document.getElementById("result").hidden = false;

        const prediction = document.getElementById("prediction");

        prediction.textContent = data.prediction;
        prediction.className =
            "prediction " +
            (data.is_anomaly ? "anomaly" : "normal");

        document.getElementById("score").textContent =
            Number(data.score).toFixed(4);

        drawAnomalyMap(data.anomaly_map);

    } catch (error) {
        document.getElementById("errorMessage").textContent =
            error.message;
    } finally {
        inspectButton.disabled = false;
        inspectButton.textContent = "START INSPECTION →";
    }
});

function drawAnomalyMap(map) {
    const canvas = document.getElementById("anomalyCanvas");
    const ctx = canvas.getContext("2d");

    const height = map.length;
    const width = map[0].length;

    canvas.width = width;
    canvas.height = height;

    const values = map.flat();
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;

    const imageData = ctx.createImageData(width, height);

    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const value = (map[y][x] - min) / range;

            const index = (y * width + x) * 4;

            imageData.data[index] =
                Math.round(255 * Math.max(0, Math.min(1, 1.5 - Math.abs(4 * value - 3))));

            imageData.data[index + 1] =
                Math.round(255 * Math.max(0, Math.min(1, 1.5 - Math.abs(4 * value - 2))));

            imageData.data[index + 2] =
                Math.round(255 * Math.max(0, Math.min(1, 1.5 - Math.abs(4 * value - 1))));

            imageData.data[index + 3] = 255;
        }
    }

    ctx.putImageData(imageData, 0, 0);
}