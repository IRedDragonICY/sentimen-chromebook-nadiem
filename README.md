# Cermin Publik — Analisis Sentimen Wacana Kasus Chromebook

Sistem analisis sentimen bahasa Indonesia untuk ~38.845 komentar Instagram
tentang kasus hukum yang menjerat Nadiem Makarim (dugaan korupsi pengadaan
Chromebook). Dari data mentah tak berlabel hingga model yang bisa dipakai dan
aplikasi web yang menyajikan temuannya.

> **Netralitas & keterwakilan.** Sistem ini mengukur *sentimen komentar*, bukan
> menilai bersalah atau tidaknya siapa pun; ia menjunjung asas praduga tak
> bersalah. Data berasal dari 11 unggahan Instagram dan **bukan** survei yang
> mewakili opini publik Indonesia — hasilnya tidak boleh digeneralisasi.

---

## Apa yang dibangun

- **Pipeline data reproducible** — 11 CSV mentah (dengan timestamp bermasalah &
  skema campur) → satu dataset Parquet bersih, dengan klaster near-duplikat dan
  fase peristiwa terhitung.
- **Skema label tiga lapis** — `spam` · `sikap` (6 kelas) · `emosi` (5 kelas),
  dirancang dari bukti bahwa wacana ini terarah ke banyak target sekaligus.
- **Gold set 710 komentar** berlabel manusia untuk evaluasi jujur, dan **silver
  set** berlabel LLM lokal untuk data latih.
- **Model multi-task IndoBERT** — satu encoder, tiga kepala; artefak tersimpan +
  `predict()` yang tahan input kotor + kalibrasi keyakinan & ambang abstain.
- **Aplikasi Streamlit** berbahasa Indonesia dengan sistem desain sendiri.

Empat kapabilitas reusable ditulis sebagai skill: `skills/sentiment-labeling-id`,
`skills/id-text-cleaning`, `skills/model-eval`, `skills/design-system`.

## Jalankan dari nol

Prasyarat: Python 3.12 (dikelola `uv`), GPU NVIDIA opsional (mempercepat training
& anotasi), [Ollama](https://ollama.com) untuk anotator silver.

```bash
# 1. Lingkungan
uv venv --python 3.12 .venv
uv pip install -p .venv/bin/python -e . -r requirements.txt

# 2. Server anotator (WAJIB dengan GPU terlihat, jika ada GPU)
CUDA_VISIBLE_DEVICES=0 ollama serve &
ollama pull qwen3.5:9b

# 3. Pipeline penuh: data → silver → train → evaluasi → skor
MODEL_ANOTATOR=qwen3.5:9b bin/pipeline.sh

# 4. Aplikasi
.venv/bin/streamlit run app/app.py
```

Setiap tahap juga bisa dijalankan sendiri sebagai modul, mis.
`python -m nadiem_sentimen.build_dataset`.

## Struktur

```
dataset/                     11 CSV mentah (tidak diubah)
data/processed/              komentar.parquet, skor.parquet, profil.json
data/labels/                 gold (710) + silver + split train/val/test
src/nadiem_sentimen/         paket inti (ingest, model, train, inference, …)
app/                         aplikasi Streamlit + sistem desain
skills/                      empat SKILL.md reusable
reports/                     hasil evaluasi
tests/                       uji parser, normalisasi, heuristik
DECISIONS.md                 jejak keputusan teknis + alasan
MODEL_CARD.md                kemampuan, keterbatasan, bias, larangan pakai
```

## Temuan utama

_Diisi setelah pipeline evaluasi & skoring dijalankan (lihat `reports/`)._

## Uji

```bash
.venv/bin/python -m pytest -q
```

## Etika & batas penggunaan

Lihat `MODEL_CARD.md` dan halaman **Metodologi & Etika** di aplikasi. Ringkasnya:
model tidak untuk moderasi otomatis tanpa manusia, tidak untuk menilai/menghukum
individu, dan identitas akun tidak ditampilkan di seluruh antarmuka.

## Lisensi & atribusi

Encoder dasar: IndoBERT (IndoBenchmark). Anotator silver: model terbuka via
Ollama. Kode proyek ini ditulis untuk keperluan analisis; hormati ketentuan
platform sumber data.
