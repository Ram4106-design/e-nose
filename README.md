# 🔬 E-NOSE Real-Time Monitoring System

Sistem Electronic Nose (E-Nose) untuk monitoring kualitas udara secara real-time dengan integrasi Edge Impulse untuk machine learning. Proyek ini menggabungkan performa tinggi Rust di backend dan kemudahan Python untuk antarmuka pengguna (GUI).

---

## 📋 Fitur Utama

### Backend (Rust)
- ⚡ **High-performance TCP Server**: Menangani aliran data sensor dengan latensi sangat rendah.
- 🔄 **FSM Control**: Mengontrol siklus sampling 5-tahap (PRE_COND → RAMP_UP → HOLD → PURGE → RECOVERY).
- 📡 **Serial Communication**: Komunikasi stabil dengan Arduino.

### Frontend (Python/PyQt6)
- 🎨 **Modern UI**: Antarmuka gelap (dark mode) dengan aksen neon yang futuristik.
- 📈 **Real-time Graph**: Visualisasi 7 sensor sekaligus secara langsung.
- ☁️ **Edge Impulse Integration**: Upload data otomatis untuk pelatihan model AI.
- 💾 **CSV Export**: Simpan data lokal untuk analisis lebih lanjut.

---

## 🛠️ Persiapan (Prerequisites)

Sebelum memulai, pastikan Anda telah menginstal software berikut:

1.  **Rust**: Untuk menjalankan backend.
    - Download: [rustup.rs](https://rustup.rs/)
2.  **Python 3.8+**: Untuk menjalankan frontend.
    - Download: [python.org](https://www.python.org/)
3.  **Arduino IDE**: Untuk upload kode ke mikrokontroler.
    - Download: [arduino.cc](https://www.arduino.cc/en/software)
4.  **Git**: Untuk mengunduh kode program.
    - Download: [git-scm.com](https://git-scm.com/)

---

## 📥 Instalasi

Ikuti langkah-langkah ini untuk menyiapkan proyek di komputer Anda:

### 1. Clone Repository
Buka terminal (Command Prompt / PowerShell) dan jalankan perintah berikut:

```bash
git clone https://github.com/Ram4106-design/e-nose.git
cd e-nose
```

### 2. Setup Backend (Rust)
Masuk ke folder backend dan build programnya:

```bash
cd backend
cargo build --release
```
*Tunggu hingga proses compile selesai (mungkin memakan waktu beberapa menit untuk pertama kali).*

### 3. Setup Frontend (Python)
Buka terminal baru, masuk ke folder frontend, dan install library yang dibutuhkan:

```bash
cd frontend
pip install -r requirements.txt
```

---

## 🚀 Cara Menjalankan (How to Run)

Untuk menjalankan sistem, Anda perlu membuka 3 komponen secara berurutan:

### Langkah 1: Upload Kode Arduino
1.  Buka file `arduino_enose_persistent.ino` menggunakan Arduino IDE.
2.  Hubungkan Arduino ke komputer via USB.
3.  Pilih Board dan Port yang sesuai di Arduino IDE.
4.  Klik tombol **Upload** (➡️).
5.  Pastikan upload sukses ("Done uploading").

### Langkah 2: Jalankan Backend (Server)
Backend bertugas membaca data dari Arduino dan mengirimkannya ke Frontend.

1.  Buka terminal di folder `backend`.
2.  Jalankan perintah:
    ```bash
    cargo run --release
    ```
3.  Anda akan melihat pesan: `Server listening on 127.0.0.1:8082`.
4.  **Biarkan terminal ini tetap terbuka.**

### Langkah 3: Jalankan Frontend (Aplikasi)
Frontend adalah tampilan antarmuka untuk mengontrol alat.

1.  Buka terminal **baru** di folder `frontend`.
2.  Jalankan perintah:
    ```bash
    python main.py
    ```
3.  Jendela aplikasi E-Nose akan muncul.

---

## 📖 Panduan Penggunaan (User Guide)

Berikut adalah langkah-langkah detail untuk menggunakan aplikasi:

### A. Menghubungkan ke Sistem
1.  Saat aplikasi terbuka, status di pojok kiri bawah harusnya **"Connected"** (Hijau).
2.  Jika **"Disconnected"**, pastikan Backend (Langkah 2) sudah berjalan.

### B. Melakukan Sampling (Pengambilan Data)
1.  Siapkan sampel aroma di dekat sensor.
2.  Klik tombol **▶ START SAMPLING**.
3.  Sistem akan berjalan otomatis melalui 5 tahapan:
    - **PRE_COND**: Pemanasan sensor.
    - **RAMP_UP**: Persiapan naik.
    - **HOLD**: Pengambilan data utama (Penting!).
    - **PURGE**: Pembersihan sensor.
    - **RECOVERY**: Pendinginan.
4.  Tunggu hingga progress bar mencapai 100% dan status kembali ke "IDLE".

### C. Upload ke Edge Impulse (Otomatis/Manual)
Fitur ini memungkinkan Anda mengirim data langsung ke cloud Edge Impulse untuk machine learning.

1.  Di panel kanan bawah ("💾 Export & Model"), isi data berikut:
    - **API Key**: Kunci API dari proyek Edge Impulse Anda.
    - **Project ID**: ID Proyek Edge Impulse.
    - **Label**: Nama label untuk data ini (contoh: `kopi`, `teh`, `alkohol`).
2.  Jika ingin upload otomatis setiap selesai sampling, biarkan tombol upload manual. Aplikasi akan otomatis mengupload jika API Key terisi.
3.  Untuk upload manual data terakhir, klik tombol **📤 UPLOAD TO EI**.

### D. Menyimpan Data ke CSV
1.  Setelah sampling selesai, klik tombol **💾 SAVE CSV**.
2.  File akan tersimpan di folder `csv/` dengan nama format tanggal dan waktu.

---

## 🔧 Troubleshooting (Pemecahan Masalah)

- **Error: "Serial port not found" di Backend**
  - Pastikan Arduino tercolok dengan benar.
  - Tutup Arduino IDE Serial Monitor jika sedang terbuka (Port tidak bisa dipakai 2 aplikasi sekaligus).

- **Error: "Connection Refused" di Frontend**
  - Pastikan Backend (Rust) sudah berjalan (`cargo run --release`).
  - Cek apakah firewall memblokir port 8082.

---

## 👥 Penulis
- **Sadrakh Ram Loudan Saputra** - Institut Teknologi Sepuluh Nopember
- **Hakan Maulana Yazid Zidane** - Institut Teknologi Sepuluh Nopember
- **Melodya Sembiring** - Institut Teknologi Sepuluh Nopember
