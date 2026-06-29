from PIL import Image
import os

DELIMITER = "####END####"

def text_to_binary(text):
    return ''.join(format(ord(i), '08b') for i in text)

def file_to_binary(filepath):
    with open(filepath, "rb") as f:
        data = f.read()

    filename = os.path.basename(filepath)

    payload = (
        filename.encode() +
        b"||" +
        data +
        DELIMITER.encode()
    )

    return ''.join(format(byte, '08b') for byte in payload)

def hide_file(image_path, file_path, output_image):
    img = Image.open(image_path)
    img = img.convert("RGB")

    binary_data = file_to_binary(file_path)
    data_len = len(binary_data)

    pixels = list(img.getdata())

    if data_len > len(pixels) * 3:
        raise ValueError("Gambar terlalu kecil!")

    data_index = 0
    new_pixels = []

    for pixel in pixels:
        r, g, b = pixel

        if data_index < data_len:
            r = (r & ~1) | int(binary_data[data_index])
            data_index += 1

        if data_index < data_len:
            g = (g & ~1) | int(binary_data[data_index])
            data_index += 1

        if data_index < data_len:
            b = (b & ~1) | int(binary_data[data_index])
            data_index += 1

        new_pixels.append((r, g, b))

    img.putdata(new_pixels)
    img.save(output_image)

    print("Berhasil disimpan:", output_image)

hide_file(
    "tumor1.JPG",
    "rahasia.txt",
    "hasil.png"
)