import pyaudio

def check_mic():
    try:
        p = pyaudio.PyAudio()
    except Exception as e:
        print(f"❌ Gagal inisialisasi PyAudio: {e}")
        return

    print("=== DAFTAR MICROPHONE ===")
    mic_indices = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            print(f"Index {i}: {info['name']}")
            mic_indices.append(i)
    
    if not mic_indices:
        print("❌ TIDAK ADA MICROPHONE YANG TERDETEKSI OLEGO PYTHON!")
        p.terminate()
        return

    print("\n=== TES BUKA MICROPHONE ===")
    # Coba buka mic pertama yang ditemukan
    target_index = mic_indices[0]
    print(f"Mencoba buka mic di Index {target_index} ({p.get_device_info_by_index(target_index)['name']})...")
    
    try:
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=16000,
                        input=True,
                        input_device_index=target_index,
                        frames_per_buffer=1024)
        print("✅ BERHASIL! Mic aman dan bisa dipakai.")
        stream.stop_stream()
        stream.close()
    except Exception as e:
        print(f"❌ GAGAL BUKA MIC! Error aslinya adalah: {e}")
        
    p.terminate()

if __name__ == "__main__":
    check_mic()