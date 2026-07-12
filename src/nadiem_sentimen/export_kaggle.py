"""Menyusun paket dataset siap-unggah ke Kaggle di ``dist/kaggle/``.

Menghasilkan tiga lapis data + dokumentasi:

- ``raw/``            — 11 CSV asli, format dipertahankan apa adanya (termasuk
                       jebakan koma pada timestamp), **hanya** identitas yang
                       disamarkan.
- ``comments_clean``  — dataset terpadu 38.845 komentar hasil pipeline
                       (CSV + Parquet).
- ``labels_gold``     — 710 komentar berlabel manusia (CSV + Parquet).
- ``labels_silver`` / ``scores_full`` — ditambahkan otomatis bila artefaknya
                       sudah ada (silver.parquet / skor.parquet), sehingga
                       skrip ini bisa dijalankan ulang untuk rilis v2.

Kebijakan privasi (brief §10). Data ini menyangkut individu nyata pada isu
hukum-politik yang sensitif, maka SEBELUM dipublikasikan:

1. Username → ``author_hash``: SHA-256 bergaram, dipangkas 12 heksadesimal.
   Stabil (bisa dipakai analisis per-akun / penautan thread) tetapi tidak bisa
   dibalik ke handle asli. Garam disimpan lokal di ``data/.author_salt`` (tidak
   ikut dipublikasikan) agar hash konsisten antar-berkas dan antar-rilis.
2. ``@sebutan`` di dalam teks ikut disamarkan memakai fungsi hash yang sama,
   sehingga sebutan atas akun yang juga berkomentar tetap tertaut ke
   ``author_hash`` yang sama — struktur referensi terjaga, identitas tidak.

Jalankan:  python -m nadiem_sentimen.export_kaggle
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import secrets
import shutil
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SUMBER_RAW = ROOT / "dataset"
PROSES = ROOT / "data" / "processed"
LABEL = ROOT / "data" / "labels"
KELUARAN = ROOT / "dist" / "kaggle"
SALT_PATH = ROOT / "data" / ".author_salt"

LISENSI = "CC BY-NC-SA 4.0"
CAKUPAN_AWAL = "2025-09-05"
CAKUPAN_AKHIR = "2026-07-11"

# Nilai parent_id yang BUKAN username — jangan di-hash.
_SENTINEL = {"", "none", "null", "-"}
# Sebutan: diawali huruf/angka/underscore, boleh titik di tengah (bukan di ujung).
_SEBUTAN = re.compile(r"@([A-Za-z0-9_][A-Za-z0-9_.]{0,29})")


def _muat_garam() -> bytes:
    """Baca garam lokal; buat sekali bila belum ada. Tak pernah dipublikasikan."""
    if SALT_PATH.exists():
        return bytes.fromhex(SALT_PATH.read_text().strip())
    garam = secrets.token_bytes(16)
    SALT_PATH.write_text(garam.hex())
    return garam


class Penyamar:
    """Menyamarkan identitas secara konsisten memakai satu garam."""

    def __init__(self, garam: bytes):
        self._garam = garam
        self._memo: dict[str, str] = {}

    def hash_akun(self, nama: str) -> str:
        nama_norm = nama.strip().lower()
        if nama_norm in _SENTINEL:
            return nama  # sentinel (mis. "NONE") dibiarkan apa adanya
        if nama_norm not in self._memo:
            h = hashlib.sha256(self._garam + nama_norm.encode()).hexdigest()[:12]
            self._memo[nama_norm] = h
        return self._memo[nama_norm]

    def samarkan_teks(self, teks: str) -> str:
        """Ganti setiap @sebutan dengan @<hash>, titik ujung tak ikut."""
        if not teks or "@" not in teks:
            return teks
        return _SEBUTAN.sub(
            lambda m: "@" + self.hash_akun(m.group(1).rstrip(".")), teks
        )


# ---------------------------------------------------------------- lapis RAW ---
def _ekspor_raw(peny: Penyamar, keluaran: Path) -> dict:
    """Salin 11 CSV asli; hanya username, parent_id, dan @sebutan disamarkan.

    Struktur baris dipertahankan lewat csv.reader/writer — termasuk timestamp
    yang terpecah dua field akibat koma tanpa kutip (jebakan itu tetap tampak).
    """
    (keluaran / "raw").mkdir(parents=True, exist_ok=True)
    ringkas = {}
    for src in sorted(SUMBER_RAW.glob("*.csv")):
        with open(src, newline="", encoding="utf-8") as f:
            baris = list(csv.reader(f))
        header = baris[0]
        threaded = header[0].strip().lower() == "type"
        i_user = 2 if threaded else 0  # kolom username

        keluar = [header]
        for row in baris[1:]:
            if not row or all(not c.strip() for c in row):
                keluar.append(row)
                continue
            if len(row) > i_user:
                row[i_user] = peny.hash_akun(row[i_user])
            if threaded and len(row) > 1:
                row[1] = peny.hash_akun(row[1])  # parent_id = username induk
            row[-1] = peny.samarkan_teks(row[-1])  # kolom komentar = field terakhir
            keluar.append(row)

        dst = keluaran / "raw" / src.name
        with open(dst, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(keluar)
        ringkas[src.name] = len(keluar) - 1
    return ringkas


# ------------------------------------------------------------- lapis CLEAN ---
# Peta nama kolom sumber → nama publikasi. Nama dipertahankan Indonesia (setia
# ke sumber), kecuali username yang diganti author_hash. is_reply dibuang: crawl
# hanya memuat komentar level atas (seluruhnya False), menyimpannya menyesatkan.
KOLOM_CLEAN = [
    "id", "post", "author_hash", "waktu", "likes", "fase",
    "teks", "teks_bersih", "n_karakter", "hanya_emoji", "emoji",
    "klaster_dup", "ukuran_klaster",
]


def _ekspor_clean(peny: Penyamar, keluaran: Path) -> int:
    df = pd.read_parquet(PROSES / "komentar.parquet").copy()
    df["author_hash"] = df["username"].map(peny.hash_akun)
    for kol in ("teks", "teks_bersih"):
        df[kol] = df[kol].map(peny.samarkan_teks)
    df = df[KOLOM_CLEAN]
    df.to_parquet(keluaran / "comments_clean.parquet", index=False)
    df.to_csv(keluaran / "comments_clean.csv", index=False)
    return len(df)


# ------------------------------------------------------------ lapis LABELS ---
def _ekspor_label(peny: Penyamar, nama_src: Path, dasar: str, keluaran: Path) -> int | None:
    if not nama_src.exists():
        return None
    df = pd.read_parquet(nama_src).copy()
    if "post" not in df.columns and "id" in df.columns:
        df.insert(1, "post", df["id"].str.split("#").str[0])
    for kol in ("teks_bersih", "catatan"):
        if kol in df.columns:
            df[kol] = df[kol].fillna("").map(peny.samarkan_teks)
    df.to_parquet(keluaran / f"{dasar}.parquet", index=False)
    df.to_csv(keluaran / f"{dasar}.csv", index=False)
    return len(df)


def _ekspor_skor(peny: Penyamar, keluaran: Path) -> int | None:
    src = PROSES / "skor.parquet"
    if not src.exists():
        return None
    df = pd.read_parquet(src).copy()
    if "username" in df.columns:
        df = df.drop(columns=["username"])  # skor per-komentar, bukan per-akun
    for kol in ("teks", "teks_bersih"):
        if kol in df.columns:
            df[kol] = df[kol].map(peny.samarkan_teks)
    df.to_parquet(keluaran / "scores_full.parquet", index=False)
    df.to_csv(keluaran / "scores_full.csv", index=False)
    return len(df)


def main() -> None:
    if KELUARAN.exists():
        shutil.rmtree(KELUARAN)
    KELUARAN.mkdir(parents=True)
    peny = Penyamar(_muat_garam())

    n_raw = _ekspor_raw(peny, KELUARAN)
    n_clean = _ekspor_clean(peny, KELUARAN)
    n_gold = _ekspor_label(peny, LABEL / "gold.parquet", "labels_gold", KELUARAN)
    n_silver = _ekspor_label(peny, LABEL / "silver.parquet", "labels_silver", KELUARAN)
    n_skor = _ekspor_skor(peny, KELUARAN)

    manifest = {
        "judul": "Komentar Instagram: Kasus Chromebook Nadiem Makarim",
        "lisensi": LISENSI,
        "cakupan_waktu": {"mulai": CAKUPAN_AWAL, "akhir": CAKUPAN_AKHIR},
        "cakupan_geografis": "Indonesia",
        "digenerasi": date.today().isoformat(),
        "privasi": "username & @sebutan menjadi hash SHA-256 bergaram (tak terbalikkan)",
        "berkas": {
            "raw/": {"deskripsi": "11 CSV asli, identitas disamarkan", "baris_per_post": n_raw},
            "comments_clean": {"baris": n_clean},
            "labels_gold": {"baris": n_gold},
            "labels_silver": {"baris": n_silver},
            "scores_full": {"baris": n_skor},
        },
    }
    (KELUARAN / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2)
    )

    print(f"Paket Kaggle → {KELUARAN}")
    print(json.dumps(manifest["berkas"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
