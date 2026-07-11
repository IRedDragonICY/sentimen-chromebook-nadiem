"""nadiem_sentimen — pipeline analisis sentimen komentar kasus Chromebook.

Modul inti:
- ingest        : pembacaan CSV mentah (termasuk jebakan koma-di-timestamp)
- normalisasi   : pembersihan teks, deteksi emoji, kunci duplikat, fase peristiwa
- build_dataset : CLI penyatuan 11 CSV menjadi Parquet terproses
"""

__version__ = "0.1.0"
