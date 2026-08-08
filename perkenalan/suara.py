
import asyncio
import edge_tts

# ==========================================
# AI INTRO - PERKENALAN MOKHAMAD AINUN NADJIB
# ==========================================

TEXT = """
Saya adalah AI Assistant dari Mokhamad Ainun Nadjib.

Izinkan saya memperkenalkan sedikit tentang dirinya.

Mokhamad Ainun Nadjib merupakan mahasiswa baru Teknik Informatika yang memiliki ketertarikan besar pada dunia teknologi, khususnya Artificial Intelligence dan Machine Learning.

Ketertarikannya pada teknologi tidak berhenti pada mempelajari teori. Ia senang mencoba, bereksperimen, dan mengubah ide menjadi sebuah project yang dapat digunakan.

Beberapa bidang yang sedang ia eksplorasi antara lain Computer Vision, pengembangan website dan aplikasi, serta Cyber Security dan OSINT.

Baginya, setiap project bukan hanya tentang menghasilkan sesuatu, tetapi juga tentang memahami bagaimana teknologi tersebut bekerja.

Di luar dunia pemrograman, ada satu hal sederhana yang cukup dekat dengannya.

Kopi.

Lebih tepatnya, kopi hitam tanpa gula.

Ia juga memiliki rasa ingin tahu yang cukup besar. Ketika menemukan sesuatu yang menarik, ia cenderung terus mempelajarinya sampai memahami bagaimana sesuatu tersebut dapat bekerja.

Sebagai mahasiswa baru, perjalanan ini tentunya masih sangat panjang.

Masih banyak hal yang ingin dipelajari.
Masih banyak teknologi yang ingin dicoba.
Dan tentunya, masih banyak karya yang ingin dikembangkan.

Saya adalah AI Assistant dari Mokhamad Ainun Nadjib.

Dan ini...
adalah awal dari perjalanannya.

"""

VOICE = "id-ID-ArdiNeural"
OUTPUT = "ai_intro_mokhamad_ainun_nadjib.mp3"


async def generate_voice():
    communicate = edge_tts.Communicate(
        text=TEXT,
        voice=VOICE,
        rate="-8%",
        volume="+0%",
        pitch="-2Hz"
    )

    await communicate.save(OUTPUT)

    print("=" * 50)
    print("AI VOICE BERHASIL DIBUAT!")
    print(f"File : {OUTPUT}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(generate_voice())

