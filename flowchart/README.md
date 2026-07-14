# Flowchart Pipeline untuk Papan Tulis Canva

Tujuh diagram alur PNG (resolusi tinggi, ~2400 sampai 2640 px, latar transparan)
untuk memaparkan sistem dari prapemrosesan hingga aplikasi. Angka pada diagram
diambil langsung dari kode dan artefak proyek, bukan ilustrasi.

Latar dibuat transparan agar menyatu dengan papan tulis Canva yang berwarna putih
bertitik. Tiap berkas bisa langsung diseret ke bagian "Flowchart Program".

## Daftar diagram

| # | Berkas | Isi | Modul sumber |
|---|--------|-----|--------------|
| 1 | `01_peta_pipeline.png` | Ikhtisar delapan tahap: data mentah hingga aplikasi | seluruh pipeline |
| 2 | `02_prapemrosesan.png` | 11 CSV mentah menjadi `komentar.parquet`: validasi baris, jebakan timestamp berkoma, kolom turunan | `ingest.py`, `build_dataset.py` |
| 3 | `03_normalisasi.png` | Tiga representasi teks (`bersihkan`, `kunci_duplikat`, `daftar_emoji`) beserta kegunaannya | `normalisasi.py` |
| 4 | `04_pelabelan_split.png` | Gold 710 (manusia) dan silver 5.912 (LLM), pembagian berbasis klaster yang bebas kebocoran | `sampling.py`, `label_silver.py`, `assemble_training.py` |
| 5 | `05_model_pelatihan.png` | Arsitektur multitugas IndoBERT, pelatihan, kalibrasi suhu, dan ambang abstain | `model.py`, `train.py` |
| 6 | `06_inferensi.png` | Alur `MesinSentimen.predict()`: prapemrosesan, kalibrasi, aturan spam dan emoji | `inference.py` |
| 7 | `07_serving.png` | Arsitektur inferensi langsung: Streamlit dengan Space HuggingFace beserta cadangan | `app/app.py`, `space/app.py` |
| 8 | `08_insight.png` | Papan temuan bergaya post-it untuk bagian "Insight" (sembilan kartu dan catatan etis) | `reports/temuan.json`, `reports/evaluasi.json` |

## Angka kunci yang tampil

- Total komentar: 38.845 (11 unggahan, 31.405 klaster near-duplikat)
- Label: gold 710 (manusia) dan silver 5.912 (LLM lokal via Ollama)
- Pembagian: train 6.233 (321 gold, 5.912 silver), val 106, test 283 (val dan test hanya gold)
- Skema: spam (2), sikap (6), emosi (5)
- Penyetelan halus pada gold test: macro-F1 sikap 0,544, emosi 0,624, spam 1,00
- Kalibrasi: suhu sikap 1,52, emosi 1,18, spam 0,50; ambang abstain sikap 0,62, emosi 0,64

## Membuat ulang

Membutuhkan `rsvg-convert` (paket `librsvg`) dan font Noto Sans.

```bash
cd flowchart/src
python gen.py            # tujuh diagram alur
python gen_insight.py    # papan insight (08)
for f in svg/*.svg; do rsvg-convert -z 2 "$f" -o "../$(basename "$f" .svg).png"; done
```

Sumber SVG ada di `svg/`, generator di `src/` (`flowlib.py` adalah pustaka,
`gen.py` menyusun tiap diagram). Warna, teks, dan tata letak dapat disunting di sana.
