from PIL import Image

DELIMITER = b"####END####"

def extract_file(image_path):
    img = Image.open(image_path)
    img = img.convert("RGB")

    pixels = list(img.getdata())

    binary_data = ""

    for pixel in pixels:
        r, g, b = pixel

        binary_data += str(r & 1)
        binary_data += str(g & 1)
        binary_data += str(b & 1)

    bytes_data = bytearray()

    for i in range(0, len(binary_data), 8):
        byte = binary_data[i:i+8]

        if len(byte) == 8:
            bytes_data.append(int(byte, 2))

    end_index = bytes_data.find(DELIMITER)

    if end_index == -1:
        print("Tidak ada data tersembunyi")
        return

    payload = bytes(bytes_data[:end_index])

    filename, content = payload.split(b"||", 1)

    filename = filename.decode()

    with open(filename, "wb") as f:
        f.write(content)

    print("File berhasil diekstrak:", filename)

extract_file("hasil.png")