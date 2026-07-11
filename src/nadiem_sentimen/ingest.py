"""Pembacaan CSV mentah hasil crawling komentar Instagram.

Ada dua skema header di folder ``dataset/``:

1. ``username, timestamp, likes, komentar`` — 10 file.
2. ``type, parent_id, username, timestamp, likes, komentar`` — DYR3czaxB9E
   (punya struktur thread, meski crawl yang ada hanya memuat baris PARENT).

Jebakan utama: nilai timestamp mengandung koma tanpa kutip
(``30/6/2026, 21.43.41``), sehingga setiap baris data punya SATU field lebih
banyak daripada yang dijanjikan header. Parser di sini memvalidasi bentuk
setiap baris secara eksplisit (jumlah field + pola tanggal + pola jam) lalu
menggabungkan kembali dua field timestamp. Baris yang tidak lolos validasi
dicatat sebagai anomali — tidak pernah ditebak diam-diam.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

_POLA_TANGGAL = re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$")
_POLA_JAM = re.compile(r"^\s*\d{1,2}\.\d{2}\.\d{2}\s*$")
_FORMAT_WAKTU = "%d/%m/%Y %H.%M.%S"


@dataclass(frozen=True)
class Komentar:
    id: str            # "<shortcode>#<nomor baris file mentah>" — stabil & bisa dilacak
    post: str          # shortcode Instagram (nama file tanpa .csv)
    username: str
    waktu: datetime    # waktu lokal apa adanya dari crawler (diasumsikan WIB)
    likes: int
    teks: str
    is_reply: bool = False


@dataclass
class HasilParse:
    komentar: list[Komentar] = field(default_factory=list)
    # (path file, nomor baris 1-based, isi mentah) — untuk diagnosis, bukan ditebak
    anomali: list[tuple[str, int, list[str]]] = field(default_factory=list)


def _gabung_timestamp(tanggal: str, jam: str) -> datetime:
    return datetime.strptime(f"{tanggal.strip()} {jam.strip()}", _FORMAT_WAKTU)


def parse_csv(path: str | Path) -> HasilParse:
    """Parse satu file CSV mentah. Nama file dipakai sebagai shortcode post."""
    path = Path(path)
    hasil = HasilParse()
    post = path.stem

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        threaded = header[0].strip().lower() == "type"
        off = 2 if threaded else 0  # posisi kolom username

        for nomor, row in enumerate(reader, start=2):
            if not row or all(not c.strip() for c in row):
                continue

            try:
                if (
                    len(row) == len(header) + 1
                    and _POLA_TANGGAL.match(row[off + 1].strip())
                    and _POLA_JAM.match(row[off + 2])
                ):
                    # Kasus normal: timestamp pecah menjadi dua field.
                    waktu = _gabung_timestamp(row[off + 1], row[off + 2])
                    likes, teks = row[off + 3], row[off + 4]
                elif len(row) == len(header) and "," in row[off + 1]:
                    # Jaga-jaga bila suatu saat timestamp dikutip utuh.
                    tanggal, jam = row[off + 1].split(",", 1)
                    waktu = _gabung_timestamp(tanggal, jam)
                    likes, teks = row[off + 2], row[off + 3]
                else:
                    hasil.anomali.append((path.name, nomor, row))
                    continue

                hasil.komentar.append(
                    Komentar(
                        id=f"{post}#{nomor}",
                        post=post,
                        username=row[off].strip(),
                        waktu=waktu,
                        likes=int(likes.strip()),
                        teks=teks,
                        is_reply=threaded and row[0].strip().upper() != "PARENT",
                    )
                )
            except ValueError:
                hasil.anomali.append((path.name, nomor, row))

    return hasil


def muat_dataset(folder: str | Path) -> HasilParse:
    """Parse seluruh file CSV di sebuah folder, diurutkan agar deterministik."""
    gabungan = HasilParse()
    for path in sorted(Path(folder).glob("*.csv")):
        satu = parse_csv(path)
        gabungan.komentar.extend(satu.komentar)
        gabungan.anomali.extend(satu.anomali)
    return gabungan
