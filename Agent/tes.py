from playwright.sync_api import sync_playwright
import time

BASE_URL = "http://localhost:5500"


def buka_form(page):
    page.goto(BASE_URL)

    page.evaluate("""
        localStorage.setItem("adminLogin", "true");
    """)

    page.goto(f"{BASE_URL}/tambah-jadwal.html")

    print("URL:", page.url)

    page.wait_for_timeout(3000)

    print("TITLE:", page.title())

    print("ISI HALAMAN:")
    print(page.content()[:500])


def test_tambah_jadwal(page):
    print("\n[TEST] Tambah Jadwal")

    try:
        buka_form(page)

        nama_matkul = f"TEST-{int(time.time())}"

        page.fill("#tanggal", "2026-06-16")
        page.select_option("#hari", label="Selasa")
        page.fill("#matkul", nama_matkul)
        page.fill("#dosen", "Budi Santoso")
        page.select_option("#ruangan", label="Lab. A")
        page.fill("#jamMulai", "08:00")
        page.fill("#jamSelesai", "10:00")

        page.check(
            'input[name="status"][value="Aktif"]'
        )

        page.click('button[type="submit"]')

        page.wait_for_url(
            "**/jadwal.html",
            timeout=10000
        )

        print("✅ Data berhasil disimpan")
        print("📝 Mata kuliah:", nama_matkul)

    except Exception as e:
        print("❌ Tambah jadwal gagal")
        print(e)

        screenshot_gagal(page, "gagal_tambah_jadwal")


def test_matkul_kosong(page):
    print("\n[TEST] Mata Kuliah Kosong")

    try:
        buka_form(page)

        page.fill("#tanggal", "2026-06-16")
        page.select_option("#hari", label="Selasa")

        page.fill("#dosen", "Budi")
        page.select_option("#ruangan", label="Lab. A")
        page.fill("#jamMulai", "08:00")
        page.fill("#jamSelesai", "10:00")

        page.click('button[type="submit"]')

        invalid = page.locator(
            "#matkul"
        ).evaluate(
            "el => !el.checkValidity()"
        )

        if invalid:
            print("✅ Validasi mata kuliah bekerja")
        else:
            print("❌ Mata kuliah kosong tetap lolos")

            screenshot_gagal(
                page,
                "matkul_kosong"
            )

    except Exception as e:
        print("❌ Test gagal")
        print(e)

        screenshot_gagal(page, "matkul_error")


def test_jam_tidak_valid(page):
    print("\n[TEST] Jam Tidak Valid")

    try:
        buka_form(page)

        page.fill("#tanggal", "2026-06-16")
        page.select_option("#hari", label="Selasa")
        page.fill("#matkul", "TEST JAM")
        page.fill("#dosen", "Andi")
        page.select_option("#ruangan", label="R.101")

        page.fill("#jamMulai", "10:00")
        page.fill("#jamSelesai", "08:00")

        page.click('button[type="submit"]')

        if page.url.endswith("jadwal.html"):
            print("❌ Jam tidak valid tetap tersimpan")

            screenshot_gagal(
                page,
                "jam_tidak_valid"
            )

        else:
            print("✅ Jam tidak valid ditolak")

    except Exception as e:
        print("⚠️ Tidak ada validasi jam")
        print(e)


def test_status_draft(page):
    print("\n[TEST] Status Draft")

    try:
        buka_form(page)

        page.check(
            'input[name="status"][value="Draft"]'
        )

        if page.is_checked(
            'input[name="status"][value="Draft"]'
        ):
            print("✅ Status Draft dapat dipilih")
        else:
            print("❌ Status Draft gagal")

    except Exception as e:
        print("❌ Test gagal")
        print(e)


def test_reset(page):
    print("\n[TEST] Reset Form")

    try:
        buka_form(page)

        page.fill("#matkul", "Pemrograman")

        page.click('button[type="reset"]')

        if page.input_value("#matkul") == "":
            print("✅ Reset berhasil")
        else:
            print("❌ Reset gagal")

    except Exception as e:
        print("❌ Test gagal")
        print(e)


def main():
    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False,
            slow_mo=500
        )

        page = browser.new_page()

        print("🚀 Memulai Automation Test SIJAKUL")

        test_tambah_jadwal(page)
        test_matkul_kosong(page)
        test_jam_tidak_valid(page)
        test_status_draft(page)
        test_reset(page)

        print("\n===== TEST SELESAI =====")

        page.wait_for_timeout(3000)

        browser.close()


if __name__ == "__main__":
    main()