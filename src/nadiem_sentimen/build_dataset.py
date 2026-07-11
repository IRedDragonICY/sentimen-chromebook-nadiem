"""CLI penyatuan data: 11 CSV mentah → ``data/processed/komentar.parquet``.

Data mentah tidak pernah diubah; skrip ini hanya membaca. Keluarannya
deterministik (urutan tetap, tanpa nilai acak) sehingga hash Parquet bisa
dipakai sebagai versi data. Profil ringkas + sha256 tiap file mentah ditulis
ke ``profil.json`` sebagai jejak provenance.

Jalankan:  python -m nadiem_sentimen.build_dataset
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from .ingest import muat_dataset
from .normalisasi import bersihkan, daftar_emoji, fase_peristiwa, hanya_emoji, kunci_duplikat


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bangun(folder_mentah: Path, folder_keluaran: Path) -> pd.DataFrame:
    hasil = muat_dataset(folder_mentah)
    if hasil.anomali:
        # Anomali menandakan format berubah — lebih baik berhenti keras daripada
        # menghasilkan dataset yang diam-diam cacat.
        contoh = hasil.anomali[:5]
        raise SystemExit(f"{len(hasil.anomali)} baris tidak dikenali, contoh: {contoh}")

    df = pd.DataFrame(
        {
            "id": k.id,
            "post": k.post,
            "username": k.username,
            "waktu": k.waktu,
            "likes": k.likes,
            "is_reply": k.is_reply,
            "teks": k.teks,
        }
        for k in hasil.komentar
    )
    df["fase"] = df["waktu"].map(fase_peristiwa)
    df["teks_bersih"] = df["teks"].map(bersihkan)
    df["n_karakter"] = df["teks_bersih"].str.len()
    df["hanya_emoji"] = df["teks"].map(hanya_emoji)
    df["emoji"] = df["teks"].map(lambda t: "".join(daftar_emoji(t)))

    kunci = df["teks"].map(kunci_duplikat)
    df["klaster_dup"] = pd.factorize(kunci)[0]
    df["ukuran_klaster"] = df.groupby("klaster_dup")["id"].transform("size")

    df["_baris"] = df["id"].str.split("#").str[1].astype(int)
    df = df.sort_values(["post", "_baris"]).drop(columns="_baris").reset_index(drop=True)

    folder_keluaran.mkdir(parents=True, exist_ok=True)
    df.to_parquet(folder_keluaran / "komentar.parquet", index=False)

    profil = {
        "total_komentar": len(df),
        "per_post": df["post"].value_counts().to_dict(),
        "per_fase": df["fase"].value_counts().to_dict(),
        "username_unik": df["username"].nunique(),
        "hanya_emoji": int(df["hanya_emoji"].sum()),
        "teks_kosong": int((df["n_karakter"] == 0).sum()),
        "klaster_duplikat": int(df["klaster_dup"].nunique()),
        "baris_dalam_klaster_ganda": int((df["ukuran_klaster"] > 1).sum()),
        "sha256_mentah": {p.name: _sha256(p) for p in sorted(folder_mentah.glob("*.csv"))},
    }
    (folder_keluaran / "profil.json").write_text(
        json.dumps(profil, ensure_ascii=False, indent=2, default=str)
    )
    return df


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mentah", type=Path, default=root / "dataset")
    ap.add_argument("--keluaran", type=Path, default=root / "data" / "processed")
    args = ap.parse_args()

    df = bangun(args.mentah, args.keluaran)
    print(f"OK: {len(df)} komentar → {args.keluaran / 'komentar.parquet'}")
    print(df["fase"].value_counts().to_string())


if __name__ == "__main__":
    main()
