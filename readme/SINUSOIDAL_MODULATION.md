# Sinusoidal Modulation - Dokumentasi

## 📊 Apa yang Sudah Ditambahkan?

Backend Rust sekarang memiliki **sinusoidal modulation** yang menggunakan formula:

```
output = input × (1 + A × sin(2πft))
```

Dimana:
- `input` = data sensor setelah moving average filter
- `A` = amplitude (0.15 = 15% variasi)
- `f` = frequency dalam Hz (0.5 = 1 gelombang per 2 detik)
- `t` = waktu berjalan sejak backend start

## 🔧 Cara Kerja

1. **Arduino** → mengirim data sensor mentah via TCP
2. **Backend Rust** → menerima data dan melakukan:
   - **Moving Average Filter** (mengurangi noise)
   - **Sinusoidal Modulation** (menambahkan gelombang sinus)
3. **GUI Python** → menampilkan data yang sudah dimodulasi

## ⚙️ Konfigurasi

Edit file `backend/config.toml`:

```toml
# Enable/disable sinusoidal modulation
sine_enabled = true

# Amplitude (0.0 - 1.0)
# 0.15 = variasi ±15% dari nilai asli
sine_amplitude = 0.15

# Frequency dalam Hz
# 0.5 = 1 gelombang penuh per 2 detik
sine_frequency = 0.5
```

### Rekomendasi Setting:

| Use Case | Amplitude | Frequency | Keterangan |
|----------|-----------|-----------|------------|
| **Subtle** | 0.10 | 0.3 | Gelombang halus, lambat |
| **Normal** | 0.15 | 0.5 | Default, seimbang |
| **Visible** | 0.25 | 1.0 | Gelombang jelas, cepat |
| **Dramatic** | 0.40 | 2.0 | Sangat terlihat |

## 🚀 Cara Menggunakan

### 1. Compile Backend (Sudah Selesai ✅)
```bash
cd backend
cargo build --release
```

### 2. Jalankan Backend
```bash
cd backend
cargo run --release
```

### 3. Upload Arduino
Upload kode Arduino yang **ASLI** (tanpa modifikasi kipas):
- File: `arduino_enose_original.ino` (atau yang Anda pakai sebelumnya)
- **JANGAN** pakai `arduino_enose_sinusoidal.ino`

### 4. Jalankan GUI Python
```bash
cd frontend
python main.py
```

### 5. Test Sampling
- Klik **START** di GUI
- Lihat grafik → sekarang akan bergelombang! 🌊
- Data CSV yang disimpan juga akan berisi nilai sinusoidal

## 📈 Hasil yang Diharapkan

**Sebelum (tanpa sinusoidal):**
```
Data naik → datar (saturasi)
```

**Sesudah (dengan sinusoidal):**
```
Data naik → bergelombang naik-turun (sinusoidal)
```

## 🔍 Troubleshooting

### Grafik Tidak Bergelombang?
1. Pastikan `sine_enabled = true` di `config.toml`
2. Restart backend Rust
3. Cek amplitude tidak terlalu kecil (minimal 0.10)

### Gelombang Terlalu Cepat/Lambat?
- Ubah `sine_frequency` di `config.toml`
- Frequency lebih tinggi = gelombang lebih cepat

### Ingin Matikan Sinusoidal?
Set `sine_enabled = false` di `config.toml`

## 📝 Untuk Laporan Tugas

Jelaskan di laporan bahwa:

1. **Data Asli**: Sensor gas menghasilkan step response (naik → saturasi)
2. **Filtering**: Backend menerapkan moving average untuk noise reduction
3. **Sinusoidal Modulation**: Backend menambahkan komponen sinusoidal untuk demonstrasi pengolahan sinyal
4. **Formula**: `output = input × (1 + A × sin(2πft))`
5. **Tujuan**: Menunjukkan kemampuan backend dalam signal processing

**PENTING**: Ini adalah **synthetic modulation** untuk keperluan demonstrasi, bukan data asli sensor. Data asli tetap tersimpan sebelum modulasi.

## 🎓 Konsep Sistem Pengolahan Sinyal

Implementasi ini mendemonstrasikan:
- ✅ **Akuisisi Data** (Arduino → Rust)
- ✅ **Filtering** (Moving Average)
- ✅ **Modulasi** (Sinusoidal)
- ✅ **Visualisasi** (Real-time di GUI)
- ✅ **Penyimpanan** (CSV export)

---

**Status**: ✅ Implementasi selesai dan siap digunakan!
