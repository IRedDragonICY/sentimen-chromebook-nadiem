"""Penandaan sub-isu (topik) berbasis leksikon terkurasi.

Bukan topic modeling probabilistik — untuk produk yang jujur, tag deterministik
yang bisa diaudit lebih baik daripada topik LDA yang sulit diberi nama. Setiap
komentar bisa punya >1 topik. Leksikon disusun dari isu yang benar-benar muncul
di data (diverifikasi saat eksplorasi).

Dipakai NFKC+casefold via ``normalisasi.bersihkan`` sebelum pencocokan.
"""

from __future__ import annotations

import re

# Kata kunci per topik. Batas kata longgar untuk menangkap varian slang.
_TOPIK = {
    "gaji_hakim": r"gaji hakim|naik.{0,6}(280|300|hampir 300)|280\s*%|300\s*%|kenaikan gaji",
    "peradilan": r"\bhakim\b|\bjaksa\b|\bvonis\b|pengadilan|sidang|dakwaan|tuntutan|yang mulia|"
                 r"kejaksaan|\bkpk\b|hukuman|banding|kasasi|penjara|terdakwa|keadilan",
    "chromebook": r"chromebook|chrome ?os|laptop|\bgoogle\b|pengadaan|e-?katalog|"
                  r"digitalisasi|perangkat|mark ?up|9[.,]3 ?trili",
    "kurikulum": r"kurikulum|merdeka belajar|pendidikan|guru|sekolah|siswa|ujian nasional|"
                 r"zonasi|mendikbud|anbk",
    "gojek": r"gojek|go-?jek|ojol|driver|grab|lapangan (kerja|pekerjaan)|\bceo\b|startup",
    "politik": r"jokowi|mulyono|prabowo|gibran|presiden|pemerintah|rezim|istana|"
               r"\bdpr\b|partai|menteri|tom lembong|negara|konoha",
    "agama_moral": r"allah|tuhan|akhirat|dosa|azab|karma|doa|zolim|zalim|dzolim|"
                   r"neraka|surga|amin|aamiin|insya",
}
_KOMPILASI = {t: re.compile(p, re.IGNORECASE) for t, p in _TOPIK.items()}

TOPIK_LABEL = {
    "gaji_hakim": "Gaji hakim naik",
    "peradilan": "Proses peradilan",
    "chromebook": "Pengadaan Chromebook",
    "kurikulum": "Kurikulum & pendidikan",
    "gojek": "Gojek & lapangan kerja",
    "politik": "Politik nasional",
    "agama_moral": "Agama & moral",
}


def topik_komentar(teks: str) -> list[str]:
    return [t for t, pola in _KOMPILASI.items() if pola.search(teks)]


def tandai_topik(teks_iter) -> list[list[str]]:
    return [topik_komentar(t) for t in teks_iter]
