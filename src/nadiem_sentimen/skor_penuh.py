"""Skor seluruh 38.845 komentar dengan model terlatih → data untuk app.

Menghasilkan ``data/processed/skor.parquet``: satu baris per komentar dengan
prediksi spam/sikap/emosi, keyakinan, dan flag abstain. Ini sumber data tunggal
untuk aplikasi Streamlit (dimuat sekali, di-cache).

Jalankan:  python -m nadiem_sentimen.skor_penuh
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .inference import MesinSentimen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, default=None)
    ap.add_argument("--batch", type=int, default=128)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[2]

    df = pd.read_parquet(root / "data" / "processed" / "komentar.parquet")
    mesin = MesinSentimen.muat(args.model) if args.model else MesinSentimen.muat()

    hasil = mesin.predict(df["teks_bersih"].tolist(), batch=args.batch)
    df["spam"] = [h.spam for h in hasil]
    df["sikap"] = [h.sikap for h in hasil]
    df["emosi"] = [h.emosi for h in hasil]
    df["keyakinan_sikap"] = [h.keyakinan["sikap"] for h in hasil]
    df["keyakinan_emosi"] = [h.keyakinan["emosi"] for h in hasil]
    df["abstain_sikap"] = [h.abstain["sikap"] for h in hasil]

    keluaran = root / "data" / "processed" / "skor.parquet"
    df.to_parquet(keluaran, index=False)
    print(f"OK: {len(df)} komentar terskor → {keluaran}")
    print("\nspam:", int(df["spam"].sum()), f"({df['spam'].mean():.1%})")
    non = df[~df["spam"]]
    print("\nsikap (non-spam):")
    print((non["sikap"].value_counts(normalize=True) * 100).round(1).to_string())
    print("\nemosi (non-spam):")
    print((non["emosi"].value_counts(normalize=True) * 100).round(1).to_string())


if __name__ == "__main__":
    main()
