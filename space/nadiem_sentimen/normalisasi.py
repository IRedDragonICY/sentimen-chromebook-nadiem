"""Normalisasi teks komentar media sosial Indonesia.

Prinsip: teks mentah tidak pernah dibuang — setiap fungsi di sini menghasilkan
representasi turunan untuk keperluan spesifik, dan fungsi yang sama dipakai
saat training maupun inferensi (menghindari train/serve skew).

Tiga representasi:
- ``bersihkan()``     : normalisasi ringan untuk input model (NFKC, kontrol,
                        whitespace). Emoji DIPERTAHANKAN — 11% komentar hanya
                        emoji dan itu sinyal, bukan noise.
- ``kunci_duplikat()``: kunci agresif untuk klaster near-duplikat (anti-bocor
                        train/test dan deteksi spam berulang). Menyamakan
                        varian yang hanya beda angka/tanda baca/huruf mewah.
- ``daftar_emoji()``  : ekstraksi emoji untuk analisis afeksi.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime

# Rentang blok Unicode yang diperlakukan sebagai emoji. Sengaja lebar
# (mencakup simbol panah/geometri yang lazim dipakai ekspresif di IG).
_RENTANG_EMOJI = (
    (0x1F000, 0x1FAFF),  # emoji modern + suplemen
    (0x2600, 0x27BF),    # simbol umum & dingbats (❤ ✨ ☔ …)
    (0x2B00, 0x2BFF),
    (0x2190, 0x21FF),
    (0x2300, 0x23FF),
    (0x25A0, 0x25FF),
)
# Karakter tak kasatmata yang menempel pada emoji (ZWJ, variation selector,
# skin tone ada di rentang 1F3FB–1F3FF yang sudah tercakup di atas).
_PENDAMPING_EMOJI = {0xFE0E, 0xFE0F, 0x200D, 0x20E3}


def _adalah_emoji(ch: str) -> bool:
    cp = ord(ch)
    return cp in _PENDAMPING_EMOJI or any(lo <= cp <= hi for lo, hi in _RENTANG_EMOJI)


def bersihkan(teks: str) -> str:
    """Normalisasi ringan: NFKC (melipat huruf 'mewah' 𝗔𝗕𝗖 → ABC), buang
    karakter kontrol, rapikan whitespace. Case dan emoji dipertahankan."""
    teks = unicodedata.normalize("NFKC", teks)
    teks = "".join(c for c in teks if unicodedata.category(c) != "Cc" or c in "\n\t")
    return re.sub(r"\s+", " ", teks).strip()


def daftar_emoji(teks: str) -> list[str]:
    return [c for c in teks if _adalah_emoji(c) and ord(c) not in _PENDAMPING_EMOJI]


def hanya_emoji(teks: str) -> bool:
    """True bila komentar hanya berisi emoji (+ tanda baca/spasi).

    Komentar seperti "😭😭😭" atau "🥺💔" masuk kategori ini; "ok 😭" tidak.
    """
    isi = [c for c in unicodedata.normalize("NFKC", teks) if not c.isspace()]
    if not isi or not any(_adalah_emoji(c) for c in isi):
        return False
    return all(_adalah_emoji(c) or unicodedata.category(c).startswith("P") for c in isi)


def kunci_duplikat(teks: str) -> str:
    """Kunci klaster near-duplikat.

    Menyamakan varian yang hanya berbeda kapitalisasi, angka (nominal "menang
    7,2jt" vs "8,5jt" pada spam), tanda baca, spasi, atau huruf Unicode mewah.
    Komentar emoji-only jatuh ke kunci berupa himpunan emojinya, sehingga
    "😭😭😭" dan "😭😭" satu klaster.
    """
    t = unicodedata.normalize("NFKC", teks).casefold()
    emoji = "".join(sorted(set(daftar_emoji(t))))
    huruf = [c for c in t if c.isalpha() and not _adalah_emoji(c)]
    inti = re.sub(r"\s+", "", "".join(huruf))
    return inti if inti else emoji


# Batas fase ditarik dari distribusi tanggal aktual (lihat DECISIONS.md D5):
# lonjakan besar dimulai 30 Jun 2026 (reaksi vonis), klaster Mei = penangkapan.
_FASE = (
    (date(2025, 12, 31), "f1_sep2025"),
    (date(2026, 4, 30), "f2_awal2026"),
    (date(2026, 6, 28), "f3_mei2026"),
    (date.max, "f4_jul2026"),
)


def fase_peristiwa(waktu: datetime | date) -> str:
    """Kode fase peristiwa untuk sebuah tanggal komentar."""
    d = waktu.date() if isinstance(waktu, datetime) else waktu
    for batas, kode in _FASE:
        if d <= batas:
            return kode
    raise AssertionError("unreachable")
